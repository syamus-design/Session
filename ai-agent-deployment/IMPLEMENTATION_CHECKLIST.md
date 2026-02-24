# Implementation Checklist

## Pre-Deployment

- [ ] AWS Account setup and credentials configured
- [ ] AWS CLI v2.x installed and configured
- [ ] kubectl v1.28+ installed
- [ ] Helm v3.12+ installed
- [ ] Docker installed
- [ ] eksctl installed
- [ ] Clone/copy this repository to your workspace

## Environment Setup

- [ ] Set AWS region and cluster name in environment variables
  ```bash
  export CLUSTER_NAME="ai-agent-cluster"
  export AWS_REGION="us-east-1"
  ```
- [ ] Copy `.env.example` to `.env` and update values
- [ ] Verify AWS credentials
  ```bash
  aws sts get-caller-identity
  ```

## Infrastructure Setup

- [ ] Create EKS cluster
  ```bash
  cd aws && bash create-eks-cluster.sh
  ```
- [ ] Verify cluster creation (5-10 minutes)
  ```bash
  kubectl cluster-info
  kubectl get nodes
  ```
- [ ] Install Karpenter for node auto-scaling
  ```bash
  cd karpenter && bash install.sh
  ```
- [ ] Verify Karpenter installation
  ```bash
  kubectl get pods -n karpenter
  kubectl get nodepools
  ```

## Application Preparation

- [ ] Update Kubernetes manifests with ECR registry URL
  - Edit `kubernetes/deployment.yaml`
  - Update `YOUR_ECR_REGISTRY` with your ECR endpoint
- [ ] Update secrets with real API keys
  - Edit `kubernetes/secrets.yaml`
  - Add OPENAI_API_KEY or other credentials
  - **Never commit secrets!**
- [ ] Update ConfigMap if needed
  - Edit `kubernetes/configmap.yaml`
  - Adjust log levels, environment, etc.

## Build and Push

- [ ] Build Docker image locally and test
  ```bash
  docker build -t ai-agent:latest .
  docker run -p 8000:8000 ai-agent:latest
  ```
- [ ] Test local API
  ```bash
  curl http://localhost:8000/health
  ```
- [ ] Build and push to ECR
  ```bash
  cd aws && bash build-and-push-image.sh
  ```
- [ ] Verify image in ECR
  ```bash
  aws ecr describe-images --repository-name ai-agent
  ```

## Kubernetes Deployment

- [ ] Create namespace
  ```bash
  kubectl apply -f kubernetes/namespace.yaml
  ```
- [ ] Deploy RBAC
  ```bash
  kubectl apply -f kubernetes/rbac.yaml
  ```
- [ ] Deploy ConfigMap
  ```bash
  kubectl apply -f kubernetes/configmap.yaml
  ```
- [ ] Deploy Secrets
  ```bash
  kubectl apply -f kubernetes/secrets.yaml
  ```
- [ ] Deploy application
  ```bash
  kubectl apply -f kubernetes/deployment.yaml
  ```
- [ ] Deploy Service
  ```bash
  kubectl apply -f kubernetes/service.yaml
  ```
- [ ] Deploy HPA
  ```bash
  kubectl apply -f kubernetes/hpa.yaml
  ```
- [ ] Deploy PDB
  ```bash
  kubectl apply -f kubernetes/pdb.yaml
  ```

## Verification

- [ ] Check all pods are running
  ```bash
  kubectl get pods -n ai-agent
  ```
- [ ] Check deployment status
  ```bash
  kubectl get deployment -n ai-agent
  ```
- [ ] Check services
  ```bash
  kubectl get svc -n ai-agent
  ```
- [ ] Check HPA status
  ```bash
  kubectl get hpa -n ai-agent
  ```
- [ ] Wait for LoadBalancer to get external IP (may take 1-2 minutes)
  ```bash
  kubectl get svc ai-agent -n ai-agent -w
  ```

## Testing

- [ ] Get LoadBalancer IP/hostname
  ```bash
  kubectl get svc ai-agent -n ai-agent
  ```
- [ ] Test health endpoint
  ```bash
  curl http://<LOAD_BALANCER_IP>/health
  ```
- [ ] Test readiness endpoint
  ```bash
  curl http://<LOAD_BALANCER_IP>/readiness
  ```
- [ ] Test process endpoint
  ```bash
  curl -X POST http://<LOAD_BALANCER_IP>/process \
    -H "Content-Type: application/json" \
    -d '{"message":"Hello"}'
  ```
- [ ] Test chat endpoint
  ```bash
  curl -X POST http://<LOAD_BALANCER_IP>/chat \
    -H "Content-Type: application/json" \
    -d '{"message":"How are you?"}'
  ```
- [ ] View application logs
  ```bash
  kubectl logs -f deployment/ai-agent -n ai-agent
  ```

## Monitoring Setup (Optional)

- [ ] Deploy Prometheus for metrics
  ```bash
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
  ```
- [ ] Deploy Grafana for visualization
  ```bash
  kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
  ```
- [ ] Access Grafana at http://localhost:3000 (admin/prom-operator)

## Load Testing (Optional)

- [ ] Install load testing tool
  ```bash
  # Using Apache Bench (ab)
  ab -n 1000 -c 10 http://<LOAD_BALANCER_IP>/health
  
  # Or using hey
  go install github.com/rakyll/hey@latest
  hey -n 1000 -c 10 http://<LOAD_BALANCER_IP>/health
  ```
- [ ] Monitor HPA scaling
  ```bash
  kubectl get hpa -n ai-agent -w
  kubectl get pods -n ai-agent -w
  ```
- [ ] Monitor node scaling
  ```bash
  kubectl get nodes -w
  ```

## Post-Deployment

- [ ] Document LoadBalancer IP/hostname for API access
- [ ] Set up CI/CD pipeline (.github/workflows/deploy.yml included)
- [ ] Configure CloudWatch logging
  ```bash
  # View logs
  aws logs tail /aws/eks/ai-agent-cluster/cluster --follow
  ```
- [ ] Set up alerts (CloudWatch Alarms)
- [ ] Document API endpoints for users
- [ ] Backup configuration files

## Scaling Tests

- [ ] [ ] Generate load and observe pod scaling
  ```bash
  # Terminal 1: Watch HPA
  kubectl get hpa -n ai-agent -w
  
  # Terminal 2: Watch pods
  kubectl get pods -n ai-agent -w
  
  # Terminal 3: Generate load
  ab -t 300 -c 50 http://<LOAD_BALANCER_IP>/health
  ```
- [ ] Observe node scaling with Karpenter
  ```bash
  kubectl get nodes -w
  ```
- [ ] Scale down and verify consolidation

## Cost Optimization

- [ ] Review and optimize instance types in Karpenter
- [ ] Enable Spot instances for cost savings
- [ ] Review and adjust HPA min/max replicas
- [ ] Configure node consolidation settings
- [ ] Set up AWS Budget alerts

## Security Hardening

- [ ] Scan Docker images for vulnerabilities
  ```bash
  trivy image <ECR_REGISTRY>/ai-agent:latest
  ```
- [ ] Enable IMDS v2 for EC2 instances
- [ ] Implement Network Policies
- [ ] Set up pod security policies
- [ ] Enable audit logging
- [ ] Rotate credentials regularly
- [ ] Review IAM roles and policies

## Backup and Disaster Recovery

- [ ] Document backup procedures
- [ ] Set up automated backups for stateful data
- [ ] Test disaster recovery procedures
- [ ] Document recovery time objectives (RTO)
- [ ] Document recovery point objectives (RPO)

## Cleanup (When Done)

- [ ] Delete application namespace
  ```bash
  kubectl delete namespace ai-agent
  ```
- [ ] Delete EKS cluster
  ```bash
  eksctl delete cluster --name ${CLUSTER_NAME} --region ${AWS_REGION}
  ```
- [ ] Delete ECR repository
  ```bash
  aws ecr delete-repository --repository-name ai-agent --force
  ```
- [ ] Remove temporary files and credentials

## Additional Setup (Recommended)

- [ ] Set up GitHub integration for CI/CD
  - Add AWS credentials as GitHub Secrets
  - Configure branch protection rules
- [ ] Set up logging aggregation
  - CloudWatch Logs Insights
  - ELK Stack (optional)
- [ ] Set up distributed tracing
  - AWS X-Ray
  - Jaeger (optional)
- [ ] Implement API rate limiting
- [ ] Set up WAF/DDoS protection
- [ ] Configure VPN/bastion access

## Troubleshooting Checklist

- [ ] Verify AWS credentials and permissions
- [ ] Check cluster connectivity
  ```bash
  kubectl cluster-info
  ```
- [ ] Verify image in ECR
  ```bash
  aws ecr describe-images --repository-name ai-agent
  ```
- [ ] Check pod events
  ```bash
  kubectl describe pod <POD_NAME> -n ai-agent
  ```
- [ ] Check pod logs
  ```bash
  kubectl logs <POD_NAME> -n ai-agent
  ```
- [ ] Verify service endpoints
  ```bash
  kubectl get endpoints -n ai-agent
  ```
- [ ] Check security groups
  ```bash
  aws ec2 describe-security-groups --filters "Name=tag:karpenter.sh/discovery,Values=true"
  ```

---

**Total Estimated Time**: 30-45 minutes for first-time setup
**Monthly Cost Estimate**: $150-400 (depending on usage and instance types)
