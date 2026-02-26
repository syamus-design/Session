@echo off
REM Windows batch script to run everything locally without AWS

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo AI Agent - Local Development Setup
echo ==========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [X] Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    exit /b 1
)

echo [OK] Docker is installed
echo.

REM Check if Docker daemon is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [X] Docker daemon is not running
    echo Please start Docker Desktop
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Check docker-compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [X] docker-compose is not installed
    echo Please install Docker Desktop ^(includes docker-compose^)
    exit /b 1
)

echo [OK] docker-compose is available
echo.

REM Display options
echo Select how you want to run locally:
echo.
echo 1) Docker Compose ^(Fastest - 2 min^)
echo    - Single container, no Kubernetes
echo    - Good for quick testing
echo.
echo 2) Local Kubernetes ^(5-10 min^)
echo    - Requires Docker Desktop with Kubernetes enabled
echo    - Tests actual K8s manifests
echo.
echo 3) Minikube ^(Full testing - 10 min^)
echo    - Requires minikube installed
echo    - Most realistic local environment
echo.
echo 4) Destroy ^(Clean up deployments^)
echo    - Remove all containers, volumes, and resources
echo.

set /p option="Choose option (1-4): "

if "%option%"=="1" (
    echo.
    echo Starting Docker Compose...
    echo.
    docker-compose up
) else if "%option%"=="2" (
    echo.
    echo Checking Kubernetes...
    echo.
    
    kubectl cluster-info >nul 2>&1
    if errorlevel 1 (
        echo [X] Kubernetes is not running in Docker Desktop
        echo.
        echo To enable:
        echo 1. Open Docker Desktop
        echo 2. Preferences ^(or Settings^) ^-^> Kubernetes ^-^> Enable Kubernetes
        echo 3. Wait for it to start ^(check status bar^)
        echo 4. Run this script again
        exit /b 1
    )
    
    echo [OK] Kubernetes is running
    echo.
    
    REM Build Docker image
    echo Building Docker image...
    docker build -t ai-agent:latest .
    if errorlevel 1 (
        echo [X] Docker build failed. Check Dockerfile and try again.
        exit /b 1
    )
    echo [OK] Docker image built successfully
    echo.
    
    REM Create namespace
    echo Creating Kubernetes namespace...
    kubectl create namespace ai-agent 2>nul
    echo [OK] Namespace ready
    echo.
    
    REM Create ConfigMap and Secret
    echo Creating ConfigMap and Secret...
    kubectl create configmap ai-agent-config -n ai-agent --from-literal=app_name=ai-agent --from-literal=debug=false 2>nul
    kubectl create secret generic ai-agent-secrets -n ai-agent --from-literal=api_key=dummy-local-key 2>nul
    echo [OK] ConfigMap and Secret created
    echo.
    
    REM Apply manifests
    echo Deploying to local Kubernetes...
    kubectl apply -f kubernetes/namespace.yaml
    kubectl apply -f kubernetes/configmap.yaml
    kubectl apply -f kubernetes/deployment.yaml
    kubectl apply -f kubernetes/service.yaml
    kubectl apply -f kubernetes/hpa.yaml
    kubectl apply -f kubernetes/rbac.yaml
    kubectl apply -f kubernetes/pdb.yaml
    
    echo.
    echo ==========================================
    echo [OK] Manifests applied!
    echo ==========================================
    echo.
    
    echo Waiting for pods to become ready ^(this may take 30-60 seconds^)...
    echo.
    
    REM Check pod status multiple times
    setlocal enabledelayedexpansion
    set ATTEMPTS=0
    :wait_loop
    set ATTEMPTS=!ATTEMPTS!+1
    if !ATTEMPTS! gtr 60 (
        echo [X] Pods failed to start. Check logs:
        echo kubectl logs -f deployment/ai-agent -n ai-agent
        exit /b 1
    )
    
    for /f %%A in ('kubectl get pods -n ai-agent --no-headers 2^>nul ^| findstr Running ^| find /c /v ""') do set RUNNING=%%A
    if "!RUNNING!"=="3" (
        echo [OK] All 3 pods are running!
        goto pods_ready
    )
    
    timeout /t 1 /nobreak >nul
    goto wait_loop
    
    :pods_ready
    echo.
    echo ==========================================
    echo [OK] Deployment successful!
    echo [*] API available at: http://localhost:8000
    echo ==========================================
    echo.
    echo Starting port-forward in new window...
    echo (Keep this window open)
    echo.
    echo Press Ctrl+C to stop
    echo.
    
    kubectl port-forward -n ai-agent svc/ai-agent 8000:80
) else if "%option%"=="3" (
    echo.
    echo Checking Minikube...
    echo.
    
    minikube version >nul 2>&1
    if errorlevel 1 (
        echo [X] minikube is not installed
        echo.
        echo To install:
        echo   Windows: choco install minikube
        echo   Or download from: https://minikube.sigs.k8s.io/docs/start/
        exit /b 1
    )
    
    echo [OK] Minikube is installed
    echo.
    
    echo Starting Minikube cluster...
    minikube start --cpus=4 --memory=8192 --disk-size=20g
    
    echo Waiting for Minikube to be ready...
    timeout /t 5 /nobreak
    
    echo Building Docker image in Minikube...
    for /f "tokens=*" %%i in ('minikube docker-env ^| findstr /v "#"') do (
        @set "%%i"
    )
    
    docker build -t ai-agent:latest .
    
    echo Deploying to Minikube...
    kubectl create namespace ai-agent 2>nul
    kubectl create configmap ai-agent-config -n ai-agent --from-literal=app_name=ai-agent --from-literal=debug=false 2>nul
    kubectl create secret generic ai-agent-secrets -n ai-agent --from-literal=api_key=dummy-local-key 2>nul
    
    kubectl apply -f kubernetes/namespace.yaml
    kubectl apply -f kubernetes/configmap.yaml
    kubectl apply -f kubernetes/deployment.yaml
    kubectl apply -f kubernetes/service.yaml
    
    echo.
    echo ==========================================
    echo [OK] Minikube deployment complete!
    echo ==========================================
    echo.
    
    echo Waiting for pods to become ready...
    timeout /t 30 /nobreak
    
    echo.
    echo [*] API available at: http://localhost:8000
    echo Press Ctrl+C to stop
    echo.
    
    kubectl port-forward -n ai-agent svc/ai-agent 8000:80
) else if "%option%"=="4" (
    echo.
    echo ==========================================
    echo Destroy - Clean up all resources
    echo ==========================================
    echo.
    echo Select what to destroy:
    echo.
    echo 1) Docker Compose stack
    echo 2) Kubernetes namespace ^(ai-agent^)
    echo 3) Minikube cluster
    echo 4) All - Docker Compose + K8s + Minikube
    echo.
    set /p destroy_option="Choose what to destroy (1-4): "
    
    if "!destroy_option!"=="1" (
        echo.
        echo [*] Destroying Docker Compose stack...
        docker-compose down -v
        echo [OK] Docker Compose stack destroyed!
    ) else if "!destroy_option!"=="2" (
        echo.
        echo [*] Destroying Kubernetes namespace...
        kubectl delete namespace ai-agent --ignore-not-found=true
        echo [OK] Kubernetes namespace destroyed!
    ) else if "!destroy_option!"=="3" (
        echo.
        echo [*] Destroying Minikube cluster...
        minikube delete
        echo [OK] Minikube cluster destroyed!
    ) else if "!destroy_option!"=="4" (
        echo.
        echo [*] Destroying all resources...
        
        echo Removing Docker Compose stack...
        docker-compose down -v 2>nul
        echo [OK] Docker Compose stack removed
        
        echo Removing Kubernetes namespace...
        kubectl delete namespace ai-agent --ignore-not-found=true 2>nul
        echo [OK] Kubernetes namespace removed
        
        echo Removing Minikube cluster...
        minikube delete 2>nul
        echo [OK] Minikube cluster removed
        
        echo.
        echo ==========================================
        echo [OK] All resources destroyed!
        echo ==========================================
    ) else (
        echo Invalid option
        exit /b 1
    )
) else (
    echo Invalid option
    exit /b 1
)
