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

set /p option="Choose option (1-3): "

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
    echo [OK] Deployment complete!
    echo ==========================================
    echo.
    
    echo Waiting for pods to start...
    timeout /t 30 /nobreak
    
    echo.
    echo Setting up port forward...
    echo.
    echo [*] API available at: http://localhost:8000
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
    kubectl apply -f kubernetes/namespace.yaml
    kubectl apply -f kubernetes/configmap.yaml
    kubectl apply -f kubernetes/service.yaml
    
    echo.
    echo ==========================================
    echo [OK] Minikube deployment complete!
    echo ==========================================
    echo.
    
    echo Waiting for pods to start...
    timeout /t 30 /nobreak
    
    echo.
    echo Setting up port forward...
    echo.
    echo [*] API available at: http://localhost:8000
    echo Press Ctrl+C to stop
    echo.
    
    kubectl port-forward -n ai-agent svc/ai-agent 8000:80
) else (
    echo Invalid option
    exit /b 1
)
