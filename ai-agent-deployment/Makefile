.PHONY: help build push deploy delete logs scale test clean install-deps

help:
	@echo "AI Agent Deployment Commands"
	@echo ""
	@echo "LOCAL DEVELOPMENT (No AWS needed):"
	@echo "  make docker-compose        Run with Docker Compose"
	@echo "  make k8s-local             Deploy to local Kubernetes"
	@echo "  make run-locally           Interactive setup script"
	@echo ""
	@echo "Setup:"
	@echo "  make install-deps          Install required tools"
	@echo ""
	@echo "Development:"
	@echo "  make build                 Build Docker image locally"
	@echo "  make run-local             Run app locally with Docker Compose"
	@echo "  make test                  Test API endpoints"
	@echo ""
	@echo "AWS/Kubernetes:"
	@echo "  make create-cluster        Create EKS cluster"
	@echo "  make install-karpenter     Install Karpenter"
	@echo "  make push                  Build and push image to ECR"
	@echo "  make deploy                Deploy to EKS"
	@echo "  make undeploy              Remove deployment from EKS"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs                  Stream application logs"
	@echo "  make status                Check deployment status"
	@echo "  make pods                  List all pods"
	@echo "  make metrics               Show resource usage"
	@echo ""
	@echo "Scaling:"
	@echo "  make scale-up              Scale to 10 replicas"
	@echo "  make scale-down            Scale to 3 replicas"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean                 Delete local Docker images"
	@echo "  make delete-cluster        Delete EKS cluster"

install-deps:
	@echo "Installing dependencies..."
	@command -v aws >/dev/null 2>&1 || { echo "AWS CLI is required"; exit 1; }
	@command -v kubectl >/dev/null 2>&1 || { echo "kubectl is required"; exit 1; }
	@command -v helm >/dev/null 2>&1 || { echo "helm is required"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "Docker is required"; exit 1; }
	@echo "All dependencies installed!"

build:
	@echo "Building Docker image..."
	docker build -t ai-agent:latest .

docker-compose:
	@echo "Starting with Docker Compose (no Kubernetes)..."
	docker-compose up

docker-compose-detach: build
	@echo "Starting Docker Compose in background..."
	docker-compose up -d
	@echo "✓ API available at http://localhost:8000"
	@echo "✓ Prometheus at http://localhost:9090"
	@echo "✓ Grafana at http://localhost:3000"
	@echo ""
	@echo "To view logs: docker-compose logs -f ai-agent"
	@echo "To stop: docker-compose down"

k8s-local:
	@echo "Deploying to local Kubernetes (Docker Desktop)..."
	@command -v kubectl >/dev/null 2>&1 || { echo "kubectl is required"; exit 1; }
	kubectl apply -f kubernetes/namespace.yaml
	kubectl apply -f kubernetes/configmap.yaml
	kubectl apply -f kubernetes/deployment.yaml
	kubectl apply -f kubernetes/service.yaml
	kubectl apply -f kubernetes/hpa.yaml
	kubectl apply -f kubernetes/rbac.yaml
	kubectl apply -f kubernetes/pdb.yaml
	@echo "✓ Deployment complete"
	@echo "Run: kubectl port-forward -n ai-agent svc/ai-agent 8000:80"

k8s-clean:
	@echo "Removing local Kubernetes deployment..."
	kubectl delete namespace ai-agent || true

run-locally:
	@echo "Running local setup wizard..."
	@bash run-locally.sh

run-local: build
	@echo "Testing API endpoints..."
	curl -s http://localhost:8000/health | python -m json.tool
	curl -s -X POST http://localhost:8000/process \
		-H "Content-Type: application/json" \
		-d '{"message":"Hello"}' | python -m json.tool

create-cluster:
	@echo "Creating EKS cluster..."
	cd aws && bash create-eks-cluster.sh

install-karpenter:
	@echo "Installing Karpenter..."
	cd karpenter && bash install.sh

push: build
	@echo "Pushing image to ECR..."
	cd aws && bash build-and-push-image.sh

deploy:
	@echo "Deploying to EKS..."
	cd aws && bash deploy.sh

undeploy:
	@echo "Removing deployment..."
	kubectl delete namespace ai-agent

logs:
	kubectl logs -f deployment/ai-agent -n ai-agent

status:
	kubectl get deployment,pods,svc -n ai-agent

pods:
	kubectl get pods -n ai-agent -o wide

metrics:
	@echo "Node metrics:"
	kubectl top nodes
	@echo ""
	@echo "Pod metrics:"
	kubectl top pods -n ai-agent

scale-up:
	@echo "Scaling to 10 replicas..."
	kubectl scale deployment ai-agent -n ai-agent --replicas=10

scale-down:
	@echo "Scaling to 3 replicas..."
	kubectl scale deployment ai-agent -n ai-agent --replicas=3

clean:
	@echo "Cleaning up local Docker images..."
	docker-compose down
	docker rmi ai-agent:latest || true

delete-cluster:
	@echo "Deleting EKS cluster..."
	eksctl delete cluster --name ai-agent-cluster --region us-east-1
