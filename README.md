HEAD
# uangmengalirderaskerekeningku
uangmengalirderaskerekeningku
=======
# YouTube Winning Pattern Detector - Backend

This is the backend for the MVP v1 of the "YouTube Winning Pattern Detector". It uses FastAPI, AgentBay (via Python SDK), and OpenAI to collect data from YouTube and generate winning title templates.

## specific Features
- **Keyword Collection**: Scrapes top YouTube search results and "People also watched" / "Related" videos.
- **AgentBay Integration**: Uses AgentBay SDK to control a remote browser for non-aggressive scraping.
- **AI Templates**: Generates reusable title templates using OpenAI.
- **Background Tasks**: Handles long-running collection jobs asynchronously.
- **Caching**: Returns cached results for 24 hours unless forced.
- **REST API**: Simple endpoints to trigger and monitor jobs.

## Tech Stack
- **Python 3.11**
- **FastAPI**
- **SQLAlchemy 2.x**
- **Supabase Postgres**
- **AgentBay Python SDK** (wuying-agentbay-sdk)
- **OpenAI API**
- **Docker**

## Setup

### Prerequisites
- Docker & Docker Compose
- Supabase Project (Postgres Database)
- AgentBay API Key
- OpenAI API Key

### Environment Variables
Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
AGENTBAY_API_KEY=your_agentbay_api_key
OPENAI_API_KEY=your_openai_api_key
# Optional
OPENAI_MODEL=gpt-3.5-turbo
```

### Local Development

1. **Build and Run**:
   ```bash
   docker-compose up --build
   ```

2. **Access API**:
   - Docs: http://localhost:8000/docs
   - API: http://localhost:8000/api

### Deployment (EasyPanel)

1. **Create a Service**: Use the "Docker Image" or "Git" deployment source.
2. **Configuration**:
   - **Build**: Use the `Dockerfile` at root.
   - **Port**: 8000
   - **Env Vars**: Add the variables from `.env`.
3. **Database**: Connect to your Supabase instance using `DATABASE_URL`.

## API Usage

### Trigger Collection
```bash
curl -X POST "http://localhost:8000/api/collect/youtube" \
     -H "Content-Type: application/json" \
     -d '{"keyword": "n8n automation", "force_refresh": false}'
```

### Check Status
```bash
curl "http://localhost:8000/api/collect/status/{job_id}"
```

## Project Structure
```
app/
├── api/            # API Endpoints
├── core/           # Configuration
├── db/             # Database Models & Session
├── services/       # Business Logic (AgentBay, YT, AI)
├── utils/          # Helpers
└── main.py         # Entrypoint
```
0940489 (first commit)
