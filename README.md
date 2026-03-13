# AI-Powered SOC Agent

A standalone, AI-powered Security Operations Center platform that replicates capabilities from Microsoft Sentinel, Defender XDR, and Security Copilot without depending on external Microsoft services.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-teal)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## Features

### Current Implementation (v2.0)

#### 1. Advanced AI Query Engine

- Natural language query understanding using the OpenAI SDK
- Intent classification (search_logs, investigate_incident, threat_intel_lookup, etc.)
- Automatic Elasticsearch query generation
- Entity extraction (IPs, domains, time ranges, usernames)
- Fallback to basic NLP if AI not configured

#### 2. Incident Management System

- Create, read, update, delete incidents
- Severity levels (critical, high, medium, low, info)
- Status tracking (new, investigating, contained, resolved, closed)
- Comments and collaboration
- Alert association
- Dashboard statistics

#### 3. Threat Intelligence Integration

- IP reputation checking (AbuseIPDB, VirusTotal)
- Domain reputation checking (VirusTotal)
- File hash analysis (VirusTotal)
- Threat scoring (0-100)
- Multi-source aggregation
- Human-readable summaries

#### 4. Elasticsearch Integration

- Connect to Elasticsearch clusters
- Query security logs
- Index management
- Date range filtering

---

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key (for AI features)
- Elasticsearch instance (optional)
- Threat intelligence API keys (optional)

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd AI-Powered-SOCAgent
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

4. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env and add your API keys
```

5. **Run the application**

```bash
python main.py
```

6. **Open the frontend**
   Open `index.html` in your browser, or serve it:

```bash
python -m http.server 8000
# Navigate to http://localhost:8000
```

---

## Configuration

### Environment Variables

Edit `.env` file:

```bash
# OpenAI API (Required for AI features)
OPENAI_API_KEY=sk-your-key-here

# Elasticsearch (Optional)
ELASTICSEARCH_HOST=https://your-elasticsearch-host
ELASTICSEARCH_API_KEY=your-es-api-key

# Database (Optional - defaults to SQLite)
DATABASE_URL=sqlite:///./soc_agent.db

# Threat Intelligence APIs (Optional)
ABUSEIPDB_API_KEY=your-abuseipdb-key
VIRUSTOTAL_API_KEY=your-virustotal-key
```

### Getting API Keys

#### OpenAI (Required for AI features)

1. Go to https://platform.openai.com/
2. Create account and navigate to API Keys
3. Create new secret key
4. Copy to `.env` as `OPENAI_API_KEY`

#### AbuseIPDB (Free tier: 1000 requests/day)

1. Go to https://www.abuseipdb.com/
2. Register account
3. Navigate to API section
4. Copy key to `.env` as `ABUSEIPDB_API_KEY`

#### VirusTotal (Free tier: 500 requests/day)

1. Go to https://www.virustotal.com/
2. Register account
3. Navigate to API section
4. Copy key to `.env` as `VIRUSTOTAL_API_KEY`

---

## Usage

### 1. Connect to Elasticsearch

In the frontend:

1. Enter Elasticsearch host URL (e.g., `https://your-es-host`)
2. Enter API key
3. Click "Connect"

### 2. Query Security Events

**Using Natural Language (AI-powered):**

```
Show me all failed SSH login attempts from IP 192.168.1.100 in the last 24 hours
```

**Using Basic NLP (fallback):**

```
phishing attacks finance department
```

The system automatically selects:

- **Advanced AI** if OpenAI API key is configured
- **Basic NLP** if not configured

### 3. Manage Incidents

**Create Incident:**

```bash
curl -X POST http://localhost:5001/api/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Suspicious PowerShell Execution",
    "description": "Detected obfuscated PowerShell on server-01",
    "severity": "high",
    "assigned_to": "security-analyst"
  }'
```

**List Incidents:**

```bash
curl http://localhost:5001/api/incidents?status=new&severity=high
```

**Update Incident:**

```bash
curl -X PUT http://localhost:5001/api/incidents/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "investigating"}'
```

### 4. Check Threat Intelligence

**Check IP Reputation:**

```bash
curl http://localhost:5001/api/threat_intel/ip/1.2.3.4
```

Response:

```json
{
  "ip": "1.2.3.4",
  "threat_score": 75,
  "is_malicious": true,
  "sources": {
    "abuseipdb": {...},
    "virustotal": {...}
  },
  "summary": "THREAT DETECTED - Threat score: 75/100..."
}
```

**Check Domain:**

```bash
curl http://localhost:5001/api/threat_intel/domain/suspicious-site.com
```

**Check File Hash:**

```bash
curl http://localhost:5001/api/threat_intel/hash/abc123...
```

### 5. View Dashboard Stats

```bash
curl http://localhost:5001/api/dashboard/stats
```

---

## API Documentation

### Interactive API Docs

Once running, visit:

- Swagger UI: http://localhost:5001/docs
- ReDoc: http://localhost:5001/redoc

### Key Endpoints

#### Query Processing

- `POST /api/query` - Unified query (auto-selects advanced/basic)
- `POST /api/query/advanced` - AI-powered query
- `POST /api/query/basic` - Basic NLP query

#### Incident Management

- `POST /api/incidents` - Create incident
- `GET /api/incidents` - List incidents
- `GET /api/incidents/{id}` - Get incident
- `PUT /api/incidents/{id}` - Update incident
- `DELETE /api/incidents/{id}` - Delete incident
- `POST /api/incidents/{id}/comments` - Add comment

#### Threat Intelligence

- `GET /api/threat_intel/ip/{ip}` - IP reputation
- `GET /api/threat_intel/domain/{domain}` - Domain reputation
- `GET /api/threat_intel/hash/{hash}` - Hash reputation

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system architecture.

### High-Level Overview

```
Frontend (HTML/JS)
       ↓
FastAPI Backend
       ↓
    ┌──┼──┐
    │  │  │
   AI  DB  Threat Intel
 Engine   (SQLite)  APIs
```

**Components:**

- **AI Engine:** LangChain + OpenAI for query understanding
- **Database:** SQLite/PostgreSQL for incidents
- **Threat Intel:** AbuseIPDB + VirusTotal integration
- **Elasticsearch:** External log storage

---

## Roadmap

See [STANDALONE_FEATURES_ROADMAP.md](STANDALONE_FEATURES_ROADMAP.md) for complete feature roadmap.

### Completed (v2.0)

- ✅ Advanced AI Query Engine
- ✅ Incident Management System
- ✅ Threat Intelligence Integration
- ✅ Elasticsearch Integration

### Phase 2 (Planned) - SIEM Capabilities

- ⏳ Detection Rules Engine
- ⏳ Alert Correlation
- ⏳ Security Dashboards
- ⏳ Automated Notifications

### Phase 3 (Planned) - EDR Capabilities

- ⏳ Endpoint Agent
- ⏳ Behavioral Analysis
- ⏳ Vulnerability Scanning
- ⏳ Response Actions

### Phase 4 (Planned) - Advanced AI

- ⏳ RAG Knowledge Base
- ⏳ AI Report Generation
- ⏳ Playbook Automation
- ⏳ Threat Hunting Recommendations

---

## Development

### Project Structure

```
AI-Powered-SOCAgent/
├── main.py                    # FastAPI application
├── database.py                # Database configuration
├── models.py                  # SQLAlchemy models
├── index.html                 # Frontend UI
├── ai_engine/                 # AI query processing
│   ├── intent_classifier.py   # Intent classification
│   └── query_processor.py     # Query generation
├── services/                  # External services
│   └── threat_intel.py        # Threat intelligence
├── config/                    # Configuration
│   └── llm_config.py          # LLM settings
├── venv/                      # Virtual environment
├── .env                       # Environment variables
├── .env.example               # Example env file
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── ARCHITECTURE.md            # Architecture documentation
└── STANDALONE_FEATURES_ROADMAP.md  # Feature roadmap
```

### Running Tests

```bash
# Unit tests (to be implemented)
pytest tests/

# Linting
flake8 .

# Type checking
mypy .
```

### Adding New Features

1. Create feature branch
2. Implement feature
3. Add tests
4. Update documentation
5. Submit PR

---

## Troubleshooting

### AI Query Engine Not Working

**Symptom:** Queries fall back to basic NLP

**Solutions:**

1. Check `.env` file has `OPENAI_API_KEY`
2. Verify API key is valid: https://platform.openai.com/account/api-keys
3. Check OpenAI API status: https://status.openai.com/
4. Review logs for specific errors

### Database Errors

**Symptom:** "No such table" or connection errors

**Solutions:**

1. Delete `soc_agent.db` and restart (recreates tables)
2. Check file permissions on database file
3. For PostgreSQL, verify `DATABASE_URL` format

### Threat Intel Errors

**Symptom:** "API key invalid" or rate limit errors

**Solutions:**

1. Verify API keys in `.env`
2. Check API rate limits (AbuseIPDB: 1000/day, VirusTotal: 500/day)
3. Wait before retrying if rate limited

### Elasticsearch Connection Failed

**Symptom:** "Failed to connect to Elasticsearch"

**Solutions:**

1. Verify Elasticsearch is running and accessible
2. Check host URL format (must include `https://`)
3. Verify API key format (remove `api_key=` prefix if present)
4. Test connection with curl first

---

## Performance

### Benchmarks (Development Machine)

- **AI Query Processing:** ~2-3 seconds
- **Basic Query Processing:** <100ms
- **Incident Creation:** <50ms
- **Threat Intel Lookup:** ~500ms (cached)
- **Elasticsearch Query:** Variable (depends on index size)

### Optimization Tips

1. **Use Redis caching** for threat intel results
2. **Index database** columns used in filters
3. **Batch Elasticsearch queries** when possible
4. **Use PostgreSQL** instead of SQLite in production

---

## Security

### Current Security Measures

- Input validation via Pydantic
- SQL injection protection (SQLAlchemy ORM)
- Environment variable for secrets
- CORS configuration

### Recommendations for Production

- Add authentication (JWT tokens)
- Implement rate limiting
- Use HTTPS only
- Restrict CORS origins
- Add audit logging
- Implement API key rotation
- Use secrets management (HashiCorp Vault, AWS Secrets Manager)

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

---

## License

MIT License - see LICENSE file

---

## Support

For issues and questions:

- GitHub Issues: [Link to repository issues]
- Documentation: See `ARCHITECTURE.md` and `STANDALONE_FEATURES_ROADMAP.md`

---

## Acknowledgments

This project replicates capabilities from:

- Microsoft Sentinel (SIEM)
- Microsoft Defender XDR (EDR)
- Microsoft Security Copilot (AI)

Built with:

- FastAPI
- LangChain
- OpenAI
- SQLAlchemy
- Elasticsearch
- AbuseIPDB
- VirusTotal

---

**Version:** 2.0.0
**Last Updated:** 2025-10-15
**Status:** Active Development
