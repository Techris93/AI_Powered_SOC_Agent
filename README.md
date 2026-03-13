# AI-Powered SOC Agent

![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![License](https://img.shields.io/badge/License-MIT-blue)

## Overview

The **AI-Powered SOC Agent** is a web-based application designed to enhance Security Operations Center (SOC) efficiency by automating security event retrieval and analysis. Built with **Python**, **FastAPI**, and **Elasticsearch**, the agent leverages **Natural Language Processing (NLP)** using spaCy to allow SOC analysts to query security data using intuitive, natural language commands. The system identifies patterns indicative of cyber threats (e.g., phishing, SQL injections) and generates detailed incident reports, streamlining threat management processes.

Hosted at: https://ai-powered-soc-agent-97d0c.web.app/

### Key Features

- **Natural Language Interface**: Query security events using human-readable commands (e.g., "Show phishing attacks from last week").
- **Automated Threat Detection**: Identifies cyber threats like phishing or SQL injections using Elasticsearch queries and NLP.
- **Incident Reporting**: Generates structured Markdown reports summarizing security events for actionable insights.
- **Full-Stack Solution**: Combines a responsive frontend (HTML, CSS, JavaScript) with a robust FastAPI backend for seamless Elasticsearch interaction.
- **Real-Time Feedback**: Displays connection status and error/success messages to enhance user experience.

## Technologies Used

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python 3.10+, FastAPI, spaCy (`en_core_web_sm`), Elasticsearch
- **Web Framework**: FastAPI with CORS middleware
- **Deployment**: Netlify (frontend), local server (backend)
- **Other**: Pydantic for request validation, Uvicorn for server hosting

## Project Structure

```plaintext
ai-powered-soc-agent/
├── index.html           # Frontend interface
├── backend/
│   ├── main.py         # FastAPI backend with API endpoints
│   ├── requirements.txt # Python dependencies
├── README.md           # Project documentation
```
## Setup Instructions
### Prerequisites
- Python 3.10+ and pip
- Elasticsearch instance with API key access
- Node.js (optional, for local frontend development)
- Git for cloning the repository

## Installation
1. Clone the Repository:
```
git clone https://github.com/Techris93/ai-powered-soc-agent.git
cd ai-powered-soc-agent
```
2. Set Up Python Environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```
3. Install spaCy Model:
```
python -m spacy download en_core_web_sm
```
4. Configure Elasticsearch:
- Obtain your Elasticsearch host URL and API key.
- Ensure your Elasticsearch instance is accessible and contains relevant security event indices.

5. Run the Backend:
```
cd backend
uvicorn main:app --host 0.0.0.0 --port 5001
```
6. Access the Frontend:
- Open index.html in a browser for local testing, or visit the deployed site at https://ai-powered-soc-agent.netlify.app.
- Ensure the backend server is running to handle API requests.

Backend Dependencies (requirements.txt)
```plaintext
fastapi==0.115.2
uvicorn==0.32.0
pydantic==2.9.2
spacy==3.7.6
elasticsearch==8.15.1
```
### Usage
1. Connect to Elasticsearch:
- Enter your Elasticsearch host URL (e.g., https://your-elasticsearch-host) and API key in the web interface.
- Click "Connect" to establish a connection and view available indices.

2. Query Security Events:
- Input a natural language query (e.g., "Show failed login attempts from yesterday") in the query textarea.
- Click "Analyze" to retrieve and display matching security events.

3. Generate Reports:
- After analyzing a query, click "Generate Report" to create a Markdown-formatted incident report summarizing the results.

#### Example Queries
- "Show me all phishing attacks from last week"
- "What IP addresses were involved in SQL injection attempts?"
- "Analyze malware incidents from the past 24 hours"

## API Endpoints
### POST /api/connect: 
- Connect to Elasticsearch with host URL and API key.
- Request Body: { "host_url": "<url>", "api_key": "<key>" }
- Response: { "success": true, "indices": ["index1", "index2", ...] }

### GET /api/indices: 
- List available Elasticsearch indices.
### POST /api/query:
- Process a natural language query.Request Body: { "query": "<natural language query>" }
- Response: { "results": [{event1}, {event2}, ...] }

### POST /api/report: 
- Generate a Markdown incident report.Request Body: { "data": [{event1}, {event2}, ...] }
- Response: { "report": "<markdown content>" }

## Troubleshooting
- Connection Issues: Verify the Elasticsearch host URL includes the protocol (e.g., https://) and the API key is valid.
- Query Failures: Ensure the Elasticsearch indices contain relevant security event data and the NLP query is specific.
- CORS Errors: Confirm the backend server is running and accessible from the frontend host.
- Dependencies: Run pip install -r backend/requirements.txt to resolve missing packages.

## Future Improvements
- Enhance NLP capabilities with advanced intent recognition for more precise query parsing.
- Integrate additional threat intelligence feeds for richer analysis.
- Add user authentication for secure access to the SOC agent.
- Support real-time alerts for critical security events.

## Contributing
Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request with your changes.
## License
This project is licensed under the MIT License (LICENSE).

