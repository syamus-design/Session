# AI Agent Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying a Python AI agent on AWS using Docker, Kubernetes (EKS), and Karpenter for auto-scaling.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Account                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │              AWS EKS Cluster                          │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  ┌──────────────────────────────────────────────┐    │   │
│  │  │         Kubernetes Namespace (ai-agent)      │    │   │
│  │  │  ┌────────────────────────────────────────┐  │    │   │
│  │  │  │   AI Agent Pods (1-20 replicas)       │  │    │   │
│  │  │  │   - CPU: 500m-2000m                   │  │    │   │
│  │  │  │   - Memory: 512Mi-2Gi                 │  │    │   │
│  │  │  └────────────────────────────────────────┘  │    │   │
│  │  │  ┌────────────────────────────────────────┐  │    │   │
│  │  │  │   HPA (Min: 3, Max: 20)               │  │    │   │
│  │  │  │   - CPU: 70% trigger                  │  │    │   │
│  │  │  │   - Memory: 80% trigger               │  │    │   │
│  │  │  └────────────────────────────────────────┘  │    │   │
│  │  └──────────────────────────────────────────────┘    │   │
│  │  ┌──────────────────────────────────────────────┐    │   │
│  │  │         Karpenter Controller                 │    │   │
│  │  │   - EC2 Auto-scaling                        │    │   │
│  │  │   - Node Consolidation                      │    │   │
│  │  │   - Spot & On-Demand Instances              │    │   │
│  │  └──────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              AWS Services                            │   │
│  │  • ECR (Docker Registry)                             │   │
│  │  • EC2 (Node Instances)                              │   │
│  │  • IAM (Authentication & Authorization)              │   │
│  │  • CloudWatch (Monitoring & Logging)                 │   │
│  │  • Bedrock (Optional: AI/ML Models)                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Required Tools
- AWS CLI v2.x
- kubectl v1.28+
- Helm v3.12+
- Docker (latest)
- eksctl (latest)
- jq (optional, for JSON processing)

### AWS Permissions Required
- EKS cluster creation
- EC2 instance management
- ECR repository management
- IAM role creation
- VPC and networking configuration

### AWS Account Setup
```bash
# Configure AWS credentials
aws configure

# Verify credentials
aws sts get-caller-identity
```

## Step 1: Create EKS Cluster

```bash
# Set environment variables
export CLUSTER_NAME="ai-agent-cluster"
export AWS_REGION="us-east-1"
export NODE_TYPE="c5.xlarge"  # For AI workloads

# Create cluster
cd aws
chmod +x create-eks-cluster.sh
./create-eks-cluster.sh
```

This will:
- Create EKS cluster with 3 initial nodes
- Configure auto-scaling groups
- Enable CloudWatch logging
- Set up networking and security groups

## Step 2: Install Karpenter

Karpenter enables intelligent node auto-scaling based on pod resource requests.

```bash
# Install Karpenter
cd karpenter
chmod +x install.sh
./install.sh

# Verify installation
kubectl get pods -n karpenter

# Apply NodePool config
kubectl apply -f nodepool.yaml

# Verify NodePool
kubectl get nodepools -n karpenter
```

## Step 3: Build and Push Docker Image to ECR

```bash
# Build and push image
cd aws
chmod +x build-and-push-image.sh
./build-and-push-image.sh

# Verify image in ECR
aws ecr describe-images --repository-name ai-agent --region ${AWS_REGION}
```

## Step 4: Configure Secrets and ConfigMaps

Update the Kubernetes configuration files with your values:

```bash
# Edit the secrets file with real values
kubectl create secret generic ai-agent-secrets \
  --from-literal=OPENAI_API_KEY='your-key' \
  --from-literal=AWS_ACCESS_KEY_ID='your-key' \
  --from-literal=AWS_SECRET_ACCESS_KEY='your-key' \
  -n ai-agent

# Or use the provided template
kubectl apply -f kubernetes/secrets.yaml
```

## Step 5: Deploy Application

```bash
# Deploy all resources
cd aws
chmod +x deploy.sh
./deploy.sh

# Monitor deployment progress
kubectl rollout status deployment/ai-agent -n ai-agent -w

# Check pod status
kubectl get pods -n ai-agent
```

## Step 6: Verify Deployment

```bash
# Get LoadBalancer endpoint
kubectl get svc ai-agent -n ai-agent

# Test health endpoint
curl http://<LOAD_BALANCER_IP>/health

# View logs
kubectl logs -f deployment/ai-agent -n ai-agent

# Check HPA status
kubectl get hpa -n ai-agent
```

## Monitoring and Logging

### CloudWatch Logs
```bash
# View EKS cluster logs
aws logs describe-log-groups --region ${AWS_REGION}
aws logs tail /aws/eks/${CLUSTER_NAME}/cluster --follow
```

### Kubernetes Dashboard
```bash
# Start kubectl proxy
kubectl proxy

# Access dashboard at http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

### Check Pod Metrics
```bash
# View resource usage
kubectl top nodes
kubectl top pods -n ai-agent

# Describe specific pod
kubectl describe pod <POD_NAME> -n ai-agent
```

## Scaling

### Manual Scaling
```bash
# Scale deployment
kubectl scale deployment ai-agent -n ai-agent --replicas=5

# Scale node group (deprecated with Karpenter)
aws eks update-nodegroup-config \
  --cluster-name ${CLUSTER_NAME} \
  --nodegroup-name ${NODE_GROUP_NAME} \
  --scaling-config desiredSize=5
```

### Automatic Scaling with Karpenter
Karpenter automatically scales nodes based on:
- Pod resource requests
- Instance type availability
- Cost optimization
- Spot availability

Monitor with:
```bash
kubectl get nodes -L karpenter.sh/capacity-type,karpenter.sh/provisioner-name
kubectl describe nodes
```

## Testing the API

### Health Check
```bash
LOAD_BALANCER_IP=$(kubectl get svc ai-agent -n ai-agent -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

curl -X GET http://${LOAD_BALANCER_IP}/health
```

### Process Message
```bash
curl -X POST http://${LOAD_BALANCER_IP}/process \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the capital of France?",
    "context": {"language": "en"}
  }'
```

### Chat
```bash
curl -X POST http://${LOAD_BALANCER_IP}/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?"
  }'
```

## Updating the Application

### Update Container Image
```bash
# Build new image
cd aws
./build-and-push-image.sh  # with IMAGE_TAG=v1.1.0

# Update deployment
kubectl set image deployment/ai-agent \
  ai-agent=<ECR_REGISTRY>/ai-agent:v1.1.0 \
  -n ai-agent

# Monitor rollout
kubectl rollout status deployment/ai-agent -n ai-agent -w

# Rollback if needed
kubectl rollout undo deployment/ai-agent -n ai-agent
```

## Troubleshooting

### Pod Not Starting
```bash
# Check pod status
kubectl describe pod <POD_NAME> -n ai-agent

# View pod logs
kubectl logs <POD_NAME> -n ai-agent

# Check events
kubectl get events -n ai-agent --sort-by='.lastTimestamp'
```

### Insufficient Resources
```bash
# Check node resources
kubectl describe nodes

# Check resource requests vs available
kubectl top nodes
kubectl top pods -n ai-agent
```

### Network Issues
```bash
# Test connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
# Inside pod: wget -O- http://ai-agent-internal:8000/health

# Check service endpoints
kubectl get endpoints -n ai-agent
```

## Cost Optimization

### Spot Instances
```bash
# Enable spot instances in NodePool
# Edit karpenter/nodepool.yaml and modify:
# karpenter.sh/capacity-type: ["spot"] or ["on-demand", "spot"]

kubectl apply -f karpenter/nodepool.yaml
```

### Consolidation
Karpenter automatically consolidates underutilized nodes. Check settings in nodepool.yaml:
- `consolidateAfter: 30s`
- `expireAfter: 604800s`

## Cleanup

### Delete Application
```bash
kubectl delete namespace ai-agent
```

### Delete Cluster
```bash
# Delete EKS cluster
eksctl delete cluster --name ${CLUSTER_NAME} --region ${AWS_REGION}

# Delete ECR repository
aws ecr delete-repository \
  --repository-name ai-agent \
  --region ${AWS_REGION} \
  --force
```

## Security Best Practices

### Network Security
- Use SecurityGroups to restrict traffic
- Enable Network Policies in Kubernetes
- Use private subnets for nodes

### Access Control
- Use IAM roles for service accounts (IRSA)
- Implement RBAC policies
- Rotate credentials regularly

### Container Security
- Scan images for vulnerabilities
- Use minimal base images
- Run containers as non-root

### Monitoring
- Enable CloudTrail for audit logs
- Set up CloudWatch alarms
- Use VPC Flow Logs

## Advanced Configuration

### Custom Metrics for Auto-scaling
```yaml
# Add custom metrics to HPA
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-agent-custom
  namespace: ai-agent
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-agent
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
EOF
```

### Multi-Region Deployment
For high availability across regions:
1. Create clusters in multiple regions
2. Set up Route53 for DNS failover
3. Sync configurations across regions
4. Use Cross-region RDS for state

## Support and Resources

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Karpenter Documentation](https://karpenter.sh/)
- [AWS Best Practices](https://aws.amazon.com/architecture/well-architected/)

