# AI-Powered SOC Agent - System Architecture

## Overview
This document describes the architecture of the standalone AI-Powered SOC Agent platform, which replicates capabilities from Microsoft Sentinel, Defender XDR, and Security Copilot.

---

## System Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│                            USER INTERFACE                                  │
│                          (index.html + JavaScript)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Dashboard   │  │  Incidents   │  │   Queries    │  │Threat Intel  │ │
│  │              │  │  Management  │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │
                        REST API (FastAPI)
                                │
┌───────────────────────────────▼───────────────────────────────────────────┐
│                         FASTAPI APPLICATION (main.py)                      │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                       API ENDPOINTS                                 │  │
│  │  • /api/connect           - Elasticsearch connection               │  │
│  │  • /api/query             - Unified NL query (auto-select)         │  │
│  │  • /api/query/advanced    - AI-powered query                       │  │
│  │  • /api/query/basic       - Basic NLP query                        │  │
│  │  • /api/incidents/*       - Incident management                    │  │
│  │  • /api/threat_intel/*    - Threat intelligence                    │  │
│  │  • /api/dashboard/stats   - Dashboard metrics                      │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
┌───────────────────┐  ┌──────────────┐  ┌─────────────────┐
│   AI ENGINE       │  │   DATABASE   │  │  THREAT INTEL   │
│  (ai_engine/)     │  │  (SQLite/    │  │   SERVICE       │
│                   │  │  PostgreSQL) │  │ (services/      │
│  ┌─────────────┐ │  │              │  │  threat_intel)  │
│  │ Intent      │ │  │  ┌────────┐  │  │                 │
│  │ Classifier  │ │  │  │Incident│  │  │  ┌───────────┐  │
│  └─────────────┘ │  │  │Table   │  │  │  │AbuseIPDB  │  │
│  ┌─────────────┐ │  │  └────────┘  │  │  │API        │  │
│  │ Query       │ │  │  ┌────────┐  │  │  └───────────┘  │
│  │ Generator   │ │  │  │Alert   │  │  │  ┌───────────┐  │
│  └─────────────┘ │  │  │Table   │  │  │  │VirusTotal │  │
│                   │  │  └────────┘  │  │  │API        │  │
│  Uses:            │  │  ┌────────┐  │  │  └───────────┘  │
│  • LangChain      │  │  │Comment │  │  │  ┌───────────┐  │
│  • OpenAI API     │  │  │Table   │  │  │  │AlienVault │  │
│  • GPT-4 mini     │  │  └────────┘  │  │  │OTX API    │  │
│                   │  │  ┌────────┐  │  │  └───────────┘  │
│                   │  │  │Rules   │  │  │                 │
│                   │  │  │Table   │  │  │                 │
│                   │  │  └────────┘  │  │                 │
└───────────────────┘  └──────────────┘  └─────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   ELASTICSEARCH       │
                    │   (External Service)  │
                    │                       │
                    │   • Security Logs     │
                    │   • Event Data        │
                    │   • Threat Data       │
                    └───────────────────────┘

External APIs:
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  OpenAI API  │ │  AbuseIPDB   │ │ VirusTotal   │
│  (GPT-4 mini)│ │     API      │ │     API      │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## Component Breakdown

### 1. Frontend Layer (index.html)
**Purpose:** User interface for SOC analysts

**Features:**
- Elasticsearch connection management
- Natural language query interface
- Results visualization
- Basic report generation

**Tech Stack:**
- Vanilla JavaScript
- Chart.js (for future dashboards)
- Fetch API for REST calls

---

### 2. API Layer (main.py)
**Purpose:** FastAPI application serving as the backend

**Modules:**
- **Elasticsearch Integration:** Connect to and query Elasticsearch
- **Query Processing:** Basic and advanced NLP query processing
- **Incident Management:** CRUD operations for incidents
- **Threat Intelligence:** IP/domain/hash reputation checks
- **Dashboard:** Statistics and metrics

**Tech Stack:**
- FastAPI
- Python 3.11+
- Uvicorn (ASGI server)

---

### 3. AI Engine (ai_engine/)
**Purpose:** Advanced query understanding and translation

**Components:**

#### 3.1 Intent Classifier (`intent_classifier.py`)
- Classifies user queries into intents:
  - `search_logs`
  - `investigate_incident`
  - `threat_intel_lookup`
  - `generate_report`
  - `analyze_behavior`
  - `hunt_threats`
- Extracts entities (IPs, domains, time ranges, usernames)
- Extracts security keywords

**Model:** OpenAI GPT-4o-mini via LangChain

#### 3.2 Query Processor (`query_processor.py`)
- Translates natural language to Elasticsearch queries
- Uses LLM to generate optimized queries
- Handles time range parsing
- Fallback to basic queries if LLM fails

**Model:** OpenAI GPT-4o-mini via LangChain

---

### 4. Database Layer (database.py + models.py)
**Purpose:** Persistent storage for incidents, alerts, and rules

**Models:**

#### 4.1 Incident
```python
- id: Integer (Primary Key)
- title: String
- description: Text
- severity: Enum (critical, high, medium, low, info)
- status: Enum (new, investigating, contained, resolved, closed)
- assigned_to: String
- created_at: DateTime
- updated_at: DateTime
- closed_at: DateTime
```

#### 4.2 Alert
```python
- id: Integer (Primary Key)
- incident_id: Foreign Key → Incident
- alert_type: String
- source_ip: String
- destination_ip: String
- username: String
- timestamp: DateTime
- raw_data: JSON
```

#### 4.3 IncidentComment
```python
- id: Integer (Primary Key)
- incident_id: Foreign Key → Incident
- author: String
- content: Text
- created_at: DateTime
```

#### 4.4 DetectionRule
```python
- id: Integer (Primary Key)
- name: String
- description: Text
- severity: Enum
- enabled: Boolean
- rule_definition: JSON
- created_at: DateTime
- last_triggered: DateTime
```

**Database:** SQLite (development) / PostgreSQL (production)

---

### 5. Threat Intelligence Service (services/threat_intel.py)
**Purpose:** Aggregate threat intelligence from multiple sources

**Sources:**
- **AbuseIPDB:** IP reputation (free tier: 1000 queries/day)
- **VirusTotal:** IP/domain/file hash reputation (free tier: 500/day)
- **AlienVault OTX:** (future implementation)

**Features:**
- Async API calls
- Threat scoring (0-100)
- Malicious/suspicious flagging
- Human-readable summaries

**Response Format:**
```json
{
  "ip": "1.2.3.4",
  "threat_score": 75,
  "is_malicious": true,
  "sources": {
    "abuseipdb": {...},
    "virustotal": {...}
  },
  "summary": "THREAT DETECTED - ..."
}
```

---

## Data Flow

### Query Processing Flow

```
1. User enters natural language query
   ↓
2. Frontend sends to /api/query
   ↓
3. Check if AI engine available
   ├─ Yes → Advanced processing
   │   ├─ Intent Classification (LangChain + GPT)
   │   ├─ Entity Extraction
   │   ├─ Elasticsearch Query Generation
   │   └─ Execute query on Elasticsearch
   └─ No → Basic processing
       ├─ spaCy NLP (keyword extraction)
       ├─ Simple multi_match query
       └─ Execute query on Elasticsearch
   ↓
4. Return results with metadata:
   - method (advanced/basic)
   - intent (if advanced)
   - confidence score
   - query used
   - results
```

### Incident Creation Flow

```
1. User creates incident via /api/incidents
   ↓
2. Validate severity level
   ↓
3. Create Incident record in database
   ↓
4. Return incident with ID
   ↓
5. (Optional) Associate alerts with incident
   ↓
6. (Optional) Add comments to incident
```

### Threat Intelligence Flow

```
1. User requests IP reputation via /api/threat_intel/ip/{ip}
   ↓
2. ThreatIntelService checks AbuseIPDB
   ↓
3. ThreatIntelService checks VirusTotal (if key provided)
   ↓
4. Aggregate results and calculate threat score
   ↓
5. Generate summary
   ↓
6. Return comprehensive threat report
```

---

## Configuration

### Environment Variables (.env)

```bash
# AI Engine
OPENAI_API_KEY=sk-...

# Elasticsearch
ELASTICSEARCH_HOST=https://...
ELASTICSEARCH_API_KEY=...

# Database
DATABASE_URL=sqlite:///./soc_agent.db  # or PostgreSQL

# Threat Intelligence
ABUSEIPDB_API_KEY=...
VIRUSTOTAL_API_KEY=...
ALIENVAULT_OTX_API_KEY=...

# Application
APP_ENV=development
LOG_LEVEL=INFO
```

---

## API Endpoints Reference

### Elasticsearch
- `POST /api/connect` - Connect to Elasticsearch
- `GET /api/indices` - List Elasticsearch indices

### Query Processing
- `POST /api/query` - Unified query endpoint (auto-selects advanced/basic)
- `POST /api/query/advanced` - AI-powered query processing
- `POST /api/query/basic` - Basic NLP query processing

### Incident Management
- `POST /api/incidents` - Create incident
- `GET /api/incidents` - List incidents (with filters)
- `GET /api/incidents/{id}` - Get incident details
- `PUT /api/incidents/{id}` - Update incident
- `DELETE /api/incidents/{id}` - Delete incident
- `POST /api/incidents/{id}/comments` - Add comment
- `GET /api/incidents/{id}/comments` - Get comments

### Threat Intelligence
- `GET /api/threat_intel/ip/{ip}` - Check IP reputation
- `GET /api/threat_intel/domain/{domain}` - Check domain reputation
- `GET /api/threat_intel/hash/{hash}` - Check file hash reputation

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics

---

## Security Considerations

1. **API Keys:** Stored in .env file (not in version control)
2. **Input Validation:** All inputs validated via Pydantic models
3. **SQL Injection:** Protected by SQLAlchemy ORM
4. **CORS:** Configured for development (restrict in production)
5. **Authentication:** Not implemented (Phase 2 feature)
6. **Rate Limiting:** Not implemented (use nginx/API gateway in production)

---

## Scalability

### Current Limitations
- Single-threaded Uvicorn
- SQLite database (dev)
- No caching layer

### Production Recommendations
1. **Web Server:** Nginx reverse proxy
2. **App Server:** Gunicorn + Uvicorn workers
3. **Database:** PostgreSQL with connection pooling
4. **Caching:** Redis for threat intel results
5. **Load Balancing:** Multiple FastAPI instances
6. **Message Queue:** Celery + RabbitMQ for background tasks

---

## Future Enhancements

### Phase 2 (Weeks 3-4) - SIEM Features
- Detection rules engine
- Alert correlation
- Automated playbooks
- Email/Slack notifications

### Phase 3 (Weeks 5-6) - EDR Features
- Endpoint agent
- Behavioral analysis
- Response actions
- Process monitoring

### Phase 4 (Weeks 7-8) - Advanced AI
- RAG knowledge base (ChromaDB)
- AI-powered report generation
- Threat hunting recommendations
- Playbook automation

---

## Deployment

### Development
```bash
python main.py
```

### Production
```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:5001
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
```

---

## Monitoring

### Health Check
- Endpoint: `GET /health` (to be implemented)
- Database connection
- Elasticsearch connection
- AI engine status

### Metrics (Future)
- Request latency
- Query success rate
- Incident response time
- Threat intel cache hit rate

---

## Troubleshooting

### AI Engine Not Working
- Check `OPENAI_API_KEY` in .env
- Verify API key is valid
- Check OpenAI API status

### Database Errors
- Ensure SQLite file permissions
- Run `init_db()` if tables missing
- Check PostgreSQL connection if using

### Threat Intel Errors
- Verify API keys in .env
- Check API rate limits
- Validate input format (IP/domain/hash)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-15
