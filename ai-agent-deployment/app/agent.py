"""
Python AI Agent for AWS Deployment
Simple example using FastAPI and LLM-like functionality
"""

import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import requests
import re
import time as _time
from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
)
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse

# Configure logging – explicitly add a StreamHandler so that uvicorn's
# dictConfig cannot silently disable our application-level logs.
logger = logging.getLogger("ai-agent")
logger.setLevel(logging.INFO)
logger.propagate = False  # we manage our own handlers

_console = logging.StreamHandler()
_console.setLevel(logging.INFO)
_console.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(_console)


class SplunkHECHandler(logging.Handler):
    """Simple log handler that posts to Splunk HEC."""

    def __init__(self, url: str, token: str, index: Optional[str] = None,
                 source: Optional[str] = None, sourcetype: str = "_json"):
        super().__init__()
        self.url = url.rstrip("/") + "/services/collector/event/1.0"
        self.token = token
        self.index = index
        self.source = source or "ai-agent"
        self.sourcetype = sourcetype

    def emit(self, record: logging.LogRecord) -> None:
        # structured event for easier searching
        event_data = {
            "message": self.format(record),
            "level": record.levelname,
            "logger": record.name,
        }
        payload = {
            "time": record.created,
            "host": record.name,
            "source": self.source,
            "sourcetype": self.sourcetype,
            "event": event_data,
        }
        if self.index:
            payload["index"] = self.index
        headers = {
            "Authorization": f"Splunk {self.token}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(self.url, json=payload, headers=headers, timeout=2, verify=False)
            if resp.status_code != 200:
                print(f"[SplunkHEC] Non-200 response: {resp.status_code} {resp.text}", flush=True)
        except Exception as exc:
            print(f"[SplunkHEC] Failed to send log: {exc}", flush=True)


# configure splunk logging handler if environment variables present
splunk_url = os.getenv("SPLUNK_HEC_URL")
splunk_token = os.getenv("SPLUNK_HEC_TOKEN")
splunk_index = os.getenv("SPLUNK_HEC_INDEX")
splunk_source = os.getenv("SPLUNK_HEC_SOURCE")
splunk_sourcetype = os.getenv("SPLUNK_HEC_SOURCETYPE", "_json")
if splunk_url and splunk_token:
    spl_handler = SplunkHECHandler(
        splunk_url,
        splunk_token,
        index=splunk_index,
        source=splunk_source,
        sourcetype=splunk_sourcetype,
    )
    spl_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    spl_handler.setFormatter(formatter)
    logger.addHandler(spl_handler)
    print(f"[SplunkHEC] Handler attached -> {spl_handler.url}", flush=True)
else:
    print("[SplunkHEC] Skipped – SPLUNK_HEC_URL or SPLUNK_HEC_TOKEN not set", flush=True)

app = FastAPI(title="AI Agent API", version="1.0.0")

# Add CORS middleware to allow chat UI to communicate with API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter(
    "ai_agent_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "ai_agent_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120]
)
CHAT_COUNT = Counter(
    "ai_agent_chat_total",
    "Total chat messages processed",
    ["question_type"]
)
CHAT_LATENCY = Histogram(
    "ai_agent_chat_duration_seconds",
    "Chat response latency in seconds",
    ["question_type", "model"],
    buckets=[1, 2, 5, 10, 20, 40, 60, 90, 120]
)
OLLAMA_ERRORS = Counter(
    "ai_agent_ollama_errors_total",
    "Ollama call errors",
    ["error_type"]
)
ACTIVE_REQUESTS = Gauge(
    "ai_agent_active_requests",
    "Currently in-flight requests"
)


@app.middleware("http")
async def prometheus_middleware(request: StarletteRequest, call_next):
    """Track per-request latency and counts."""
    if request.url.path == "/metrics":
        return await call_next(request)
    ACTIVE_REQUESTS.inc()
    start = _time.perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        elapsed = _time.perf_counter() - start
        status = response.status_code if response else 500
        endpoint = request.url.path
        REQUEST_COUNT.labels(request.method, endpoint, status).inc()
        REQUEST_LATENCY.labels(request.method, endpoint).observe(elapsed)
        ACTIVE_REQUESTS.dec()


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return StarletteResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


class AgentRequest(BaseModel):
    """Request model for AI agent"""
    message: str
    context: Optional[dict] = None


class AgentResponse(BaseModel):
    """Response model from AI agent"""
    response: str
    timestamp: str
    success: bool


@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/readiness")
async def readiness_check():
    """Readiness probe for Kubernetes"""
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/process")
async def process_message(request: AgentRequest) -> AgentResponse:
    """Process a message through the AI agent"""
    try:
        logger.info(f"Processing message: {request.message}")
        
        # Simulated AI processing - replace with actual LLM calls
        # Example: OpenAI, Claude, LLaMA, etc.
        response = simulate_ai_processing(request.message, request.context)
        
        logger.info(f"Generated response: {response}")
        return AgentResponse(
            response=response,
            timestamp=datetime.utcnow().isoformat(),
            success=True
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@app.post("/chat")
async def chat(request: AgentRequest) -> AgentResponse:
    """Chat endpoint for conversational AI"""
    qtype = detect_question_type(request.message)
    CHAT_COUNT.labels(question_type=qtype).inc()
    start = _time.perf_counter()
    try:
        logger.info(f"Chat message: {request.message}")
        response = simulate_ai_processing(request.message, request.context)
        elapsed = _time.perf_counter() - start
        model = "deepseek-coder" if qtype == "technical" else "phi"
        CHAT_LATENCY.labels(question_type=qtype, model=model).observe(elapsed)
        return AgentResponse(
            response=response,
            timestamp=datetime.utcnow().isoformat(),
            success=True
        )
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Static majors dataset (extracted from undergrad.osu.edu Feb 2026)
# ---------------------------------------------------------------------------
OSU_MAJORS = [
    "Accounting", "Actuarial Science", "Aerospace Engineering",
    "African American and African Studies", "Agribusiness",
    "Agribusiness and Applied Economics", "Agricultural Communication",
    "Agricultural Systems Management", "Agriscience Education", "Agronomy",
    "Ancient History and Classics", "Animal Sciences",
    "Anthropological Sciences", "Anthropology", "Arabic", "Architecture",
    "Art", "Art Education", "Arts Management",
    "Astronomy and Astrophysics", "Atmospheric Sciences", "Aviation",
    "Aviation Management", "Biochemistry", "Biology",
    "Biomedical Engineering", "Biomedical Science",
    "Business Administration", "Business Management",
    "Chemical Engineering", "Chemistry", "Child and Youth Studies",
    "Chinese", "City and Regional Planning", "Civil Engineering",
    "Classics", "Communication", "Community Leadership",
    "Comparative Studies", "Computer and Information Science",
    "Computer Science and Engineering", "Construction Systems Management",
    "Consumer and Family Financial Services",
    "Criminology and Criminal Justice Studies", "Dance", "Data Analytics",
    "Dental Hygiene", "Earth Sciences", "Economics",
    "Economics - Business",
    "Education - Integrated Language Arts/English Education",
    "Education - Middle Childhood Education",
    "Education - Primary Education",
    "Education - Science and Mathematics Education",
    "Education - Special Education",
    "Education - Teaching English to Speakers of Other Languages",
    "Education - Technical Education and Training",
    "Education - World Language Education",
    "Electrical and Computer Engineering", "Engineering Physics",
    "Engineering Technology", "English", "Entomology",
    "Environment and Natural Resources",
    "Environment, Economy, Development and Sustainability",
    "Environmental Engineering", "Environmental Policy and Decision Making",
    "Environmental Science", "Evolution and Ecology",
    "Exercise Science Education", "Experiential Media Design",
    "Fashion and Retail Studies", "Film Studies", "Finance",
    "Food Business Management", "Food Science and Technology",
    "Food, Agricultural and Biological Engineering",
    "Forensic Anthropology", "Forestry, Fisheries and Wildlife",
    "French", "French and Francophone Studies",
    "Geographic Information Science", "Geography", "German",
    "Health and Rehabilitation Sciences",
    "Health Information Management and Systems",
    "Health Promotion, Nutrition and Exercise Science",
    "Health Sciences", "Hebrew and Jewish Studies", "History",
    "History of Art", "Horticulture and Crop Science",
    "Hospitality Management", "Human Development and Family Science",
    "Human Nutrition", "Human Resources",
    "Industrial and Systems Engineering", "Industrial Design",
    "Information Systems", "Interior Design", "International Business",
    "International Studies", "Islamic Studies", "Italian",
    "Italian Studies", "Japanese", "Journalism", "Korean",
    "Landscape Architecture", "Leadership", "Linguistics",
    "Logistics Management", "Marketing",
    "Materials Science and Engineering", "Mathematics",
    "Mechanical Engineering", "Medical Anthropology",
    "Medical Laboratory Science", "Microbiology", "Modern Greek",
    "Molecular Genetics", "Moving-Image Production", "Music",
    "Music - Composition", "Music - Education", "Music - Jazz Studies",
    "Music - Performance (orchestral instruments)",
    "Music - Performance (piano)", "Music - Performance (voice)",
    "Natural Resource Management", "Neuroscience", "Nursing",
    "Occupational Therapy", "Operations Management",
    "Pharmaceutical Sciences", "Philosophy",
    "Philosophy, Politics and Economics", "Physical Therapy", "Physics",
    "Plant Pathology", "Political Science", "Portuguese",
    "Pre-Dentistry", "Pre-Law", "Pre-Medicine", "Pre-Optometry",
    "Pre-Pharmacy", "Pre-Veterinary Medicine",
    "Professional Golf Management", "Psychology", "Public Health",
    "Public Management, Leadership and Policy", "Public Policy Analysis",
    "Radiologic Sciences and Therapy", "Real Estate and Urban Analysis",
    "Religious Studies", "Respiratory Therapy", "Romance Studies",
    "Russian", "Social Sciences Air Transportation", "Social Work",
    "Sociology", "Spanish", "Speech and Hearing Science",
    "Sport Industry", "Statistics", "Theatre", "Vision Science",
    "Visual Communication Design", "Welding Engineering",
    "Women's, Gender and Sexuality Studies", "World Literatures",
    "World Politics", "Zoology",
]


def get_osu_context() -> str:
    """Get OSU-specific context for the AI agent.

    Uses the embedded static majors list as the default, and still
    attempts a live fetch via fetch_osu_majors() which can override
    the list when the external site is reachable.
    """
    # Try live scrape first; fall back to the static list
    try:
        live = fetch_osu_majors()
        if live and len(live) > 10:
            return build_osu_context(live)
    except Exception:
        pass
    return build_osu_context(OSU_MAJORS)


def fetch_osu_majors(source_url: Optional[str] = None, max_items: int = 80, timeout: int = 8) -> list:
    """Fetch and parse OSU majors from the undergraduate majors page.

    Targets links whose href matches /majors-and-academics/majors/detail/.
    Uses BeautifulSoup when available; falls back to regex. Returns a
    deduplicated list of major names (may be empty on failure).
    """
    url = source_url or "https://undergrad.osu.edu/majors-and-academics/majors"
    detail_pattern = "/majors-and-academics/majors/detail/"

    try:
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "OSU-AI-Agent/1.0 (internal assistant)"
        })
        resp.raise_for_status()
        html = resp.text

        majors: list = []
        seen: set = set()

        def _add(name: str):
            name = name.strip()
            if name and name not in seen and len(name) >= 3:
                seen.add(name)
                majors.append(name)

        # --- BeautifulSoup path (preferred) ---
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                if detail_pattern in a["href"]:
                    _add(a.get_text(strip=True))
            if majors:
                return majors[:max_items]
        except Exception:
            pass  # fall through to regex

        # --- Regex fallback ---
        # Match: href="…/majors/detail/…">Major Name</a>
        pattern = r'href="[^"]*' + re.escape(detail_pattern) + r'[^"]*"[^>]*>([^<]{3,120})</a>'
        for m in re.finditer(pattern, html):
            _add(re.sub(r"\s+", " ", m.group(1)))
            if len(majors) >= max_items:
                break

        return majors
    except Exception as e:
        logger.warning(f"Failed to fetch OSU majors from {url}: {e}")
        return []


def build_osu_context(majors_list: Optional[list] = None) -> str:
    """Build the OSU context string, optionally inserting a live majors list."""
    if majors_list and len(majors_list) > 0:
        total = len(majors_list)
        sample = ', '.join(majors_list[:20])
        majors_line = (f"OSU offers {total}+ undergraduate majors including: {sample}."
                       f"\nFull list: https://undergrad.osu.edu/majors-and-academics/majors")
    else:
        majors_line = "Popular majors: Computer Science, Engineering, Business, Nursing, Psychology, Biology, Communications. Browse all at: https://undergrad.osu.edu/majors-and-academics/majors"

    context = f"""You are an Ohio State University assistant. Answer OSU questions specifically.

Spring 2026 Dates:
- Jan 5: Tuition due
- Jan 12: Classes start
- Jan 16: Add/drop deadline
- Jan 23: Drop deadline with refund

Majors at OSU:
OSU offers 200+ undergraduate majors.
{majors_line}
To declare/change major: Meet with academic advisor in your college.

Resources:
- BuckeyeLink: buckeyelink.osu.edu (registration, grades, schedule)
- Advising: advising.osu.edu
- Financial Aid: sfa.osu.edu

Always provide OSU-specific answers with links when possible."""
    return context


def detect_question_type(message: str) -> str:
    """Detect the type of question to route to appropriate handler"""
    message_lower = message.lower()
    
    # OSU-specific keywords
    osu_keywords = ['osu', 'buckeye', 'class', 'registration', 'tuition', 'fee', 'deadline', 'semester', 'drop', 'add', 'refund', 'payment', 'buckeyelink', 'columbus campus', 'regional campus', 'major', 'degree', 'minor', 'advisor', 'advising', 'graduate', 'undergraduate', 'college', 'gpa', 'transcript', 'ohio state']
    
    # Code/Technical keywords
    code_keywords = ['python', 'javascript', 'java', 'docker', 'kubernetes', 'k8s', 'git', 'api', 'database', 'react', 'node', 'sql', 'code', 'program', 'function', 'algorithm', 'debug', 'error', 'exception', 'kubernetes', 'container', 'devops', 'cloud', 'aws', 'terraform', 'yaml', 'json', 'rest', 'http', 'css', 'html']
    
    if any(keyword in message_lower for keyword in osu_keywords):
        return "osu"
    elif any(keyword in message_lower for keyword in code_keywords):
        return "technical"
    else:
        return "general"


def get_code_context() -> str:
    """Get context for code/technical questions"""
    context = """You are a technical expert. IMPORTANT: Format responses like ChatGPT:

**For code/commands:**
1. Use clear markdown code blocks with language specified (```python, ```bash, ```yaml, etc)
2. Make code easily copyable
3. Add explanations AFTER code blocks
4. Show example outputs when relevant

**Structure:**
- Brief explanation first
- Code/command in marked block
- What it does
- Example or usage

**Example format:**
Here's how to deploy with Kubernetes:

```bash
kubectl apply -f deployment.yaml
kubectl rollout status deployment/myapp
```

This deploys your app and waits for rollout."""
    return context


def simulate_ai_processing(message: str, context: Optional[dict] = None) -> str:
    """
    Smart routing based on question type:
    - OSU questions → Ollama with OSU context
    - Code/Technical questions → Ollama with code context
    - General questions → Ollama with general knowledge
    """
    # Detect question type
    question_type = detect_question_type(message)
    
    logger.info(f"Question type detected: {question_type} | Message: {message[:50]}...")
    
    # Get environment variables for LLM configuration
    llm_provider = os.getenv("LLM_PROVIDER", "ollama")
    
    # Prepare context based on question type
    enhanced_context = context or {}
    
    if question_type == "osu":
        enhanced_context['system_prompt'] = get_osu_context()
        enhanced_context['question_type'] = 'osu'
    elif question_type == "technical":
        enhanced_context['system_prompt'] = get_code_context()
        enhanced_context['question_type'] = 'technical'
    else:
        # General questions get minimal system prompt
        enhanced_context['system_prompt'] = "Helpful assistant. Answer concisely."
        enhanced_context['question_type'] = 'general'
    
    if llm_provider == "ollama":
        return process_with_ollama(message, enhanced_context)
    elif llm_provider == "openai":
        return process_with_openai(message, enhanced_context)
    elif llm_provider == "bedrock":
        return process_with_bedrock(message, enhanced_context)
    else:
        # Mock response for testing
        return f"Mock AI Response: Processing '{message}' with context {context or {}}"


def process_with_ollama(message: str, context: Optional[dict] = None) -> str:
    """Process with Ollama - local LLM running in Docker with intelligent routing"""
    try:
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        
        context = context or {}
        question_type = context.get("question_type", "general")
        system_prompt = context.get("system_prompt", "You are a helpful AI assistant.")
        
        # Select model based on question type
        if question_type == "technical":
            ollama_model = "deepseek-coder"
        else:
            ollama_model = "phi"  # phi for general and OSU questions
        
        logger.info(f"[{question_type.upper()}] Calling Ollama at {ollama_url} with model {ollama_model}")
        
        # Build custom prompt with context
        prompt_text = f"{system_prompt}\n\nUser: {message}\n\nAssistant:"
        
        # Using Ollama's generate API for text completion
        url = f"{ollama_url}/api/generate"
        payload = {
            "model": ollama_model,
            "prompt": prompt_text,
            "stream": False,
            "temperature": 0.7
        }
        
        # Timeouts: phi needs ~60s, deepseek needs ~90s
        timeout = 90 if question_type == "technical" else 70
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        
        result = response.json()
        ollama_response = result.get("response", "").strip()
        
        logger.info(f"[{question_type.upper()}] Ollama response ({len(ollama_response)} chars): {ollama_response[:80]}...")
        return ollama_response
        
    except requests.exceptions.ConnectionError:
        OLLAMA_ERRORS.labels(error_type="connection").inc()
        error_msg = f"Cannot connect to Ollama at {os.getenv('OLLAMA_URL', 'http://localhost:11434')}. Is it running?"
        logger.error(error_msg)
        raise HTTPException(status_code=503, detail=error_msg)
    except requests.exceptions.Timeout:
        OLLAMA_ERRORS.labels(error_type="timeout").inc()
        error_msg = f"Model response timed out. Try a simpler question."
        logger.error(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Ollama error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


def process_with_openai(message: str, context: Optional[dict] = None) -> str:
    """Process with OpenAI API"""
    try:
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # Example OpenAI call
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant"},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {str(e)}")
        raise


def process_with_bedrock(message: str, context: Optional[dict] = None) -> str:
    """Process with AWS Bedrock"""
    try:
        import boto3
        client = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
        # Example Bedrock call (Claude model)
        response = client.invoke_model(
            modelId="anthropic.claude-v2",
            body=f'{{"prompt": "{message}"}}'
        )
        return response['body'].read().decode('utf-8')
    except Exception as e:
        logger.error(f"Bedrock error: {str(e)}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "readiness": "/readiness",
            "process": "/process",
            "chat": "/chat",
            "ui": "/chat-ui"
        }
    }


@app.get("/chat-ui")
async def chat_ui():
    """Serve the ChatGPT-like UI"""
    try:
        # Try to find the chat-ui.html file
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "..", "chat-ui.html"),
            os.path.join(os.path.dirname(__file__), "chat-ui.html"),
            "chat-ui.html"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return FileResponse(path, media_type="text/html")
        
        # If file not found, return inline HTML
        logger.warning("chat-ui.html not found, serving inline HTML")
        return HTMLResponse(get_inline_chat_ui_html())
    except Exception as e:
        logger.error(f"Error serving chat UI: {str(e)}")
        return HTMLResponse(get_inline_chat_ui_html())


@app.get("/scrape/majors")
async def scrape_majors():
    """Endpoint to fetch a live list of OSU majors (returns JSON).

    This can be used to verify the scraper result or fetch on demand.
    """
    source = "https://undergrad.osu.edu/majors-and-academics/majors"
    majors = fetch_osu_majors(source_url=source)
    return {
        "source": source,
        "count": len(majors),
        "majors": majors,
        "timestamp": datetime.utcnow().isoformat()
    }


def get_inline_chat_ui_html() -> str:
    """Return inline HTML for chat UI (fallback)"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ohio State AI Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px;
        }

        .chat-container {
            width: 100%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 20px;
            font-weight: 600;
        }

        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }

        .welcome-content {
            text-align: center;
            color: #666;
            padding: 20px;
        }

        .welcome-content h2 {
            color: #667eea;
            margin-bottom: 10px;
        }

        .suggested-questions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-top: 30px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }

        .question-btn {
            background: white;
            border: 2px solid #667eea;
            border-radius: 8px;
            padding: 12px 16px;
            cursor: pointer;
            font-size: 13px;
            color: #667eea;
            font-weight: 500;
            transition: all 0.2s;
        }

        .question-btn:hover {
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }

        .message {
            margin-bottom: 16px;
            animation: slideIn 0.3s ease-in-out;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            display: flex;
            justify-content: flex-end;
        }

        .message.assistant {
            display: flex;
            justify-content: flex-start;
        }

        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.5;
        }

        .user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .assistant .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            max-width: 90%;
        }

        .code-block {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 12px;
            border-radius: 6px;
            margin: 8px 0;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            border-left: 4px solid #667eea;
        }

        .code-lang {
            color: #858585;
            font-size: 11px;
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid #444;
            display: block;
        }

        .input-container {
            padding: 16px 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
        }

        .input-wrapper {
            flex: 1;
            display: flex;
            gap: 8px;
            background: #f5f5f5;
            border-radius: 24px;
            padding: 10px 16px;
        }

        #messageInput {
            flex: 1;
            border: none;
            background: transparent;
            outline: none;
            font-size: 14px;
            font-family: inherit;
        }

        .send-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50%;
            width: 32px;
            height: 32px;
            cursor: pointer;
            font-weight: bold;
        }

        .send-button:hover { opacity: 0.9; }
        .send-button:disabled { opacity: 0.5; cursor: not-allowed; }

        .status-message {
            color: #667eea;
            font-size: 12px;
            font-style: italic;
            margin-top: 4px;
        }

        .follow-up-questions {
            margin-top: 16px;
            padding: 12px;
            background: #f0f4ff;
            border-radius: 8px;
            animation: slideIn 0.3s ease-in-out;
        }

        .follow-up-btn {
            background: white;
            border: 1px solid #667eea;
            color: #667eea;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: left;
            font-weight: 500;
        }

        .follow-up-btn:hover {
            background: #667eea;
            color: white;
            transform: translateX(4px);
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">Ohio State AI Assistant</div>
        <div class="messages-container" id="messagesContainer">
            <div class="welcome-content">
                <h2>Welcome to OSU Assistant!</h2>
                <p>Get instant answers about classes, registration, tuition, and more.</p>
                <div class="suggested-questions">
                    <button class="question-btn" onclick="askQuestion('When is tuition due?')">When is tuition due?</button>
                    <button class="question-btn" onclick="askQuestion('How do I register for classes?')">How do I register?</button>
                    <button class="question-btn" onclick="askQuestion('What is the add/drop deadline?')">Add/Drop deadline?</button>
                    <button class="question-btn" onclick="askQuestion('When does the semester start?')">Semester start date?</button>
                    <button class="question-btn" onclick="askQuestion('How do I access BuckeyeLink?')">BuckeyeLink access?</button>
                    <button class="question-btn" onclick="askQuestion('What are the refund deadlines?')">Refund deadlines?</button>
                </div>
            </div>
        </div>
        <div class="input-container">
            <div class="input-wrapper">
                <input type="text" id="messageInput" placeholder="Ask about OSU, registration, tuition..." />
                <button class="send-button" onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>

    <script>
        const messageInput = document.getElementById('messageInput');
        const messagesContainer = document.getElementById('messagesContainer');
        let isWelcomeVisible = true;

        // Helper functions - MUST BE DEFINED FIRST
        var codeBlockMarker = String.fromCharCode(96, 96, 96);
        
        function escapeHtml(unsafe) {
            var div = document.createElement('div');
            div.textContent = unsafe;
            return div.innerHTML;
        }

        function formatCodeBlocks(text) {
            if (text.indexOf(codeBlockMarker) === -1) return escapeHtml(text);
            
            var parts = text.split(codeBlockMarker);
            var result = '';
            var newline = String.fromCharCode(10);
            
            for (var i = 0; i < parts.length; i++) {
                if (i % 2 === 0) {
                    result += escapeHtml(parts[i]);
                } else {
                    var block = parts[i];
                    var lines = block.split(newline);
                    var lang = 'code';
                    var code = block;
                    
                    if (lines.length > 0 && lines[0].trim().length > 0) {
                        var firstLine = lines[0].trim();
                        if (/^[a-z0-9]+$/.test(firstLine)) {
                            lang = firstLine;
                            code = lines.slice(1).join(newline);
                        }
                    }
                    
                    result += '<div class="code-block">';
                    if (lang !== 'code') {
                        result += '<div class="code-lang">' + escapeHtml(lang) + '</div>';
                    }
                    result += '<pre><code>' + escapeHtml(code.trim()) + '</code></pre>';
                    result += '</div>';
                }
            }
            return result;
        }

        function addMessage(content, role) {
            var messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + role;
            
            var contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            if (role === 'assistant' && content.indexOf(codeBlockMarker) !== -1) {
                contentDiv.innerHTML = formatCodeBlocks(content);
            } else {
                contentDiv.textContent = content;
            }
            
            messageDiv.appendChild(contentDiv);
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function addStatusMessage(status) {
            const statusDiv = document.createElement('div');
            statusDiv.id = 'statusMessage';
            statusDiv.className = 'status-message';
            statusDiv.textContent = status;
            messagesContainer.appendChild(statusDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function removeStatusMessage() {
            const status = document.getElementById('statusMessage');
            if (status) status.remove();
        }

        function askQuestion(question) {
            messageInput.value = question;
            sendMessage();
        }

        function getFollowUpQuestions(topic) {
            const questions = followUpQuestions[topic] || followUpQuestions.general;
            const shuffled = [...questions].sort(() => Math.random() - 0.5);
            return shuffled.slice(0, 3);
        }

        function detectTopicType(userMessage) {
            const msg = userMessage.toLowerCase();
            const osuKeywords = ['osu', 'buckeye', 'class', 'registration', 'tuition', 'fee', 'deadline', 'semester', 'drop', 'add', 'refund', 'payment', 'buckeyelink'];
            const techKeywords = ['python', 'javascript', 'docker', 'kubernetes', 'git', 'api', 'database', 'code', 'function', 'debug', 'error', 'devops', 'cloud', 'aws'];
            
            if (osuKeywords.some(kw => msg.includes(kw))) return 'osu';
            if (techKeywords.some(kw => msg.includes(kw))) return 'technical';
            return 'general';
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            messageInput.value = '';

            if (isWelcomeVisible) {
                messagesContainer.innerHTML = '';
                isWelcomeVisible = false;
            }

            addMessage(message, 'user');
            addStatusMessage('Connecting to AI Agent...');

            try {
                const startTime = Date.now();
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
                
                removeStatusMessage();
                addMessage(data.response, 'assistant');
                addStatusMessage('Response received in ' + elapsed + 's');
                
                lastQuestionType = detectTopicType(message);
                const followUps = getFollowUpQuestions(lastQuestionType);
                setTimeout(() => {
                    addFollowUpQuestions(followUps);
                }, 1500);
                
                setTimeout(removeStatusMessage, 3000);
            } catch (error) {
                removeStatusMessage();
                addMessage('Error: ' + error.message, 'assistant');
            }
        }

        // Sample follow-up questions by topic
        const followUpQuestions = {
            osu: [
                "What is BuckeyeLink?",
                "How do I request a transcript?",
                "What is the GPA requirement?",
                "How do I appeal a grade?"
            ],
            technical: [
                "Can you explain this better?",
                "What are best practices?",
                "How do I debug this?",
                "What is the difference between...?"
            ],
            general: [
                "Tell me more about this",
                "Can you explain that differently?",
                "What are the pros and cons?",
                "How does it work?"
            ]
        };

        let lastQuestionType = "general";

        function addFollowUpQuestions(questions) {
            const followUpDiv = document.createElement('div');
            followUpDiv.className = 'follow-up-questions';
            followUpDiv.innerHTML = '<div style="font-size: 12px; color: #999; margin-bottom: 8px; font-weight: 500;">Follow-up questions:</div>';
            
            const buttonContainer = document.createElement('div');
            buttonContainer.style.display = 'flex';
            buttonContainer.style.flexDirection = 'column';
            buttonContainer.style.gap = '6px';
            
            questions.forEach(q => {
                const btn = document.createElement('button');
                btn.className = 'follow-up-btn';
                btn.textContent = q;
                btn.onclick = () => askQuestion(q);
                buttonContainer.appendChild(btn);
            });
            
            followUpDiv.appendChild(buttonContainer);
            messagesContainer.appendChild(followUpDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });

        messageInput.focus();
    </script>
</body>
</html>"""


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
