# Python AI Agent on AWS EKS with Karpenter

A production-ready Python AI agent deployment on AWS featuring:

- **Python FastAPI Application** - Scalable API for AI processing
- **Docker Containerization** - Optimized multi-stage builds
- **Kubernetes (EKS)** - AWS managed Kubernetes service
- **Karpenter** - Advanced node auto-scaling and optimization
- **Horizontal Pod Autoscaler** - Pod-level scaling (3-20 replicas)
- **Security** - RBAC, non-root containers, network policies
- **Monitoring** - Health checks, pod disruption budgets, metrics

## ✅ Runs Locally (No AWS Required!)

Yes! Most of this stack runs completely locally:

| Component | Local | Notes |
|-----------|-------|-------|
| **Python AI Agent** | ✅ | FastAPI runs anywhere |
| **Docker** | ✅ | Containerize on any machine |
| **Kubernetes** | ✅ | Docker Desktop or Minikube |
| **HPA & Scaling** | ✅ | Works in local k8s |
| **EKS** | ❌ | AWS-only service |
| **Karpenter** | ❌ | AWS-specific auto-scaler |
| **ECR** | ❌ | Use Docker Hub or local registry |

**Start locally with:** `docker-compose up` or `make k8s-local`

## Quick Start - Three Options

### 🚀 Option 1: Docker Compose (2 minutes - No AWS needed)
```bash
docker-compose up
curl http://localhost:8000/health
```

### 🎯 Option 2: Local Kubernetes (5-10 minutes - No AWS needed)
```bash
make k8s-local
kubectl port-forward -n ai-agent svc/ai-agent 8000:80
curl http://localhost:8000/health
```

### ☁️ Option 3: AWS EKS Deployment (15-25 minutes)
```bash
export CLUSTER_NAME="ai-agent-cluster"
export AWS_REGION="us-east-1"

cd aws && bash create-eks-cluster.sh
cd ../karpenter && bash install.sh
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
