# Karpenter Installation Script
# This script installs Karpenter on an EKS cluster

#!/bin/bash

set -e

# Variables
KARPENTER_VERSION="v0.32.0"
KARPENTER_NAMESPACE="karpenter"
CLUSTER_NAME="${CLUSTER_NAME:-ai-agent-cluster}"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Installing Karpenter v${KARPENTER_VERSION}"
echo "Cluster: ${CLUSTER_NAME}"
echo "Region: ${AWS_REGION}"

# Create namespace
kubectl create namespace ${KARPENTER_NAMESPACE} || true

# Add Helm repository
helm repo add karpenter https://charts.karpenter.sh
helm repo update

# Create IAM role and policy for Karpenter controller
eksctl create iamserviceaccount \
  --cluster=${CLUSTER_NAME} \
  --namespace=${KARPENTER_NAMESPACE} \
  --name=karpenter \
  --attach-policy-arn=arn:aws:iam::${AWS_ACCOUNT_ID}:policy/KarpenterControllerPolicy \
  --override-existing-serviceaccounts \
  --region ${AWS_REGION} \
  --approve || true

# Install Karpenter using Helm
helm install karpenter karpenter/karpenter \
  --namespace ${KARPENTER_NAMESPACE} \
  --create-namespace \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=arn:aws:iam::${AWS_ACCOUNT_ID}:role/eksctl-${CLUSTER_NAME}-addon-iamserviceaccount-karpenter-karpenter-Role1 \
  --set settings.clusterName=${CLUSTER_NAME} \
  --set settings.aws.region=${AWS_REGION} \
  --version ${KARPENTER_VERSION}

echo "Karpenter installation complete!"
