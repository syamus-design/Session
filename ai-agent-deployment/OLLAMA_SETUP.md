# Ollama Integration Guide

Your AI agent is now integrated with **Ollama** - a local LLM inference engine running in Docker! 🦙

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```powershell
# Start the entire stack with Ollama
docker-compose up -d

# Wait a moment for Ollama to start, then download a model
# Open PowerShell and run:
docker exec ollama-local ollama pull llama2

# Or pull other models:
docker exec ollama-local ollama pull mistral
docker exec ollama-local ollama pull neural-chat
docker exec ollama-local ollama pull orca-mini
```

Then access the chat UI:
```
http://localhost:8000/chat-ui
```

### Option 2: Ollama Already Running Separately

If you already have Ollama running in Docker Desktop on a different port/host:

1. Update `docker-compose.yml`:
   ```yaml
   ai-agent:
     environment:
       - OLLAMA_URL=http://host.docker.internal:11434  # For Docker Desktop
       # or
       - OLLAMA_URL=http://your-ollama-ip:11434
   ```

2. Restart the agent:
   ```powershell
   docker-compose restart ai-agent
   ```

## Available Models

Ollama has many models to choose from:

| Model | Size | Speed | Quality | Tokens/sec |
|-------|------|-------|---------|-----------|
| `orca-mini` | 1.7GB | ⚡⚡⚡ | Good | ~50+ |
| `neural-chat` | 4.1GB | ⚡⚡ | Better | ~30+ |
| `mistral` | 4GB | ⚡⚡ | Excellent | ~30+ |
| `llama2` | 3.8GB | ⚡⚡ | Excellent | ~20+ |
| `llama2-7b-chat` | 3.8GB | ⚡⚡ | Excellent | ~20+ |
| `llama2-uncensored` | 3.8GB | ⚡⚡ | Interesting | ~20+ |

### Pull a Model
```powershell
# Pull llama2 (default)
docker exec ollama-local ollama pull llama2

# Pull another model
docker exec ollama-local ollama pull mistral

# List all installed models
docker exec ollama-local ollama list
```

## Configuration

### Environment Variables

Set these in `docker-compose.yml` under `ai-agent`:

```yaml
environment:
  - LLM_PROVIDER=ollama           # Use Ollama as LLM provider
  - OLLAMA_URL=http://ollama:11434 # Ollama service URL
  - OLLAMA_MODEL=llama2            # Model to use (must be pulled first)
```

### Change Model

Edit `docker-compose.yml`:
```yaml
ai-agent:
  environment:
    - OLLAMA_MODEL=mistral  # Change from llama2 to mistral
```

Then restart:
```powershell
docker-compose restart ai-agent
```

## Monitoring Ollama

### Check Ollama Status
```powershell
# Is Ollama running?
curl http://localhost:11434/api/tags

# You should see:
# {"models":[{"name":"llama2:latest"...}]}
```

### View Ollama Logs
```powershell
docker logs ollama-local -f

# Follow logs in real-time
docker logs ollama-local --tail 50 -f
```

### Monitor Performance
While chatting, check resource usage:
```powershell
docker stats ollama-local
```

## Testing

### 1. Test Ollama Directly
```powershell
# Make a direct request to Ollama
curl -X POST http://localhost:11434/api/generate `
  -H "Content-Type: application/json" `
  -d @'
{
  "model": "llama2",
  "prompt": "Why is the sky blue?",
  "stream": false
}
'@
```

### 2. Test via Chat UI
- Open: http://localhost:8000/chat-ui
- Type a message
- Watch the AI respond!

### 3. Check Agent Logs
```powershell
docker logs ai-agent-local -f
```

Look for:
```
INFO:agent:Chat message: Your question here
INFO:agent:Calling Ollama at http://ollama:11434 with model llama2
INFO:agent:Ollama response: The response...
```

## Troubleshooting

### Error: "Cannot connect to Ollama"
**Problem:** Agent can't reach Ollama
```
HTTPException: 503 Cannot connect to Ollama at http://localhost:11434
```

**Solution:**
1. Check Ollama is running:
   ```powershell
   docker ps | grep ollama
   ```
2. Verify it's using the correct URL:
   - In Docker Compose: `http://ollama:11434` (service name)
   - From Docker Desktop: `http://localhost:11434` or `http://host.docker.internal:11434`

### Error: "Model not found"
**Problem:** Requested model not downloaded
```
"error": "model \"mistral\" not found"
```

**Solution:**
```powershell
# Pull the model first
docker exec ollama-local ollama pull mistral

# List what you have
docker exec ollama-local ollama list
```

### Slow Responses
**Problem:** Model takes too long to respond

**Solutions:**
1. Use a smaller model (orca-mini, neural-chat)
2. Increase timeout in agent.py (currently 60 seconds)
3. Add GPU support (see below)

### Out of Memory
**Problem:** Ollama crashes or Docker Desktop is slow

**Solutions:**
1. Switch to smaller model: `orca-mini` instead of `llama2`
2. Increase Docker Desktop memory:
   - Settings → Resources → Memory → Increase to 8GB+
3. Stop unused containers

## GPU Support (Advanced)

To use GPU acceleration (if you have NVIDIA GPU):

1. Install NVIDIA Docker runtime:
   ```powershell
   # Follow: https://docs.docker.com/config/containers/resource_constraints/#gpu
   ```

2. Uncomment in `docker-compose.yml`:
   ```yaml
   ollama:
     runtime: nvidia
     environment:
       - NVIDIA_VISIBLE_DEVICES=all
   ```

3. Restart:
   ```powershell
   docker-compose restart ollama
   ```

## Switching Providers

You can easily switch between LLM providers:

### Switch to Mock (fastest for testing)
```yaml
environment:
  - LLM_PROVIDER=mock
```

### Switch to OpenAI
```yaml
environment:
  - LLM_PROVIDER=openai
  - OPENAI_API_KEY=sk-your-key-here
```

### Switch to AWS Bedrock
```yaml
environment:
  - LLM_PROVIDER=bedrock
  - AWS_REGION=us-east-1
```

### Switch back to Ollama
```yaml
environment:
  - LLM_PROVIDER=ollama
  - OLLAMA_URL=http://ollama:11434
  - OLLAMA_MODEL=llama2
```

## Performance Tips

1. **Warm up the model:** First query is slower (model loading)
2. **Use smaller models:** orca-mini is ~50 tokens/sec
3. **Increase context:** Set longer timeouts for complex questions
4. **Batch questions:** Send multiple at once for better throughput
5. **Monitor memory:** Watch `docker stats ollama-local`

## Integration with Your Stack

```
┌─────────────────┐
│  Chat UI        │ (http://localhost:8000/chat-ui)
│  (Browser)      │
└────────┬────────┘
         │ HTTP /chat
┌────────▼────────┐
│   FastAPI App   │ (http://localhost:8000)
│  (ai-agent)     │
└────────┬────────┘
         │ HTTP requests
┌────────▼────────┐
│    Ollama       │ (http://localhost:11434)
│  (llama2, etc)  │
└─────────────────┘

All synced to Splunk for logs/monitoring
```

## Next Steps

1. ✅ Start with docker-compose
2. ✅ Pull a model: `docker exec ollama-local ollama pull llama2`
3. ✅ Open chat UI: http://localhost:8000/chat-ui
4. ✅ Ask it questions!
5. ✅ Try different models
6. ✅ Monitor performance

Enjoy your local AI agent! 🚀
