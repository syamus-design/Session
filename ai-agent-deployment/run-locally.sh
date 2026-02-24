#!/bin/bash

# Simple script to run everything locally without AWS

set -e

echo "=========================================="
echo "AI Agent - Local Development Setup"
echo "=========================================="
echo ""

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running"
    echo "Please start Docker Desktop"
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed"
    echo "Please install Docker Desktop (includes docker-compose)"
    exit 1
fi

echo "✅ docker-compose is available"
echo ""

# Display options
echo "Select how you want to run locally:"
echo ""
echo "1) Docker Compose (Fastest - 2 min)"
echo "   - Single container, no Kubernetes"
echo "   - Good for quick testing"
echo ""
echo "2) Local Kubernetes (5-10 min)"
echo "   - Requires Docker Desktop with Kubernetes enabled"
echo "   - Tests actual K8s manifests"
echo ""
echo "3) Minikube (Full testing - 10 min)"
echo "   - Requires minikube installed"
echo "   - Most realistic local environment"
echo ""

read -p "Choose option (1-3): " option

case $option in
    1)
        echo ""
        echo "Starting Docker Compose..."
        echo ""
        docker-compose up
        ;;
    2)
        echo ""
        echo "Checking Kubernetes..."
        
        if ! command -v kubectl &> /dev/null; then
            echo "❌ kubectl is not installed"
            echo "Please install kubectl or Docker Desktop with Kubernetes enabled"
            exit 1
        fi
        
        # Check if Docker Desktop Kubernetes is running
        if ! kubectl cluster-info &> /dev/null; then
            echo "❌ Kubernetes is not running in Docker Desktop"
            echo ""
            echo "To enable:"
            echo "1. Open Docker Desktop"
            echo "2. Preferences → Kubernetes → Enable Kubernetes"
            echo "3. Wait for it to start (check status bar)"
            echo "4. Run this script again"
            exit 1
        fi
        
        echo "✅ Kubernetes is running"
        echo ""
        
        echo "Deploying to local Kubernetes..."
        kubectl apply -f kubernetes/namespace.yaml
        kubectl apply -f kubernetes/configmap.yaml
        kubectl apply -f kubernetes/deployment.yaml
        kubectl apply -f kubernetes/service.yaml
        kubectl apply -f kubernetes/hpa.yaml
        kubectl apply -f kubernetes/rbac.yaml
        kubectl apply -f kubernetes/pdb.yaml
        
        echo ""
        echo "=========================================="
        echo "✅ Deployment complete!"
        echo "=========================================="
        echo ""
        echo "Waiting for pods to start (this may take 30 seconds)..."
        kubectl wait --for=condition=ready pod \
            -l app=ai-agent \
            -n ai-agent \
            --timeout=120s 2>/dev/null || true
        
        echo ""
        echo "Setting up port forward..."
        echo ""
        echo "🚀 API available at: http://localhost:8000"
        echo ""
        echo "Press Ctrl+C to stop"
        echo ""
        
        kubectl port-forward -n ai-agent svc/ai-agent 8000:80
        ;;
    3)
        echo ""
        echo "Checking Minikube..."
        
        if ! command -v minikube &> /dev/null; then
            echo "❌ minikube is not installed"
            echo ""
            echo "To install:"
            echo "  macOS:   brew install minikube"
            echo "  Windows: choco install minikube"
            echo "  Linux:   curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64"
            exit 1
        fi
        
        echo "✅ Minikube is installed"
        echo ""
        
        # Start minikube
        echo "Starting Minikube cluster..."
        minikube start --cpus=4 --memory=8192 --disk-size=20g 2>/dev/null || true
        
        echo "Waiting for Minikube to be ready..."
        sleep 5
        
        # Build image in minikube
        echo "Building Docker image in Minikube..."
        eval $(minikube docker-env)
        docker build -t ai-agent:latest .
        
        # Deploy
        echo "Deploying to Minikube..."
        kubectl apply -f kubernetes/namespace.yaml
        kubectl apply -f kubernetes/configmap.yaml
        
        # Update imagePullPolicy to Never for local image
        kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-agent
  namespace: ai-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-agent
  template:
    metadata:
      labels:
        app: ai-agent
    spec:
      containers:
      - name: ai-agent
        image: ai-agent:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 8000
        env:
        - name: PORT
          value: "8000"
        - name: LLM_PROVIDER
          value: "mock"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /readiness
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
EOF
        
        kubectl apply -f kubernetes/service.yaml
        
        echo ""
        echo "=========================================="
        echo "✅ Minikube deployment complete!"
        echo "=========================================="
        echo ""
        
        echo "Waiting for pods to start..."
        kubectl wait --for=condition=ready pod \
            -l app=ai-agent \
            -n ai-agent \
            --timeout=120s 2>/dev/null || true
        
        echo ""
        echo "Getting Minikube IP..."
        MINIKUBE_IP=$(minikube ip)
        echo "Minikube IP: $MINIKUBE_IP"
        echo ""
        
        echo "Setting up port forward..."
        echo "Press Ctrl+C to stop"
        echo ""
        
        kubectl port-forward -n ai-agent svc/ai-agent 8000:80
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac
