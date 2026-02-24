# AI Agent Deployment - Quick Start

## 5-Minute Setup

### Prerequisites Check
```bash
aws --version
kubectl version --client
helm version
eksctl version
docker --version
```

### Environment Variables
```bash
export CLUSTER_NAME="ai-agent-cluster"
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

### Step 1: Create EKS Cluster (5-10 minutes)
```bash
cd aws
bash create-eks-cluster.sh
```

### Step 2: Install Karpenter (2-3 minutes)
```bash
cd karpenter
bash install.sh
```

### Step 3: Build and Push Docker Image (2-5 minutes)
```bash
cd aws
bash build-and-push-image.sh
```

### Step 4: Deploy Application (1-2 minutes)
```bash
cd aws
bash deploy.sh
```

### Step 5: Access Your Application
```bash
# Get LoadBalancer address
kubectl get svc ai-agent -n ai-agent

# Test API
curl http://<LOAD_BALANCER_IP>/health
curl -X POST http://<LOAD_BALANCER_IP>/process \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}'
```

## File Structure

```
ai-agent-deployment/
├── app/                           # Python application
│   ├── agent.py                   # Main FastAPI application
│   └── requirements.txt            # Python dependencies
├── docker/
│   └── Dockerfile                 # Container configuration
├── kubernetes/                    # K8s manifests
│   ├── namespace.yaml             # Namespace definition
│   ├── deployment.yaml            # App deployment
│   ├── service.yaml               # Load balancer & cluster IP services
│   ├── hpa.yaml                   # Horizontal Pod Autoscaler
│   ├── configmap.yaml             # Configuration
│   ├── secrets.yaml               # Sensitive data (update before deploy)
│   ├── rbac.yaml                  # Role-based access control
│   └── pdb.yaml                   # Pod disruption budget
├── karpenter/                    # Karpenter auto-scaling
│   ├── install.sh                 # Installation script
│   ├── nodepool.yaml              # Node pool configuration
│   └── iam-policy.json            # IAM policy for controller
├── aws/                           # AWS infrastructure scripts
│   ├── create-eks-cluster.sh      # EKS cluster creation
│   ├── build-and-push-image.sh    # Docker build & ECR push
│   └── deploy.sh                  # Application deployment
├── DEPLOYMENT_GUIDE.md            # Comprehensive guide
├── QUICK_START.md                 # This file
└── Dockerfile                     # Root dockerfile
```

## Configuration

### Update Before Deploying

1. **ECR Registry**: Update image registry in `kubernetes/deployment.yaml`
2. **Secrets**: Add real values to `kubernetes/secrets.yaml`
3. **Region**: Set `AWS_REGION` environment variable
4. **Instance Types**: Modify `karpenter/nodepool.yaml` for different instance types
5. **Replicas**: Adjust min/max in HPA and Karpenter settings

## Common Commands

```bash
# Cluster info
kubectl cluster-info
kubectl get nodes
kubectl get namespaces

# Deployment status
kubectl get deployment -n ai-agent
kubectl get pods -n ai-agent
kubectl get svc -n ai-agent

# Logs
kubectl logs -f deployment/ai-agent -n ai-agent -c ai-agent

# Resource usage
kubectl top nodes
kubectl top pods -n ai-agent

# Scale
kubectl scale deployment ai-agent -n ai-agent --replicas=5

# Rollback
kubectl rollout undo deployment/ai-agent -n ai-agent

# Delete all
kubectl delete namespace ai-agent
```

## Monitoring

```bash
# Pod metrics
kubectl describe pod <POD_NAME> -n ai-agent

# Node metrics
kubectl describe node <NODE_NAME>

# HPA status
kubectl get hpa -n ai-agent -w

# Events
kubectl get events -n ai-agent --sort-by='.lastTimestamp'
```

## Troubleshooting

**Pod not starting?**
```bash
kubectl describe pod <POD_NAME> -n ai-agent
kubectl logs <POD_NAME> -n ai-agent
```

**Can't access service?**
```bash
# Check service
kubectl get svc ai-agent -n ai-agent

# Check endpoints
kubectl get endpoints -n ai-agent

# Check pod is running
kubectl get pods -n ai-agent
```

**Running out of resources?**
```bash
# Check node resources
kubectl describe nodes

# Check Karpenter logs
kubectl logs -f -n karpenter -l app.kubernetes.io/name=karpenter
```

## Cleanup

```bash
# Delete namespace and all resources
kubectl delete namespace ai-agent

# Delete cluster
eksctl delete cluster --name ${CLUSTER_NAME} --region ${AWS_REGION}

# Delete ECR repository
aws ecr delete-repository --repository-name ai-agent --region ${AWS_REGION} --force
```

## Next Steps

1. Configure proper secrets and API keys
2. Set up monitoring and alerts (CloudWatch)
3. Configure logging (CloudWatch Logs)
4. Set up CI/CD pipeline (GitHub Actions, GitLab CI)
5. Implement backup and disaster recovery
6. Add custom metrics and dashboards
7. Configure SSL/TLS certificates
8. Set up VPC peering or bastion hosts

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for comprehensive documentation.
