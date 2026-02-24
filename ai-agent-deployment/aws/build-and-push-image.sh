#!/bin/bash

# Docker Image Build and Push to ECR
# This script builds the Docker image and pushes it to AWS ECR

set -e

# Variables
IMAGE_NAME="ai-agent"
IMAGE_TAG="${IMAGE_TAG:-latest}"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ECR_REPOSITORY="${ECR_REGISTRY}/${IMAGE_NAME}"

echo "=========================================="
echo "Building and Pushing Docker Image"
echo "Image: ${ECR_REPOSITORY}:${IMAGE_TAG}"
echo "=========================================="

# Create ECR repository if it doesn't exist
echo "Creating ECR repository..."
aws ecr create-repository \
  --repository-name ${IMAGE_NAME} \
  --region ${AWS_REGION} \
  --encryption-configuration encryptionType=AES \
  --tags Key=Application,Value=ai-agent Key=Environment,Value=production \
  2>/dev/null || echo "Repository already exists"

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Build Docker image
echo "Building Docker image..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

# Tag image for ECR
echo "Tagging image for ECR..."
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${ECR_REPOSITORY}:${IMAGE_TAG}
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${ECR_REPOSITORY}:latest

# Push to ECR
echo "Pushing image to ECR..."
docker push ${ECR_REPOSITORY}:${IMAGE_TAG}
docker push ${ECR_REPOSITORY}:latest

echo "=========================================="
echo "Docker Image Pushed Successfully!"
echo "Repository: ${ECR_REPOSITORY}"
echo "Tags: ${IMAGE_TAG}, latest"
echo "=========================================="
