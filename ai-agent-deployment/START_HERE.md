# 🚀 Start Here - 2 Minutes to Getting Started

**No AWS account needed. Everything works locally.**

## Option 1: Docker Compose (Easiest)

```bash
# Make sure Docker is running
docker-compose up

# In another terminal, test:
curl http://localhost:8000/health

# You'll see: {"status": "healthy", "timestamp": "..."}
```

✅ Done! API is running at http://localhost:8000

---

## Option 2: Local Kubernetes (5 min)

**Prerequisites**: Docker Desktop with Kubernetes enabled

```bash
# Deploy to local Kubernetes
make k8s-local

# In another terminal:
kubectl port-forward -n ai-agent svc/ai-agent 8000:80

# Test:
curl http://localhost:8000/health
```

✅ Running with Kubernetes! Watch pods scale:
```bash
kubectl get pods -n ai-agent -w
```

---

## Option 3: Fastest Experience

```bash
bash run-locally.sh
```
Then follow the interactive prompts.

---

## What Can You Do Now?

### Test the API
```bash
# Process a message
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello, what is AI?"}'

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How are you?"}'
```

### View Logs
```bash
# Docker Compose
docker-compose logs -f ai-agent

# Kubernetes
kubectl logs -f deployment/ai-agent -n ai-agent
```

### Modify Code
- Edit `app/agent.py`
- Changes auto-reload in Docker Compose
- Just refresh/resend requests to see changes

### Generate Load & Watch Scaling
```bash
# Terminal 1: Watch pods
kubectl get pods -n ai-agent -w

# Terminal 2: Send 100 requests
for i in {1..100}; do
  curl http://localhost:8000/health &
done
```

---

## Next: Learn More

### Want production deployment?
→ See [QUICK_START.md](QUICK_START.md)

### Want detailed local setup guide?
→ See [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)

### Want local vs AWS comparison?
→ See [LOCAL_VS_AWS.md](LOCAL_VS_AWS.md)

### Want AWS deployment?
→ See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Want comprehensive setup?
→ See [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)

---

## Troubleshooting

### Port 8000 already in use?
```bash
# Find and kill the process
lsof -i :8000
kill -9 <PID>

# Or use different port
# Edit docker-compose.yml: "8001:8000"
```

### Docker not running?
Open Docker Desktop

### Can't connect to localhost:8000?
```bash
# Check if container is running
docker ps

# Check logs
docker-compose logs

# Restart
docker-compose down
docker-compose up
```

### Kubernetes not running (Docker Desktop)?
1. Open Docker Desktop
2. Settings → Kubernetes → Enable Kubernetes
3. Wait for it to start
4. Try again

---

## 📚 Documentation Structure

| Document | Purpose | Time |
|----------|---------|------|
| **This file** | Get started NOW | 2 min ↑ |
| [LOCAL_VS_AWS.md](LOCAL_VS_AWS.md) | Understand what runs where | 5 min |
| [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) | Detailed local setup guide | 15 min |
| [README.md](README.md) | Project overview | 10 min |
| [QUICK_START.md](QUICK_START.md) | AWS 5-minute setup | 5 min |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Complete AWS guide | 30 min |

---

## 🎯 Your Journey

```
START HERE
    ↓
    docker-compose up
    ↓
    Explore the API
    ↓
    Try LocalKubernetes (make k8s-local)
    ↓
    Learn how to scale pods
    ↓
    Ready for AWS? (optional)
      ↓
      cd aws && bash create-eks-cluster.sh
      ...
```

---

## ✨ What You Get

- ✅ Running Python AI Agent API
- ✅ Docker containerization
- ✅ Kubernetes (optional, local)
- ✅ Auto-scaling (with K8s)
- ✅ Health checks
- ✅ 100% working code
- ✅ Production-ready defaults

---

## 🔗 Quick Links

**Local Development**:
- [LOCAL_VS_AWS.md](LOCAL_VS_AWS.md) - What runs locally
- [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) - Setup details
- [docker-compose.yml](docker-compose.yml) - Container config

**AWS Deployment**:
- [QUICK_START.md](QUICK_START.md) - Quick AWS setup
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Detailed AWS guide
- [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) - Step-by-step

**Code**:
- [app/agent.py](app/agent.py) - Main application
- [kubernetes/](kubernetes/) - K8s manifests
- [aws/](aws/) - AWS scripts

---

## 🎓 Zero Assumptions

- ✅ No Kubernetes knowledge needed
- ✅ No AWS knowledge needed  
- ✅ No Docker expertise required
- ✅ Just need Docker Desktop installed

Everything is interactive and documented!

---

**Ready?** 

```bash
docker-compose up
```

That's it! 🎉
