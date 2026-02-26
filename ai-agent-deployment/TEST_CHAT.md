# Testing ChatGPT-Like UI with Ollama

Complete step-by-step guide to test your AI Agent chat UI.

## Prerequisites
- Docker Desktop running
- All files in place (docker-compose.yml, app/agent.py, chat-ui.html)

## 🚀 Step-by-Step Testing

### Step 1: Start Everything

```powershell
# Navigate to project directory
cd C:\Users\eml2s\Session\ai-agent-deployment

# Start all services (AI Agent + Ollama + Splunk + Prometheus + Grafana)
docker-compose up -d

# Wait 10-15 seconds for services to start
```

### Step 2: Pull an Ollama Model

In a **new PowerShell window**:

```powershell
# Pull llama2 (or use mistral, neural-chat, orca-mini)
docker exec ollama-local ollama pull llama2

# This takes 2-5 minutes depending on internet speed
# You'll see a progress bar like: [==================] 100%
```

While waiting, you can check progress:
```powershell
docker logs ollama-local -f
```

### Step 3: Verify Services Are Running

```powershell
# Check all containers
docker ps

# You should see:
# - ai-agent-local (port 8000)
# - ollama-local (port 11434)
# - splunk-local (port 8088, 8001)
# - prometheus-local (port 9090)
# - grafana-local (port 3000)
# - node-exporter-local (port 9100)
```

### Step 4: Test Agent Health

```powershell
# Check if AI Agent is healthy
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","timestamp":"2026-02-25T..."}
```

### Step 5: Test Ollama Directly

```powershell
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Should return list of models:
# {"models":[{"name":"llama2:latest",...}]}
```

### Step 6: Make a Direct Chat Request

```powershell
# Test the /chat endpoint
$body = @{
    message = "What is the capital of France?"
} | ConvertTo-Json

curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d $body

# Should return:
# {
#   "response": "The capital of France is Paris...",
#   "timestamp": "2026-02-25T...",
#   "success": true
# }
```

### Step 7: Open the Chat UI

Open your browser and go to:

```
http://localhost:8000/chat-ui
```

You should see:
- 🤖 AI Agent Chat (purple gradient header)
- "Welcome to AI Agent Chat" welcome message
- ● Connected (green status indicator)
- Input field with send button

### Step 8: Send Your First Message

1. Type a message in the input field:
   ```
   Hello! What can you do?
   ```

2. Press **Enter** or click the **➤** send button

3. You should see:
   - Your message appears on the right (purple bubble)
   - Typing indicator (three dots) appears on the left
   - Agent's response appears on the left (white bubble) after 5-30 seconds

4. Try more messages:
   ```
   What is machine learning?
   Explain AI in simple terms
   Tell me a joke
   ```

## 🧪 Advanced Testing

### Test 1: Check Response Speed

```powershell
# Time how long a response takes
Measure-Command {
    curl -X POST http://localhost:8000/chat `
      -H "Content-Type: application/json" `
      -d '{"message":"test"}' | Out-Null
}

# Should be 5-30 seconds depending on model
```

### Test 2: Monitor Agent Logs

In a **new PowerShell window**:

```powershell
# Follow agent logs in real-time
docker logs ai-agent-local -f

# You should see:
# INFO:agent:Chat message: Your message here
# INFO:agent:Calling Ollama at http://ollama:11434 with model llama2
# INFO:agent:Ollama response: The response...
```

### Test 3: Monitor Ollama Logs

```powershell
docker logs ollama-local -f

# You should see model loading and token generation
```

### Test 4: Multiple Messages

Send 5+ messages rapidly and watch:
- Chat UI updates in real-time
- Agent processes each one
- Responses appear sequentially

### Test 5: Try Different Models

Pull and test other models:

```powershell
# Pull mistral (faster, higher quality)
docker exec ollama-local ollama pull mistral

# Update docker-compose.yml
# Change: OLLAMA_MODEL=mistral

# Restart agent
docker-compose restart ai-agent

# Test again at http://localhost:8000/chat-ui
```

### Test 6: Check System Resources

While chatting, monitor resource usage:

```powershell
# Watch Docker stats in real-time
docker stats

# Should see:
# - ollama-local using 2-4GB memory
# - CPU spike during inference (5-30 seconds)
# - ai-agent-local minimal resources (just waiting)
```

### Test 7: Splunk Integration

Check if logs are sent to Splunk:

1. Open Splunk:
   ```
   http://localhost:8001
   ```
   - Username: admin
   - Password: Demouser123

2. Search for agent logs:
   ```
   index=main source=ai-agent
   ```

3. You should see every chat message and response!

## ✅ Verification Checklist

- [ ] All containers running (`docker ps`)
- [ ] AI Agent health check passes (`curl http://localhost:8000/health`)
- [ ] Ollama models loaded (`curl http://localhost:11434/api/tags`)
- [ ] Chat UI loads (`http://localhost:8000/chat-ui`)
- [ ] Status shows "● Connected"
- [ ] Can send messages
- [ ] Receive responses (5-30 seconds)
- [ ] Agent logs show message processing (`docker logs ai-agent-local -f`)
- [ ] Ollama logs show inference (`docker logs ollama-local -f`)
- [ ] Splunk has logs (`http://localhost:8001`)

## 🐛 Troubleshooting

### Chat UI loads but says "● Disconnected"

**Problem:** UI can't reach API

**Fix:**
```powershell
# Check if agent is running
docker ps | grep ai-agent
# If not running: docker-compose up -d ai-agent

# Check if port 8000 is open
curl http://localhost:8000/health

# Check agent logs
docker logs ai-agent-local
```

### Send button doesn't work / No response

**Problem:** Can't reach Ollama

**Fix:**
```powershell
# Check Ollama is running
docker ps | grep ollama

# Check if models are loaded
docker exec ollama-local ollama list
# If empty, pull a model:
docker exec ollama-local ollama pull llama2

# Check Ollama is accessible
curl http://localhost:11434/api/tags
```

### Response is "Failed to get response from agent"

**Problem:** Error in agent code

**Fix:**
```powershell
# Check agent logs for error
docker logs ai-agent-local -f

# Common errors:
# - "Cannot connect to Ollama" → Check OLLAMA_URL is correct
# - "model not found" → Pull the model first
# - "timeout" → Model is too slow, try orca-mini

# Restart agent
docker-compose restart ai-agent
```

### Slow responses (>60 seconds)

**Problem:** Model is overloaded or too large

**Fix:**
```powershell
# 1. Try smaller model
docker exec ollama-local ollama pull orca-mini
# Update: OLLAMA_MODEL=orca-mini
docker-compose restart ai-agent

# 2. Or increase timeout in agent.py
# Change: timeout=60 → timeout=120

# 3. Check Docker memory
docker stats ollama-local
# If using >6GB, increase Docker Desktop memory
```

### Port already in use

**Problem:** Another service using port 8000 or 11434

**Fix:**
```powershell
# Find what's using port 8000
netstat -ano | findstr 8000
# Kill it: taskkill /PID <PID> /F

# Or change docker-compose ports
# Change: "8000:8000" → "8001:8000"
```

## 📊 Performance Expectations

| Action | Time | Notes |
|--------|------|-------|
| Start containers | 10-15s | First time slower |
| Pull model | 2-5 min | Depends on internet |
| First chat message | 10-30s | Model loads into memory |
| Subsequent messages | 5-20s | Model already loaded |
| Stop containers | 5-10s | Graceful shutdown |

## 🎯 What's Working

✅ **FastAPI backend** - Processing requests on port 8000
✅ **Ollama integration** - Running local LLM on port 11434
✅ **Chat UI** - Beautiful ChatGPT-like interface
✅ **Real AI responses** - From Ollama models
✅ **Splunk logging** - Centralized log collection
✅ **Health checks** - Automatic service monitoring
✅ **CORS enabled** - UI can talk to backend

## 🚀 Next Steps

1. ✅ Test basic chat functionality
2. ✅ Try different models (mistral, neural-chat, orca-mini)
3. ✅ Monitor performance with `docker stats`
4. ✅ Check logs in Splunk
5. ✅ Deploy to Kubernetes (see DEPLOY_LOCAL_KUBERNETES.md)
6. ✅ Deploy to AWS EKS (see aws/README.md)

## 📞 Getting Help

If something doesn't work:

1. **Check logs:**
   ```powershell
   docker logs ai-agent-local -f
   docker logs ollama-local -f
   docker logs splunk-local -f
   ```

2. **Check status:**
   ```powershell
   docker ps -a
   curl http://localhost:8000/health
   curl http://localhost:11434/api/tags
   ```

3. **Restart everything:**
   ```powershell
   docker-compose down -v
   docker-compose up -d
   docker exec ollama-local ollama pull llama2
   ```

4. **Check port conflicts:**
   ```powershell
   netstat -ano | findstr "8000\|11434\|8001\|9090\|3000"
   ```

---

Enjoy your ChatGPT-like AI Agent! 🎉
