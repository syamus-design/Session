#!/bin/bash

# Complete Deployment Script
# Deploys application to EKS with all required configurations

set -e

CLUSTER_NAME="${CLUSTER_NAME:-ai-agent-cluster}"
AWS_REGION="${AWS_REGION:-us-east-1}"
NAMESPACE="ai-agent"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "=========================================="
echo "Deploying AI Agent to EKS"
echo "=========================================="

# Update kubeconfig
echo "Updating kubeconfig..."
aws eks update-kubeconfig --name ${CLUSTER_NAME} --region ${AWS_REGION}

# Verify cluster access
echo "Verifying cluster access..."
kubectl cluster-info

# Create namespace
echo "Creating namespace..."
kubectl apply -f kubernetes/namespace.yaml

# Deploy RBAC
echo "Deploying RBAC..."
kubectl apply -f kubernetes/rbac.yaml

# Deploy ConfigMap
echo "Deploying ConfigMap..."
kubectl apply -f kubernetes/configmap.yaml

# Deploy Secrets (Update with real values first!)
echo "Deploying Secrets..."
kubectl apply -f kubernetes/secrets.yaml

# Update deployment image
echo "Updating deployment configuration..."
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
sed -i "s|YOUR_ECR_REGISTRY|${ECR_REGISTRY}|g" kubernetes/deployment.yaml

# Deploy application
echo "Deploying AI Agent application..."
kubectl apply -f kubernetes/deployment.yaml

# Deploy service
echo "Deploying service..."
kubectl apply -f kubernetes/service.yaml

# Deploy HPA
echo "Deploying Horizontal Pod Autoscaler..."
kubectl apply -f kubernetes/hpa.yaml

# Deploy PDB
echo "Deploying Pod Disruption Budget..."
kubectl apply -f kubernetes/pdb.yaml

# Wait for deployment
echo "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s \
  deployment/ai-agent -n ${NAMESPACE} 2>/dev/null || true

# Check deployment status
echo "Checking deployment status..."
kubectl get deployment,pods,svc -n ${NAMESPACE}

# Get LoadBalancer endpoint
echo "=========================================="
echo "Deployment Complete!"
echo "Checking LoadBalancer endpoint..."
sleep 10
kubectl get svc ai-agent -n ${NAMESPACE} -w

echo "=========================================="
echo "AI Agent is now deployed!"
echo "Namespace: ${NAMESPACE}"
echo "=========================================="
