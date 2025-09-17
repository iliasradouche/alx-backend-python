@echo off
REM kurbeScript.bat - Kubernetes Local Cluster Management Script for Windows
REM This script sets up and manages a local Kubernetes cluster using minikube

setlocal enabledelayedexpansion

REM Colors for output (Windows compatible)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

echo ======================================
echo     Kubernetes Local Setup Script    
echo ======================================
echo.

REM Function to check if a command exists
echo %BLUE%[INFO]%NC% Checking minikube installation...
minikube version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%[ERROR]%NC% minikube is not installed!
    echo %BLUE%[INFO]%NC% Please install minikube from: https://minikube.sigs.k8s.io/docs/start/
    echo %BLUE%[INFO]%NC% For Windows: Download from https://github.com/kubernetes/minikube/releases/latest
    echo %BLUE%[INFO]%NC% Or use chocolatey: choco install minikube
    echo %BLUE%[INFO]%NC% Or use winget: winget install Kubernetes.minikube
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('minikube version --short 2^>nul') do set MINIKUBE_VERSION=%%i
    echo %GREEN%[SUCCESS]%NC% minikube is installed (version: !MINIKUBE_VERSION!)
)

echo.
echo %BLUE%[INFO]%NC% Checking kubectl installation...
kubectl version --client >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%[WARNING]%NC% kubectl is not installed separately!
    echo %BLUE%[INFO]%NC% kubectl will be available through minikube kubectl
) else (
    for /f "tokens=3" %%i in ('kubectl version --client --short 2^>nul') do set KUBECTL_VERSION=%%i
    echo %GREEN%[SUCCESS]%NC% kubectl is installed (version: !KUBECTL_VERSION!)
)

echo.
echo %BLUE%[INFO]%NC% Starting Kubernetes cluster with minikube...

REM Check if minikube is already running
minikube status >nul 2>&1
if %errorlevel% equ 0 (
    echo %YELLOW%[WARNING]%NC% minikube cluster is already running
    minikube status
) else (
    echo %BLUE%[INFO]%NC% Starting new minikube cluster...
    minikube start --driver=docker --cpus=2 --memory=2048mb --disk-size=10gb
    if %errorlevel% neq 0 (
        echo %RED%[ERROR]%NC% Failed to start Kubernetes cluster
        echo %BLUE%[INFO]%NC% Trying with different driver...
        minikube start --driver=hyperv --cpus=2 --memory=2048mb --disk-size=10gb
        if %errorlevel% neq 0 (
            echo %RED%[ERROR]%NC% Failed to start with hyperv driver, trying virtualbox...
            minikube start --driver=virtualbox --cpus=2 --memory=2048mb --disk-size=10gb
            if %errorlevel% neq 0 (
                echo %RED%[ERROR]%NC% Failed to start Kubernetes cluster with any driver
                pause
                exit /b 1
            )
        )
    )
    echo %GREEN%[SUCCESS]%NC% Kubernetes cluster started successfully!
)

echo.
echo %BLUE%[INFO]%NC% Verifying cluster status with kubectl cluster-info...

REM Wait a moment for cluster to be fully ready
timeout /t 5 /nobreak >nul

REM Use minikube kubectl if regular kubectl is not available
kubectl cluster-info >nul 2>&1
if %errorlevel% neq 0 (
    echo %BLUE%[INFO]%NC% Using minikube kubectl...
    minikube kubectl -- cluster-info >nul 2>&1
    if %errorlevel% neq 0 (
        echo %RED%[ERROR]%NC% Cluster verification failed!
        echo %BLUE%[INFO]%NC% Trying to diagnose the issue...
        minikube status
        pause
        exit /b 1
    ) else (
        echo %GREEN%[SUCCESS]%NC% Cluster is running and accessible!
        echo.
        echo %BLUE%[INFO]%NC% Cluster Information:
        minikube kubectl -- cluster-info
        echo.
        echo %BLUE%[INFO]%NC% Node Status:
        minikube kubectl -- get nodes
    )
) else (
    echo %GREEN%[SUCCESS]%NC% Cluster is running and accessible!
    echo.
    echo %BLUE%[INFO]%NC% Cluster Information:
    kubectl cluster-info
    echo.
    echo %BLUE%[INFO]%NC% Node Status:
    kubectl get nodes
)

echo.
echo %BLUE%[INFO]%NC% Retrieving available pods...
echo.
echo %BLUE%[INFO]%NC% Pods in all namespaces:

REM Try kubectl first, then minikube kubectl
kubectl get pods --all-namespaces >nul 2>&1
if %errorlevel% neq 0 (
    minikube kubectl -- get pods --all-namespaces
    echo.
    echo %BLUE%[INFO]%NC% Pods in default namespace:
    minikube kubectl -- get pods
    
    REM Count pods
    for /f %%i in ('minikube kubectl -- get pods --all-namespaces --no-headers ^| find /c /v ""') do set POD_COUNT=%%i
) else (
    kubectl get pods --all-namespaces
    echo.
    echo %BLUE%[INFO]%NC% Pods in default namespace:
    kubectl get pods
    
    REM Count pods
    for /f %%i in ('kubectl get pods --all-namespaces --no-headers ^| find /c /v ""') do set POD_COUNT=%%i
)

echo %GREEN%[SUCCESS]%NC% Total pods found: !POD_COUNT!

echo.
echo %BLUE%[INFO]%NC% Kubernetes Dashboard Information:
echo %BLUE%[INFO]%NC% To access the Kubernetes dashboard, run: minikube dashboard
echo %BLUE%[INFO]%NC% To get the dashboard URL, run: minikube dashboard --url

echo.
echo %BLUE%[INFO]%NC% Useful commands for managing your cluster:
echo   minikube status          - Check cluster status
echo   minikube stop            - Stop the cluster
echo   minikube delete          - Delete the cluster
echo   minikube dashboard       - Open Kubernetes dashboard
echo   kubectl get nodes        - List cluster nodes
echo   kubectl get pods         - List pods in default namespace
echo   kubectl get services     - List services
echo   kubectl get deployments - List deployments
echo   minikube kubectl -- [command] - Use kubectl through minikube

echo.
echo %GREEN%[SUCCESS]%NC% Kubernetes cluster setup completed successfully!
echo ======================================

pause