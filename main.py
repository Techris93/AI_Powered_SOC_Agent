from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch
import spacy
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Elasticsearch client
es_client = None

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Pydantic models for request validation
class ConnectionDetails(BaseModel):
    host_url: str  # Full URL, e.g., https://your-elasticsearch-host
    api_key: str   # API key is required for web-based Elasticsearch

class QueryRequest(BaseModel):
    query: str

class ReportRequest(BaseModel):
    data: List[dict]

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
            hosts=[details.host_url],
            api_key=api_key
        )
        if es_client.ping():
            indices = list(es_client.indices.get_alias(index="*").keys())
            return {"success": True, "indices": indices}
        else:
            raise HTTPException(status_code=400, detail="Failed to connect to Elasticsearch")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# List indices
@app.get("/api/indices")
async def list_indices():
    if not es_client:
        raise HTTPException(status_code=400, detail="Not connected to Elasticsearch")
    try:
        indices = es_client.indices.get_alias(index="*")
        return {"indices": list(indices.keys())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Search events with date range
@app.post("/api/search_events")
async def search_events(start_date: str, end_date: str):
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Process natural language query
@app.post("/api/query")
async def process_query(request: QueryRequest):
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
        return {"results": [hit["_source"] for hit in hits]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)