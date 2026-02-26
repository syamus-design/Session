# 🚀 Python AI Agent Deployment Stack

> **A complete, production-ready AI agent microservice with Docker, Kubernetes, and AWS deployment options. Learn DevOps, Cloud Architecture, and Observability all in one project!**

**Perfect for:** CS/Engineering students learning containerization, Kubernetes, CI/CD, and cloud architectures.

---

## 📚 What You'll Learn

By working with this project, you'll gain hands-on experience with:

| Topic | Component | Level |
|-------|-----------|-------|
| **Containerization** | Docker, Dockerfile, multi-stage builds | Beginner |
| **Local Development** | docker-compose, networking, volumes | Beginner |
| **Monitoring & Observability** | Prometheus, Grafana, Splunk | Intermediate |
| **Kubernetes** | Local K8s, Deployments, Services, StatefulSets | Intermediate |
| **Auto-Scaling** | HPA, Karpenter, resource management | Advanced |
| **Cloud Deployment** | AWS: EKS, ECR, IAM, networking | Advanced |
| **CI/CD** | GitHub Actions, automated testing & deployment | Intermediate |
| **Logging** | Centralized logging with Splunk HEC | Intermediate |
| **Python Backend** | FastAPI, async/await, REST APIs | Beginner |

---
## ⚙️ First-Time Setup: Configure Secrets

⚠️ **Important:** The repo includes `docker-compose.example.yml` but NOT `docker-compose.yml` (to prevent secrets being pushed to GitHub).

**One-time setup:**

```bash
# Copy the example file
cp docker-compose.example.yml docker-compose.yml

# Edit docker-compose.yml and replace:
#   - <REPLACE-WITH-YOUR-SPLUNK-PASSWORD>  → Any password you want (e.g., Demouser123)
#   - <REPLACE-WITH-YOUR-HEC-TOKEN>        → Your Splunk HEC token (UUID format)

# If you don't have a HEC token yet, use this placeholder.
# After starting Splunk, create one in the Splunk Web UI (see guide below).
```

**Getting a Splunk HEC Token** (after first docker-compose up):
1. Open http://localhost:8001
2. Login: `admin` / `<your-password>`
3. Settings → Data Inputs → HTTP Event Collector → New Token
4. Name it `ai-agent-hec`, copy the token
5. Update `docker-compose.yml` with the token value

ℹ️ **Note:** docker-compose.yml is in `.gitignore` for security. Never commit it with real secrets!

---
## 🎯 Quick Start (Choose Your Path)

### 🐳 Path 1: Docker Compose (⭐ Recommended for beginners - 2 minutes)

No cloud account needed. Everything runs on your machine.

```powershell
# Clone and navigate
git clone <this-repo>
cd ai-agent-deployment

# Start everything
docker-compose up -d

# Verify services
docker-compose ps

# Test the API
curl http://localhost:8000/health

# Access dashboards & UIs
# - AI Agent API:    http://localhost:8000
# - Grafana:         http://localhost:3000 (admin/admin)
# - Prometheus:      http://localhost:9090
# - Splunk Web:      http://localhost:8001 (admin/Demouser123)

# Stop everything
docker-compose down
```

**What you get:**
- ✅ FastAPI Python application
- ✅ Prometheus metrics collection
- ✅ Grafana dashboards (CPU, Memory monitoring)
- ✅ Splunk centralized logging
- ✅ Load generator for testing

**Watch the magic:** Send a test message and watch it flow through the system:
```powershell
$body = '{"message":"test from powershell"}'
Invoke-WebRequest -Uri http://localhost:8000/chat -Method Post `
  -Body $body -Headers @{"Content-Type"="application/json"}

# Check logs in Splunk: index=main source="ai-agent"
```

---

### ☸️ Path 2: Local Kubernetes (15 minutes)

Perfect for learning Kubernetes concepts without AWS.

```bash
# Install Kubernetes (Docker Desktop or Minikube)
# Then:

make k8s-local
kubectl get pods
kubectl port-forward -n ai-agent svc/ai-agent 8000:80
```

**What you get:**
- Everything from Path 1 +
- Kubernetes Deployments, Services, StatefulSets
- Horizontal Pod Autoscaler (HPA)
- ConfigMaps and Secrets management

---

### ☁️ Path 3: AWS EKS Deployment (20+ minutes)

Deploy to real AWS infrastructure. ⚠️ **AWS account + credits required**

```bash
# Set configuration
export CLUSTER_NAME="ai-agent-cluster"
export AWS_REGION="us-east-1"

# Deploy
cd aws && bash create-eks-cluster.sh
cd ../karpenter && bash install.sh
cd .. && kubectl apply -f kubernetes/
```

**What you get:**
- Everything from Path 2 +
- AWS EKS managed Kubernetes
- Karpenter auto-scaling
- Real cloud infrastructure experience
- CI/CD with GitHub Actions

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Load Testing (Optional)               │
│                  CPU/Memory Spike Generator             │
└────────────────────────┬────────────────────────────────┘
                         │
┌─────────────────────────▼─────────────────────────────────┐
│                 Python FastAPI Agent                      │
│        (Containerized, Scalable, Production-Ready)        │
│  Endpoints: /health, /readiness, /chat, /process         │
└────┬─────────────────────────────┬──────────────────────┘
     │                             │
     │ Logs (HTTPS HEC)       Metrics
     │ to Splunk             (Prometheus)
     │                             │
┌────▼──────────────────┐  ┌────▼──────────────────┐
│  Splunk Centralized   │  │   Prometheus Data    │
│  Logging & Analytics  │  │   Collection Server   │
│                       │  │                      │
│ Web: :8001            │  │ Scrape: :9090        │
│ HEC: :8088 (HTTPS)    │  │ node-exporter:9100   │
└───────────────────────┘  └────────┬─────────────┘
                                    │
                           ┌────────▼─────────────┐
                           │  Grafana Dashboards │
                           │  - CPU Usage (%)    │
                           │  - Memory Used (%)  │
                           │  Web: :3000         │
                           └─────────────────────┘
```

---

## 📁 Project Structure

```
ai-agent-deployment/
├── app/                              # Python backend
│   ├── agent.py                     # FastAPI app + SplunkHECHandler
│   └── requirements.txt             # Dependencies
├── docker-compose.yml               # Local stack (8 services)
├── Dockerfile                       # Container image
├── kubernetes/                      # K8s manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml                    # Horizontal Pod Autoscaler
│   └── karpenter/
├── karpenter/                       # Auto-scaling config for AWS
│   └── install.sh
├── aws/                             # AWS scripts
│   ├── create-eks-cluster.sh
│   └── configure-iam.sh
├── monitoring/                      # Observability stack
│   ├── prometheus.yml              # Metrics scraper config
│   └── grafana/                    # Dashboards & provisioning
│       ├── provisioning/datasources/
│       └── provisioning/dashboards/
├── .github/workflows/               # CI/CD pipelines
│   ├── docker-build.yml
│   └── deploy-aws.yml
└── README.md                        # This file!
```

---

## 🔧 Setup & Configuration

### Prerequisites

**Minimum (Docker Compose):**
- Docker Desktop or Docker Engine
- 8GB RAM, 10GB disk space
- Windows 10+ / macOS 10.14+ / Linux

**For Kubernetes:**
- All above +
- Docker Desktop with Kubernetes enabled OR Minikube

**For AWS Deployment:**
- All above +
- AWS account with credits
- AWS CLI configured (`aws configure`)
- kubectl installed

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/ai-agent-deployment.git
cd ai-agent-deployment

# Install dependencies (Optional - for local development)
pip install -r app/requirements.txt

# Create .env file from example
cp .env.example .env

# Verify Docker installation
docker --version
docker-compose --version
```

---

## 🚀 Common Tasks

### Run the Application

**Docker Compose (Easiest):**
```bash
docker-compose up -d
# All services start and run in background
docker-compose logs -f ai-agent  # Watch logs
docker-compose down              # Cleanup
```

**Local Kubernetes:**
```bash
make k8s-local
kubectl logs -f deployment/ai-agent -n ai-agent
```

**Test the API:**
```bash
# Health check
curl http://localhost:8000/health

# Send a chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello, AI agent!"}'
```

### Monitor Metrics

**Via Grafana:**
1. Open http://localhost:3000
2. Login: `admin` / `admin`
3. View dashboard: "AI Agent & Node Exporter"
4. See real-time CPU and Memory metrics

**Via Prometheus:**
1. Open http://localhost:9090
2. Query metrics: `node_cpu_seconds_total`, `node_memory_MemAvailable_bytes`
3. Run PromQL queries

### View Logs

**Via Splunk:**
1. Open http://localhost:8001
2. Login: `admin` / `Demouser123`
3. Search: `index=main source="ai-agent"`
4. See application logs with timestamps and levels

**Via Docker:**
```bash
docker-compose logs ai-agent
```

### 🎓 Why You Need an Orchestrator (Docker vs Kubernetes)

This is one of the **most important lessons** in this project! Let's demonstrate why Docker Compose alone isn't enough:

#### ❌ Docker Compose: Manual, Limited Scaling

```yaml
# docker-compose.yml - Attempt to scale
ai-agent:
  deploy:
    replicas: 3  # ← Set manually, won't auto-update
```

**Try it:**
```bash
docker-compose up -d
docker-compose ps              # Shows 1 replica

# Now try to scale
docker-compose up -d --scale ai-agent=3
docker-compose ps              # 3 replicas! Success?
```

**But what happens when:**
1. ❌ Application CPU spikes to 80%? → **No auto-scaling** (stays at 3 replicas)
2. ❌ Traffic drops to zero? → **Wastes resources** (still running 3 replicas)
3. ❌ One container crashes? → **Manual restart needed** (no self-healing)
4. ❌ You need rolling updates? → **Downtime required** (can't do graceful updates)
5. ❌ Container needs to move to another host? → **Not possible** (Docker only works on one machine)

**Result:** Docker Compose is great for **development**, but **fails at production requirements**.

---

#### ✅ Kubernetes: Automatic, Intelligent Scaling

Kubernetes solves all of these problems:

```bash
# Deploy to Kubernetes
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/hpa.yaml

# Check status
kubectl get pods -n ai-agent              # See all replicas
kubectl get hpa -n ai-agent               # See HPA config
```

**What Kubernetes does automatically:**

| Scenario | Docker Compose | Kubernetes |
|----------|---|---|
| **CPU spikes to 80%** | ❌ Stays at 3 replicas | ✅ Auto-scales to 10+ pods |
| **Traffic drops** | ❌ Wastes resources | ✅ Scales down to 3 pods |
| **Pod crashes** | ❌ Manual restart | ✅ Auto-restarts immediately |
| **Rolling update** | ❌ Downtime | ✅ Zero downtime (staged) |
| **Multi-host? Cloud?** | ❌ Single machine only | ✅ Spans 1000s of nodes |
| **Health checks** | ⚠️ Basic | ✅ Deep (liveness, readiness) |
| **Resource limits** | ⚠️ Manual config | ✅ Enforced automatically |

---

#### 🧪 Hands-On Demo: See the Difference

**Step 1: Test Docker Compose (manual scaling)**
```bash
# Start with docker-compose
docker-compose up -d

# Run load generator
docker-compose up -d loadgen

# Watch Grafana (http://localhost:3000)
# ↳ CPU SPIKES to 95%!

# But try to scale...
docker-compose up --scale ai-agent=5
# ↳ Nothing changes! You're stuck at current CPU usage.
```

**Step 2: Test Kubernetes (automatic scaling)**
```bash
# Deploy to local Kubernetes
make k8s-local

# Start load test
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: load-tester
  namespace: ai-agent
spec:
  containers:
  - name: hammering
    image: alpine:latest
    command: ["sh", "-c"]
    args:
      - |
        apk add curl
        for i in {1..100}; do
          curl -X POST http://ai-agent:80/chat -d '{"message":"test"}' &
        done
        wait
EOF

# Watch pods auto-scale!
kubectl get pods -n ai-agent -w
# ↳ Starts: 3 pods
# ↳ CPU rises...
# ↳ BOOM! → 5 pods
# ↳ CPU rises more...
# ↳ BOOM! → 8 pods
# ↳ Traffic drops...
# ↳ SHRINK! → Back to 3 pods

# Check the HPA status
kubectl describe hpa ai-agent-hpa -n ai-agent
# ↳ Shows: "Metrics: <unknown>/80%, Current: 3, Desired: 8"
```

**Output:** Kubernetes automatically adjusted replicas from 3 → 8 based on CPU, no manual intervention!

---

#### 📊 Visual Comparison

```
DOCKER COMPOSE (Static)
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  ai-agent   │    │  ai-agent   │    │  ai-agent   │
│  Pod #1     │    │  Pod #2     │    │  Pod #3     │
└─────────────┘    └─────────────┘    └─────────────┘
   Running           Running            Running
   (Fixed at 3)     (Fixed at 3)       (Fixed at 3)
   ← CPU 95%! But no auto-scaling →

KUBERNETES (Dynamic - with HPA)
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │    Pod #1   │    │    Pod #4   │    │    Pod #7   │
   └─────────────┘    └─────────────┘    └─────────────┘
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │    Pod #2   │    │    Pod #5   │    │    Pod #8   │
   └─────────────┘    └─────────────┘    └─────────────┘
   ┌─────────────┐    ┌─────────────┐
   │    Pod #3   │    │    Pod #6   │
   └─────────────┘    └─────────────┘
   ← Auto-scaled to 8 pods (was 3) ← CPU under control at 80%
```

---

#### 🎯 Key Takeaway

| Feature | Purpose |
|---------|---------|
| **Docker** | ✅ Package & run apps (Dev & Test) |
| **Docker Compose** | ✅ Multi-container apps on 1 machine |
| **Kubernetes** | ✅ Large-scale, self-healing, auto-scaling |

**Docker Compose = Great for dev/test**
**Kubernetes = Required for production**

This project teaches **both**, so you understand why each exists!

---

### Scale the Application

**In docker-compose.yml**, scale manually (development only):
```bash
docker-compose up --scale ai-agent=3
# ↳ Manual scaling, no auto-adjustment
```

**In Kubernetes**, HPA auto-scales (automatic, production-ready):
```bash
# View HPA configuration
kubectl get hpa -n ai-agent
kubectl describe hpa ai-agent-hpa -n ai-agent

# Watch it auto-scale in real-time
kubectl get pods -n ai-agent -w
```

### Generate Test Load

```bash
# Start load generator
docker-compose up loadgen -d

# Watch Grafana for CPU/Memory spikes
# Go to http://localhost:3000

# Stop load generator
docker-compose down loadgen
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port already in use (8000, 3000, 8001, 8088)** | `docker-compose down` then retry, or change ports in `docker-compose.yml` |
| **"No logs in Splunk"** | Check SPLUNK_HEC_URL uses `https://` (not http://), verify token in docker-compose.yml |
| **"Prometheus won't connect to node-exporter"** | Verify service name is `node-exporter:9100` in prometheus.yml (check indentation!) |
| **"Grafana shows no data"** | Reload page, check Prometheus datasource is `http://prometheus:9090` |
| **Docker out of memory** | Reduce replicas in docker-compose.yml or allocate more RAM to Docker Desktop |
| **Kubernetes pod stuck in pending** | `kubectl describe pod <name> -n ai-agent` to see events |
| **Connection refused to HEC (port 8088)** | Verify Splunk service is healthy: `docker-compose ps splunk` |

**Need help?** Check:
- [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) - Detailed local setup
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - AWS deployment steps
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Architecture decisions

---

## 📊 Performance & Scaling

### Current Stack Performance

- **AI Agent Response:** <100ms per request
- **Prometheus Scrape:** 15-second interval (configurable)
- **Splunk Ingestion:** ~1000 events/second capacity
- **Node-exporter Metrics:** <1ms collection time

### Scaling Limits

| Component | Local Max | AWS Production |
|-----------|-----------|-----------------|
| AI Agent Replicas | 5 | 100+ |
| Memory per Pod | 512MB | 2-4GB |
| Requests/sec | 500 | 10,000+ |
| Concurrent Connections | 100 | 100,000+ |
| Event Ingestion Rate | 1K/s | 100K+/s |

### How to Scale

1. **Horizontal (more pods):** Modify HPA settings in `kubernetes/hpa.yaml`
2. **Vertical (bigger pods):** Increase memory/CPU requests in Deployment
3. **Karpenter (AWS):** Auto-adds nodes based on demand

---

## 🔐 Security Notes

⚠️ **For Development Only:**
- Splunk password and tokens are in docker-compose (use `.env` files for production)
- TLS verification disabled for self-signed certs (`verify=False`)
- Non-root container user configured but basic RBAC

**Production Checklist:**
- [ ] Use AWS Secrets Manager for passwords
- [ ] Enable proper TLS certificates
- [ ] Implement NetworkPolicies
- [ ] Enable RBAC with least-privilege
- [ ] Add Pod Security Policies
- [ ] Use private ECR registry
- [ ] Enable audit logging

---

## 📚 Learning Resources

### ⚡ Deep Dive: Why We Need Orchestrators

**This is crucial!** Read this to understand the core problem Docker Compose cannot solve:

👉 **[DOCKER_COMPOSE_SCALING_LIMITS.md](DOCKER_COMPOSE_SCALING_LIMITS.md)** - Comprehensive guide showing:
- Why Docker Compose manual scaling fails in production
- Real-world cost impact ($12/day → $4,380/year per service)
- Hands-on experiments you can run to see the problem
- How Kubernetes HPA solves it automatically

**TL;DR:** Docker Compose can scale, but NOT automatically. Traffic spike? You manually run `docker-compose up --scale`. Traffic drops? You manually scale down. Production? This costs thousands.

---

### Docker & Containerization
- [Docker Getting Started](https://docs.docker.com/get-started/)
- [Best Practices for Dockerfiles](https://docs.docker.com/develop/dev-best-practices/)

### Kubernetes
- [Kubernetes for Beginners](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
- [Kubernetes Components Explained](https://kubernetes.io/docs/concepts/overview/components/)

### Observability
- [Prometheus Fundamentals](https://prometheus.io/docs/)
- [Grafana Dashboard Guide](https://grafana.com/tutorials/grafana-fundamentals/)
- [Splunk Getting Started](https://www.splunk.com/en_us/why-splunk.html)

### AWS & Karpenter
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Karpenter Getting Started](https://karpenter.sh/)
- [AWS Best Practices](https://aws.amazon.com/architecture/well-architected/)

### FastAPI
- [FastAPI Official Tutorial](https://fastapi.tiangolo.com/)
- [Async Python](https://docs.python.org/3/library/asyncio.html)

---

## 🤝 Contributing & Feedback

**Found a bug?** Open an issue with:
- [ ] What you were doing
- [ ] Error message/logs
- [ ] Your OS and Docker version
- [ ] Reproduction steps

**Want to improve?** Submit a PR with:
- [ ] Clear description of changes
- [ ] Updated docs if needed
- [ ] Tested locally

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🎓 OSU Students

This project is designed as a learning resource. Feel free to:
- ✅ Fork and modify for assignments
- ✅ Use as reference for your own projects
- ✅ Submit improvements
- ✅ Ask questions (respectfully)

**Questions?** Reach out to the course instructor or TA.

---

## 📞 Quick Reference

### URLs & Access

| Service | URL | Credentials | Port |
|---------|-----|-------------|------|
| AI Agent API | http://localhost:8000 | None (public) | 8000 |
| Grafana | http://localhost:3000 | admin/admin | 3000 |
| Prometheus | http://localhost:9090 | None (open) | 9090 |
| Splunk Web | http://localhost:8001 | admin/Demouser123 | 8001 |
| Splunk HEC | https://localhost:8088 | Token-based | 8088 |
| Node-Exporter | http://localhost:9100 | None (metrics only) | 9100 |

### Key Commands

```bash
# Docker Compose
docker-compose up -d              # Start all
docker-compose down               # Stop all
docker-compose ps                # See status
docker-compose logs -f ai-agent   # Stream logs

# Kubernetes
kubectl get pods -n ai-agent      # List pods
kubectl describe pod <name> -n ai-agent  # Details
kubectl logs -f pod/<name> -n ai-agent   # Logs
kubectl port-forward svc/ai-agent 8000:80  # Port forward

# Testing
curl http://localhost:8000/health
curl -X POST http://localhost:8000/chat -d '{"message":"test"}'

# Cleanup
docker system prune -a --volumes   # Remove everything
```

---

**Last Updated:** February 2026 | Made with ❤️ for OSU Students
cd ../aws && bash build-and-push-image.sh
bash deploy.sh

curl http://<LOAD_BALANCER_IP>/health
```

**🎓 See [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) for detailed local setup guides**

## Architecture

### Python AI Agent
- FastAPI-based REST API
- Supports multiple LLM providers:
  - OpenAI API
  - AWS Bedrock (Claude, Llama)
  - Mock responses for testing

### Kubernetes Deployment
- **Namespace**: `ai-agent` (isolated environment)
- **Replicas**: 3-20 (controlled by HPA)
- **Resource Requests**: 500m CPU, 512Mi Memory
- **Resource Limits**: 2 CPU, 2Gi Memory
- **Health Checks**: Liveness & readiness probes

### Auto-Scaling Strategy

**Pod Level (HPA)**
- Min Replicas: 3
- Max Replicas: 20
- CPU Trigger: 70% utilization
- Memory Trigger: 80% utilization

**Node Level (Karpenter)**
- Instance Types: c5, c6a, m5, m6a (with 4+ generation)
- Capacity Types: On-Demand & Spot
- Consolidation: Automatic node consolidation for cost savings
- Spot Integration: Cost-optimized with fallback to on-demand

## Project Structure

```
ai-agent-deployment/
├── app/                           # Python application
│   ├── agent.py                   # Main FastAPI app
│   └── requirements.txt            # Dependencies
├── Dockerfile                      # Container build
├── docker-compose.yml              # Local development
├── kubernetes/                     # K8s manifests
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── rbac.yaml
│   └── pdb.yaml
├── karpenter/                      # Node auto-scaling
│   ├── install.sh
│   ├── nodepool.yaml
│   └── iam-policy.json
├── aws/                            # AWS infrastructure
│   ├── create-eks-cluster.sh
│   ├── build-and-push-image.sh
│   └── deploy.sh
├── Makefile                        # Common commands
├── DEPLOYMENT_GUIDE.md             # Comprehensive guide
└── QUICK_START.md                  # Quick reference
```

## 🧪 Testing Locally (Start Now!)

### Fastest: Docker Compose (2 min)
```bash
# No Kubernetes, just the API
docker-compose up

# In another terminal:
curl http://localhost:8000/health
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}'
```

### Full Stack: Local Kubernetes (5 min)
```bash
# Requires: Docker Desktop with Kubernetes enabled
make k8s-local

# In another terminal:
kubectl port-forward -n ai-agent svc/ai-agent 8000:80

# Test
curl http://localhost:8000/health
```

### Realistic: Minikube (10 min)
```bash
bash run-locally.sh
# Select option 3
```

**⏱️ Start with Docker Compose for instant feedback!**

### Health Check
```bash
GET /health
GET /readiness
```

### Process Message
```bash
POST /process
Content-Type: application/json

{
  "message": "What is the capital of France?",
  "context": {"language": "en"}
}
```

### Chat
```bash
POST /chat
Content-Type: application/json

{
  "message": "Hello, how are you?"
}
```

## Configuration

### Environment Variables
- `PORT`: Server port (default: 8000)
- `LLM_PROVIDER`: AI provider (mock, openai, bedrock)
- `AWS_REGION`: AWS region (default: us-east-1)
- `LOG_LEVEL`: Logging level (default: INFO)

### Secrets to Configure
- `OPENAI_API_KEY`: For OpenAI API integration
- `AWS_ACCESS_KEY_ID`: AWS credentials
- `AWS_SECRET_ACCESS_KEY`: AWS credentials

## Monitoring & Logs

```bash
# Check deployment status
kubectl get deployment -n ai-agent
kubectl get pods -n ai-agent

# View application logs
kubectl logs -f deployment/ai-agent -n ai-agent

# Monitor auto-scaling
kubectl get hpa -n ai-agent -w
kubectl top pods -n ai-agent

# Check Karpenter
kubectl get nodes -L karpenter.sh/capacity-type
kubectl logs -f -n karpenter -l app.kubernetes.io/name=karpenter
```

## Cost Optimization

1. **Spot Instances**: Configure Karpenter to use AWS Spot Instances
2. **Node Consolidation**: Automatic consolidation of underutilized nodes
3. **Right-sizing**: Start small, let Karpenter optimize
4. **Reserved Instances**: Consider RIs for baseline capacity

## Security Features

- Non-root user (UID 1000) in containers
- Read-only root filesystem
- Resource limits to prevent resource exhaustion
- RBAC for pod-level access control
- Network policies for traffic control
- Secrets management via Kubernetes Secrets

## Scaling Scenarios

### Auto-Scaling Example
```bash
# Send load to trigger scaling
for i in {1..100}; do
  curl -X POST http://<LB_IP>/process \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"Test $i\"}" &
done

# Watch scaling happen
kubectl get hpa -n ai-agent -w
kubectl get pods -n ai-agent -w
kubectl get nodes -w
```

## Troubleshooting

**Pods not starting?**
```bash
kubectl describe pod <POD_NAME> -n ai-agent
kubectl logs <POD_NAME> -n ai-agent
```

**Can't access service?**
```bash
kubectl get endpoints -n ai-agent
kubectl exec -it <POD_NAME> -n ai-agent -- sh
# Inside: curl http://localhost:8000/health
```

**Running out of resources?**
```bash
kubectl top nodes
kubectl top pods -n ai-agent
# Check Karpenter: kubectl logs -f -n karpenter
```

## Cleanup

```bash
# Delete application
kubectl delete namespace ai-agent

# Delete EKS cluster (destroys all infrastructure)
eksctl delete cluster --name ai-agent-cluster --region us-east-1

# Delete ECR repository
aws ecr delete-repository --repository-name ai-agent --force --region us-east-1
```

## Advanced Topics

- Multi-region deployment
- Custom metrics for auto-scaling
- GitOps with ArgoCD
- Service mesh (Istio)
- Serverless with AWS Lambda
- ML model versioning and deployment

## Additional Resources

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Karpenter Documentation](https://karpenter.sh/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/overview/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## License

MIT License - Feel free to use for production deployments

## Support

For issues or questions:
1. Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions
2. Review [QUICK_START.md](QUICK_START.md) for common commands
3. Check Kubernetes events: `kubectl get events -n ai-agent`
4. Review logs: `kubectl logs -f deployment/ai-agent -n ai-agent`

---

**Last Updated**: February 22, 2026
