# Local Development Guide

Complete guide for running the entire AI Agent stack locally without AWS.

## Prerequisites

### For Docker Compose (Lightweight)
- Docker Desktop (includes Docker + Kubernetes)
- 4GB RAM, 2GB disk space

### For Local Kubernetes
- Docker Desktop with Kubernetes enabled, OR
- Minikube/Kind installed
- kubectl installed
- 8GB RAM, 5GB disk space

### Tools

```bash
# macOS
brew install docker minikube kubectl docker-compose

# Windows (using Chocolatey)
choco install docker-desktop minikube kubectl

# Linux
sudo apt-get install docker.io minikube kubectl docker-compose
```

## Option 1: Docker Compose (Fastest - 2 minutes)

Perfect for quick testing and development.

### Setup

```bash
cd ai-agent-deployment
docker-compose up -d
```

### Test the Application

```bash
# Health check
curl http://localhost:8000/health

# Process message
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"message":"What is AI?", "context":{"language":"en"}}'

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}'
```

### Monitor

```bash
# View logs
docker-compose logs -f ai-agent

# CPU/Memory usage
docker stats ai-agent-local

# List containers
docker-compose ps
```

### Access Services

- **API**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### Development Workflow

```bash
# Make changes to app/agent.py
# Container auto-reloads (volume mounted)

# View changes
curl http://localhost:8000/health

# Rebuild if needed
docker-compose build --no-cache

# Restart
docker-compose restart ai-agent

# Cleanup
docker-compose down
```

### Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes
docker-compose down -v

# Remove images
docker rmi ai-agent-deployment_ai-agent
```

---

## Option 2: Local Kubernetes with Docker Desktop (5 minutes)

Great for testing Kubernetes manifests locally.

### Enable Kubernetes

1. Open Docker Desktop
2. Settings → Kubernetes → Enable Kubernetes
3. Wait for it to start (watch status bar)
4. Verify: `kubectl cluster-info`

### Deploy

```bash
# Create namespace and deploy
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/hpa.yaml
kubectl apply -f kubernetes/rbac.yaml
kubectl apply -f kubernetes/pdb.yaml
```

### Verify Deployment

```bash
# Check resources
kubectl get namespace
kubectl get deployment -n ai-agent
kubectl get pods -n ai-agent
kubectl get svc -n ai-agent

# Describe pod for details
kubectl describe pod <POD_NAME> -n ai-agent

# View logs
kubectl logs -f deployment/ai-agent -n ai-agent
```

### Access Application

```bash
# Method 1: Port forward (recommended)
kubectl port-forward -n ai-agent svc/ai-agent 8000:80

# Method 2: Get service IP (may not have external IP locally)
kubectl get svc -n ai-agent

# Test API
curl http://localhost:8000/health
```

### Test Scaling

```bash
# Terminal 1: Watch HPA
kubectl get hpa -n ai-agent -w

# Terminal 2: Watch pods
kubectl get pods -n ai-agent -w

# Terminal 3: Generate load
for i in {1..100}; do
  curl -X POST http://localhost:8000/process \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"Test $i\"}" &
done
wait

# Pods should scale up!
```

### Cleanup

```bash
# Delete namespace and all resources
kubectl delete namespace ai-agent

# Or delete individual resources
kubectl delete deployment ai-agent -n ai-agent
kubectl delete service ai-agent -n ai-agent
```

---

## Option 3: Minikube (Most Realistic Local K8s)

Best for testing in a realistic single-node Kubernetes cluster.

### Install

```bash
# macOS
brew install minikube

# Windows
choco install minikube

# Linux
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

### Start Cluster

```bash
# Start minikube with sufficient resources
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=20g \
  --driver=docker

# Verify
minikube status
kubectl cluster-info
```

### Use Local Docker Images

```bash
# Build image in minikube
eval $(minikube docker-env)

# Build (this builds in minikube's docker)
docker build -t ai-agent:latest .

# Or set imagePullPolicy to Never
# Edit deployment.yaml:
# imagePullPolicy: Never

# Deploy
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

### Access Application

```bash
# Get minikube IP
MINIKUBE_IP=$(minikube ip)

# Access via port-forward
kubectl port-forward -n ai-agent svc/ai-agent 8000:80

# Or get service type
kubectl get svc -n ai-agent

# Access via NodePort service (if you create one)
curl http://$MINIKUBE_IP:8000/health
```

### Dashboard

```bash
# Open Kubernetes dashboard
minikube dashboard
```

### Cleanup

```bash
minikube stop      # Pause cluster
minikube delete    # Delete cluster
```

---

## Option 4: Kind (Kubernetes in Docker - Lightweight)

Lightweight alternative to Minikube.

### Install

```bash
# macOS
brew install kind

# Windows
choco install kind

# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### Create Cluster

```bash
# Create kind cluster
kind create cluster --name ai-agent-local

# Verify
kubectl cluster-info --context kind-ai-agent-local
```

### Build and Load Image

```bash
# Build image
docker build -t ai-agent:latest .

# Load into kind
kind load docker-image ai-agent:latest --name ai-agent-local

# Deploy with imagePullPolicy: Never
# Edit kubernetes/deployment.yaml
```

### Deploy

```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml

# Access via port-forward
kubectl port-forward -n ai-agent svc/ai-agent 8000:80
```

### Cleanup

```bash
kind delete cluster --name ai-agent-local
```

---

## LocalStack (Mock AWS Services Locally)

For testing with AWS SDK calls (Bedrock, S3, etc.).

### Install

```bash
pip install localstack localstack-ext
```

### Run LocalStack

```bash
# Using Docker
docker run --rm -it -p 4566:4566 localstack/localstack

# Using localstack CLI
localstack start -d

# View logs
localstack logs -f
```

### Configure AWS CLI

```bash
# Point to local LocalStack
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Test
aws s3 ls --endpoint-url=http://localhost:4566
```

### Update App to Use LocalStack

```python
# In app/agent.py
import os
import boto3

bedrock_client = boto3.client(
    'bedrock-runtime',
    endpoint_url=os.getenv('AWS_ENDPOINT_URL', 'https://bedrock.us-east-1.amazonaws.com'),
    region_name='us-east-1'
)
```

### Update docker-compose.yml

```yaml
services:
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3,bedrock,sqs
      - DEBUG=1
    volumes:
      - "${TMPDIR}/.localstack:/tmp/localstack"

  # ... rest of services
```

---

## Local Testing Workflow

### 1. Develop Locally

```bash
# Start Docker Compose
docker-compose up

# Edit code (auto-reloads)
# Test changes
curl http://localhost:8000/health
```

### 2. Test Kubernetes Manifests

```bash
# Switch to local k8s
kubectl config use-context docker-desktop

# Deploy locally
kubectl apply -f kubernetes/

# Test
kubectl port-forward svc/ai-agent 8000:80 -n ai-agent
curl http://localhost:8000/health
```

### 3. Load Test Locally

```bash
# Install hey tool
go install github.com/rakyll/hey@latest

# Run load test
hey -n 1000 -c 50 http://localhost:8000/health

# Monitor scaling
watch 'kubectl get pods -n ai-agent'
```

### 4. Before AWS Deployment

```bash
# Build production image
docker build -t ai-agent:latest .

# Test image
docker run -p 8000:8000 ai-agent:latest

# Tag for ECR
docker tag ai-agent:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/ai-agent:latest

# Push when ready
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/ai-agent:latest
```

---

## Common Local Development Commands

```bash
# Docker Compose
docker-compose up                    # Start
docker-compose down                  # Stop
docker-compose logs -f ai-agent      # Logs
docker-compose build --no-cache      # Rebuild
docker-compose ps                    # Status

# Local Kubernetes (Docker Desktop / Kind)
kubectl apply -f kubernetes/         # Deploy all
kubectl delete namespace ai-agent    # Remove all
kubectl get pods -n ai-agent         # List pods
kubectl logs -f deployment/ai-agent -n ai-agent    # Logs
kubectl port-forward svc/ai-agent 8000:80 -n ai-agent  # Access
kubectl describe pod <POD> -n ai-agent   # Debug

# Minikube
minikube start                       # Start
minikube stop                        # Stop
minikube delete                      # Delete
minikube dashboard                   # Open dashboard
eval $(minikube docker-env)         # Use minikube docker
```

---

## Troubleshooting Local Setup

### Issue: Port 8000 already in use

```bash
# Kill process using port
lsof -i :8000
kill -9 <PID>

# Or use different port
docker run -p 8001:8000 ai-agent:latest
```

### Issue: Out of memory

```bash
# Docker Desktop: Increase memory in Preferences
# Minikube: Restart with more memory
minikube start --memory=16384

# Docker Compose: Limit service memory
# Edit docker-compose.yml
services:
  ai-agent:
    deploy:
      resources:
        limits:
          memory: 1G
```

### Issue: Image not found in Kubernetes

```bash
# Make sure image is built locally
docker build -t ai-agent:latest .

# For Minikube/Kind: Load image
minikube load docker-image ai-agent:latest
kind load docker-image ai-agent:latest

# Update ImagePullPolicy in deployment.yaml
imagePullPolicy: Never
```

### Issue: Can't reach service from localhost

```bash
# Use port-forward
kubectl port-forward -n ai-agent svc/ai-agent 8000:80

# Or check if service has endpoint
kubectl get endpoints -n ai-agent
kubectl describe svc ai-agent -n ai-agent
```

---

## Summary Table

| Method | Speed | Cost | K8s? | Production-like | Best For |
|--------|-------|------|------|-----------------|----------|
| **Docker Compose** | 2 min | Free | ❌ | Basic | Quick dev, prototyping |
| **Docker Desktop K8s** | 5 min | Free | ✅ | Good | Testing manifests |
| **Minikube** | 5 min | Free | ✅ | Excellent | Full testing |
| **Kind** | 3 min | Free | ✅ | Excellent | CI/CD, quick tests |
| **LocalStack+K8s** | 10 min | Free | ✅ | Full | AWS integration testing |

---

## Next Steps

1. **Quick Test**: `docker-compose up`
2. **Test K8s**: Use Docker Desktop Kubernetes
3. **Full Test**: Spin up Minikube
4. **AWS Prep**: Build image, tag, push to ECR
5. **Deploy**: Run AWS deployment scripts

See [README.md](README.md) for AWS deployment.
