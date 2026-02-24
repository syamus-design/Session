#!/bin/bash

# EKS Cluster Creation and Setup Script
# This script creates an EKS cluster with proper configuration for AI Agent deployment

set -e

# Variables
CLUSTER_NAME="${CLUSTER_NAME:-ai-agent-cluster}"
AWS_REGION="${AWS_REGION:-us-east-1}"
NODE_GROUP_NAME="${NODE_GROUP_NAME:-ai-agent-nodes}"
NODE_TYPE="${NODE_TYPE:-t3.xlarge}"
MIN_NODES="${MIN_NODES:-3}"
MAX_NODES="${MAX_NODES:-10}"
DESIRED_NODES="${DESIRED_NODES:-3}"

echo "=========================================="
echo "Creating EKS Cluster: ${CLUSTER_NAME}"
echo "Region: ${AWS_REGION}"
echo "=========================================="

# Check Prerequisites
echo "Checking prerequisites..."
command -v aws >/dev/null 2>&1 || { echo "AWS CLI is required but not installed."; exit 1; }
command -v eksctl >/dev/null 2>&1 || { echo "eksctl is required but not installed."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "kubectl is required but not installed."; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "helm is required but not installed."; exit 1; }

# Create EKS Cluster
echo "Creating EKS cluster..."
eksctl create cluster \
  --name ${CLUSTER_NAME} \
  --region ${AWS_REGION} \
  --version 1.28 \
  --nodegroup-name ${NODE_GROUP_NAME} \
  --node-type ${NODE_TYPE} \
  --nodes ${DESIRED_NODES} \
  --nodes-min ${MIN_NODES} \
  --nodes-max ${MAX_NODES} \
  --managed \
  --enable-ssm \
  --tags Environment=production,Application=ai-agent \
  --instance-selector-vcpus 2 \
  --instance-selector-memory 4 \
  --spot=false

# Update kubeconfig
echo "Updating kubeconfig..."
aws eks update-kubeconfig --name ${CLUSTER_NAME} --region ${AWS_REGION}

# Verify cluster
echo "Verifying cluster..."
kubectl cluster-info
kubectl get nodes

echo "=========================================="
echo "EKS Cluster Created Successfully!"
echo "Cluster Name: ${CLUSTER_NAME}"
echo "Region: ${AWS_REGION}"
echo "=========================================="
