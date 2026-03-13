from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, AnyHttpUrl, field_validator
from elasticsearch import Elasticsearch
import spacy
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from ai_engine.query_processor import AdvancedQueryProcessor
from config.llm_config import LLMConfig
import os
import logging
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db, init_db
from models import Incident, IncidentComment, SeverityLevel, IncidentStatus
from datetime import datetime
from services.threat_intel import ThreatIntelService

# Load environment variables
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger("soc_agent")

app = FastAPI(
    title="AI-Powered SOC Agent",
    description="Intelligent Security Operations Center with Advanced AI Capabilities",
    version="2.0.0"
)

# Add CORS middleware with safer defaults for browser clients
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5001,http://127.0.0.1:5001"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

trusted_hosts = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

API_ACCESS_KEY = os.getenv("SOC_AGENT_API_KEY", "").strip()


@app.middleware("http")
async def secure_api_middleware(request: Request, call_next):
    if request.url.path.startswith("/api") and API_ACCESS_KEY:
        provided_api_key = request.headers.get("x-api-key", "")
        if provided_api_key != API_ACCESS_KEY:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

# Global Elasticsearch client
es_client = None

# Load spaCy NLP model (kept for backward compatibility)
nlp = spacy.load("en_core_web_sm")

# Initialize Advanced Query Processor (OpenAI SDK-based)
query_processor = None
try:
    if LLMConfig.validate():
        query_processor = AdvancedQueryProcessor()
        print("✓ Advanced AI Query Engine initialized successfully")
    else:
        print("⚠ OpenAI API key not found. Advanced query features disabled.")
        print("  Set OPENAI_API_KEY in .env file to enable AI-powered queries.")
except Exception as e:
    print(f"⚠ Failed to initialize AI Query Engine: {e}")
    print("  Falling back to basic NLP processing.")

# Initialize database
try:
    init_db()
except Exception as e:
    print(f"⚠ Failed to initialize database: {e}")

# Initialize Threat Intelligence Service
threat_intel_service = ThreatIntelService()
print("✓ Threat Intelligence Service initialized")

# Pydantic models for request validation
class ConnectionDetails(BaseModel):
    host_url: AnyHttpUrl  # Full URL, e.g., https://your-elasticsearch-host
    api_key: str = Field(min_length=16, max_length=512)

    @field_validator("host_url")
    @classmethod
    def validate_host_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        host = value.host or ""
        if value.scheme != "https" and host not in {"localhost", "127.0.0.1"}:
            raise ValueError("host_url must use HTTPS unless connecting to localhost")
        return value

class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=LLMConfig.MAX_QUERY_LENGTH)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("query cannot be empty")
        return cleaned

class ReportRequest(BaseModel):
    data: List[dict] = Field(min_length=1, max_length=500)


# Incident Management Models
class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: Optional[str] = Field(default=None, max_length=4000)
    severity: str = Field(default="medium", pattern="^(critical|high|medium|low|info)$")
    assigned_to: Optional[str] = Field(default=None, max_length=100)


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    description: Optional[str] = Field(default=None, max_length=4000)
    severity: Optional[str] = Field(default=None, pattern="^(critical|high|medium|low|info)$")
    status: Optional[str] = Field(default=None, pattern="^(new|investigating|contained|resolved|closed|false_positive)$")
    assigned_to: Optional[str] = Field(default=None, max_length=100)


class CommentCreate(BaseModel):
    author: str = Field(min_length=2, max_length=100)
    content: str = Field(min_length=1, max_length=4000)

# Connect to Elasticsearch
@app.post("/api/connect")
async def connect(details: ConnectionDetails):
    global es_client
    try:
        # Remove 'api_key=' prefix if present
        api_key = details.api_key
        if api_key.startswith("api_key="):
            api_key = api_key[len("api_key="):]
        es_client = Elasticsearch(
            hosts=[str(details.host_url)],
            api_key=api_key
        )
        if es_client.ping():
            indices = list(es_client.indices.get_alias(index="*").keys())
            return {"success": True, "indices": indices}
        else:
            raise HTTPException(status_code=400, detail="Failed to connect to Elasticsearch")
    except Exception:
        logger.exception("Failed Elasticsearch connection attempt")
        raise HTTPException(status_code=400, detail="Failed to connect to Elasticsearch with provided settings")

# List indices
@app.get("/api/indices")
async def list_indices():
    if not es_client:
        raise HTTPException(status_code=400, detail="Not connected to Elasticsearch")
    try:
        indices = es_client.indices.get_alias(index="*")
        return {"indices": list(indices.keys())}
    except Exception:
        logger.exception("Failed to list Elasticsearch indices")
        raise HTTPException(status_code=500, detail="Failed to retrieve indices")

# Search events with date range
@app.post("/api/search_events")
async def search_events(
    start_date: str = Query(..., min_length=4, max_length=64),
    end_date: str = Query(..., min_length=4, max_length=64)
):
    if not es_client:
        raise HTTPException(status_code=400, detail="Not connected to Elasticsearch")
    query = {
        "query": {
            "range": {
                "@timestamp": {  # Adjust field name if necessary
                    "gte": start_date,
                    "lte": end_date
                }
            }
        }
    }
    try:
        result = es_client.search(index="*", body=query)
        hits = result["hits"]["hits"]
        return {"results": [hit["_source"] for hit in hits]}
    except Exception:
        logger.exception("Elasticsearch date-range search failed")
        raise HTTPException(status_code=500, detail="Search execution failed")

# Process natural language query (Legacy - Basic NLP)
@app.post("/api/query/basic")
async def process_query_basic(request: QueryRequest):
    """
    Basic query processing using spaCy (legacy endpoint)
    Use /api/query/advanced for AI-powered query understanding
    """
    if not es_client:
        raise HTTPException(status_code=400, detail="Not connected to Elasticsearch")

    # Basic NLP processing
    doc = nlp(request.query)
    keywords = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN", "VERB"]]

    # Simple query construction
    es_query = {
        "query": {
            "multi_match": {
                "query": " ".join(keywords),
                "fields": ["*"]
            }
        }
    }

    try:
        result = es_client.search(index="*", body=es_query)
        hits = result["hits"]["hits"]
        return {
            "method": "basic",
            "query_used": es_query,
            "results": [hit["_source"] for hit in hits],
            "total_hits": result["hits"]["total"]["value"]
        }
    except Exception:
        logger.exception("Basic query processing failed")
        raise HTTPException(status_code=500, detail="Basic query processing failed")


# Advanced AI-powered query processing (NEW)
@app.post("/api/query/advanced")
async def process_query_advanced(request: QueryRequest):
    """
    Advanced query processing using OpenAI
    Provides intelligent intent classification and query generation
    """
    if not es_client:
        raise HTTPException(status_code=400, detail="Not connected to Elasticsearch")

    if not query_processor:
        raise HTTPException(
            status_code=503,
            detail="AI Query Engine not available. Please configure OPENAI_API_KEY in .env file."
        )

    try:
        # Process query with AI engine
        ai_result = await query_processor.process_query(request.query)

        # Execute the generated Elasticsearch query
        es_query = ai_result["es_query"]
        result = es_client.search(index="*", body=es_query)
        hits = result["hits"]["hits"]

        return {
            "method": "advanced",
            "intent": ai_result["intent"],
            "confidence": ai_result["confidence"],
            "entities": ai_result["entities"],
            "keywords": ai_result["keywords"],
            "query_used": es_query,
            "results": [hit["_source"] for hit in hits],
            "total_hits": result["hits"]["total"]["value"]
        }
    except Exception:
        logger.exception("Advanced query processing failed")
        raise HTTPException(status_code=500, detail="Advanced query processing failed")


# Unified query endpoint (AUTO-SELECT: Advanced if available, fallback to Basic)
@app.post("/api/query")
async def process_query(request: QueryRequest):
    """
    Unified query endpoint - automatically uses advanced AI if available,
    falls back to basic NLP if not configured
    """
    if query_processor:
        return await process_query_advanced(request)
    else:
        return await process_query_basic(request)

# Generate report
@app.post("/api/report")
async def generate_report(request: ReportRequest):
    if not request.data:
        raise HTTPException(status_code=400, detail="No data provided for report")

    # Simple Markdown report
    report_content = "# Incident Report\n\n"
    report_content += "## Events\n"
    for event in request.data:
        report_content += f"- **Event**: {event.get('@timestamp', 'Unknown time')}\n"
        report_content += f"  - Details: {event}\n"

    return {"report": report_content}


# ============================================================================
# INCIDENT MANAGEMENT API ENDPOINTS
# ============================================================================

@app.post("/api/incidents", status_code=201)
async def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    """Create a new security incident"""
    try:
        severity_enum = SeverityLevel[incident.severity.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid severity: {incident.severity}")

    db_incident = Incident(
        title=incident.title,
        description=incident.description,
        severity=severity_enum,
        assigned_to=incident.assigned_to
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    return {"success": True, "incident": db_incident.to_dict()}


@app.get("/api/incidents")
async def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List all incidents with optional filters"""
    query = db.query(Incident)

    if status:
        try:
            status_enum = IncidentStatus[status.upper()]
            query = query.filter(Incident.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    if severity:
        try:
            severity_enum = SeverityLevel[severity.upper()]
            query = query.filter(Incident.severity == severity_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

    if assigned_to:
        query = query.filter(Incident.assigned_to == assigned_to)

    incidents = query.order_by(Incident.created_at.desc()).limit(limit).all()

    return {
        "total": len(incidents),
        "incidents": [inc.to_dict() for inc in incidents]
    }


@app.get("/api/incidents/{incident_id}")
async def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Get incident details including all associated alerts and comments"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident_dict = incident.to_dict()
    incident_dict["alerts"] = [alert.to_dict() for alert in incident.alerts]
    incident_dict["comments"] = [comment.to_dict() for comment in incident.comments]

    return incident_dict


@app.put("/api/incidents/{incident_id}")
async def update_incident(
    incident_id: int,
    update_data: IncidentUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing incident"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Update fields if provided
    if update_data.title is not None:
        incident.title = update_data.title

    if update_data.description is not None:
        incident.description = update_data.description

    if update_data.severity is not None:
        try:
            incident.severity = SeverityLevel[update_data.severity.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {update_data.severity}")

    if update_data.status is not None:
        try:
            new_status = IncidentStatus[update_data.status.upper()]
            incident.status = new_status

            # Set closed_at timestamp if status is being set to CLOSED or RESOLVED
            if new_status in [IncidentStatus.CLOSED, IncidentStatus.RESOLVED]:
                if incident.closed_at is None:
                    incident.closed_at = datetime.utcnow()
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {update_data.status}")

    if update_data.assigned_to is not None:
        incident.assigned_to = update_data.assigned_to

    incident.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(incident)

    return {"success": True, "incident": incident.to_dict()}


@app.delete("/api/incidents/{incident_id}")
async def delete_incident(incident_id: int, db: Session = Depends(get_db)):
    """Delete an incident and all associated alerts/comments"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    db.delete(incident)
    db.commit()

    return {"success": True, "message": f"Incident {incident_id} deleted"}


@app.post("/api/incidents/{incident_id}/comments")
async def add_comment(
    incident_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db)
):
    """Add a comment to an incident"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    comment = IncidentComment(
        incident_id=incident_id,
        author=comment_data.author,
        content=comment_data.content
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {"success": True, "comment": comment.to_dict()}


@app.get("/api/incidents/{incident_id}/comments")
async def get_comments(incident_id: int, db: Session = Depends(get_db)):
    """Get all comments for an incident"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return {
        "incident_id": incident_id,
        "comments": [comment.to_dict() for comment in incident.comments]
    }


@app.get("/api/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    total_incidents = db.query(Incident).count()
    open_incidents = db.query(Incident).filter(
        Incident.status.in_([IncidentStatus.NEW, IncidentStatus.INVESTIGATING])
    ).count()

    critical_incidents = db.query(Incident).filter(
        Incident.severity == SeverityLevel.CRITICAL,
        Incident.status != IncidentStatus.CLOSED
    ).count()

    # Incidents by severity
    severity_counts = {}
    for severity in SeverityLevel:
        count = db.query(Incident).filter(Incident.severity == severity).count()
        severity_counts[severity.value] = count

    # Incidents by status
    status_counts = {}
    for status in IncidentStatus:
        count = db.query(Incident).filter(Incident.status == status).count()
        status_counts[status.value] = count

    return {
        "total_incidents": total_incidents,
        "open_incidents": open_incidents,
        "critical_incidents": critical_incidents,
        "severity_distribution": severity_counts,
        "status_distribution": status_counts
    }


# ============================================================================
# THREAT INTELLIGENCE API ENDPOINTS
# ============================================================================

@app.get("/api/threat_intel/ip/{ip_address}")
async def check_ip_reputation(ip_address: str):
    """Check IP address reputation using threat intelligence sources"""
    try:
        result = await threat_intel_service.check_ip(ip_address)
        return result
    except Exception:
        logger.exception("Threat intel IP check failed")
        raise HTTPException(status_code=500, detail="Threat intelligence check failed")


@app.get("/api/threat_intel/domain/{domain}")
async def check_domain_reputation(domain: str):
    """Check domain reputation using threat intelligence sources"""
    try:
        result = await threat_intel_service.check_domain(domain)
        return result
    except Exception:
        logger.exception("Threat intel domain check failed")
        raise HTTPException(status_code=500, detail="Threat intelligence check failed")


@app.get("/api/threat_intel/hash/{file_hash}")
async def check_hash_reputation(file_hash: str):
    """Check file hash reputation using threat intelligence sources"""
    try:
        result = await threat_intel_service.check_hash(file_hash)
        return result
    except Exception:
        logger.exception("Threat intel hash check failed")
        raise HTTPException(status_code=500, detail="Threat intelligence check failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)