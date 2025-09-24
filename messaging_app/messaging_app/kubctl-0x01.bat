@echo off
REM kubctl-0x01.bat: Kubernetes Application Scaling Script (Windows Batch)
REM This script demonstrates how to scale applications in Kubernetes
REM Author: ALX Backend Python Course
REM Purpose: Scale Django messaging app, perform load testing, and monitor resources

setlocal enabledelayedexpansion

REM Configuration
set DEPLOYMENT_NAME=django-messaging-app
set SERVICE_NAME=django-messaging-service
set NAMESPACE=default
set TARGET_REPLICAS=3
set LOAD_TEST_DURATION=30s
set LOAD_TEST_CONNECTIONS=10
set LOAD_TEST_THREADS=2

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :main
if /i "%~1"=="-h" goto :show_usage
if /i "%~1"=="--help" goto :show_usage
if /i "%~1"=="-r" (
    set TARGET_REPLICAS=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--replicas" (
    set TARGET_REPLICAS=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="-d" (
    set LOAD_TEST_DURATION=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--duration" (
    set LOAD_TEST_DURATION=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="-c" (
    set LOAD_TEST_CONNECTIONS=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--connections" (
    set LOAD_TEST_CONNECTIONS=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--skip-load-test" (
    set SKIP_LOAD_TEST=true
    shift
    goto :parse_args
)
if /i "%~1"=="--skip-monitoring" (
    set SKIP_MONITORING=true
    shift
    goto :parse_args
)
echo [ERROR] Unknown option: %~1
goto :show_usage

:show_usage
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   -h, --help              Show this help message
echo   -r, --replicas NUM      Set target number of replicas (default: 3)
echo   -d, --duration TIME     Set load test duration (default: 30s)
echo   -c, --connections NUM   Set load test connections (default: 10)
echo   --skip-load-test        Skip the load testing phase
echo   --skip-monitoring       Skip the resource monitoring phase
echo.
echo Examples:
echo   %~nx0                      # Scale to 3 replicas and run full test
echo   %~nx0 -r 5                 # Scale to 5 replicas
echo   %~nx0 -d 60s -c 20         # Run 60s load test with 20 connections
echo   %~nx0 --skip-load-test     # Scale and monitor without load testing
exit /b 0

:print_status
echo [INFO] %~1
exit /b 0

:print_success
echo [SUCCESS] %~1
exit /b 0

:print_warning
echo [WARNING] %~1
exit /b 0

:print_error
echo [ERROR] %~1
exit /b 0

:check_prerequisites
call :print_status "Checking prerequisites..."

REM Check kubectl
kubectl version --client --short >nul 2>&1
if errorlevel 1 (
    call :print_error "kubectl is not installed or not in PATH"
    call :print_status "Please install kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/"
    exit /b 1
)

REM Check if Kubernetes cluster is accessible
kubectl cluster-info >nul 2>&1
if errorlevel 1 (
    call :print_error "Kubernetes cluster is not accessible. Make sure minikube is running."
    call :print_status "Try running: minikube start"
    exit /b 1
)

REM Check wrk for load testing
wrk --version >nul 2>&1
if errorlevel 1 (
    call :print_warning "wrk is not installed. Load testing will be skipped."
    call :print_status "To install wrk on Windows, download from: https://github.com/wg/wrk/releases"
    set WRK_AVAILABLE=false
) else (
    set WRK_AVAILABLE=true
)

exit /b 0

:check_deployment
call :print_status "Checking if deployment '%DEPLOYMENT_NAME%' exists..."

kubectl get deployment %DEPLOYMENT_NAME% -n %NAMESPACE% >nul 2>&1
if errorlevel 1 (
    call :print_error "Deployment '%DEPLOYMENT_NAME%' not found in namespace '%NAMESPACE%'"
    call :print_status "Make sure to apply the deployment.yaml first:"
    call :print_status "kubectl apply -f deployment.yaml"
    exit /b 1
)

call :print_success "Deployment '%DEPLOYMENT_NAME%' found"
exit /b 0

:get_current_replicas
for /f %%i in ('kubectl get deployment %DEPLOYMENT_NAME% -n %NAMESPACE% -o jsonpath^="{.spec.replicas}" 2^>nul') do set CURRENT_REPLICAS=%%i
exit /b 0

:scale_deployment
call :get_current_replicas
call :print_status "Current replicas: %CURRENT_REPLICAS%"

if "%CURRENT_REPLICAS%"=="%TARGET_REPLICAS%" (
    call :print_warning "Deployment is already scaled to %TARGET_REPLICAS% replicas"
    exit /b 0
)

call :print_status "Scaling deployment '%DEPLOYMENT_NAME%' to %TARGET_REPLICAS% replicas..."
kubectl scale deployment %DEPLOYMENT_NAME% --replicas=%TARGET_REPLICAS% -n %NAMESPACE%

call :print_status "Waiting for deployment to be ready..."
kubectl rollout status deployment/%DEPLOYMENT_NAME% -n %NAMESPACE% --timeout=300s

call :print_success "Successfully scaled deployment to %TARGET_REPLICAS% replicas"
exit /b 0

:verify_pods
call :print_status "Verifying that multiple pods are running..."

echo.
echo Current pods:
kubectl get pods -l app=%DEPLOYMENT_NAME% -n %NAMESPACE% -o wide

REM Count running pods
for /f %%i in ('kubectl get pods -l app^=%DEPLOYMENT_NAME% -n %NAMESPACE% --field-selector^=status.phase^=Running --no-headers 2^>nul ^| find /c /v ""') do set RUNNING_PODS=%%i

if %RUNNING_PODS% geq %TARGET_REPLICAS% (
    call :print_success "%RUNNING_PODS% pods are running (target: %TARGET_REPLICAS%)"
) else (
    call :print_warning "Only %RUNNING_PODS% pods are running (target: %TARGET_REPLICAS%)"
    call :print_status "Waiting a bit more for pods to start..."
    timeout /t 10 /nobreak >nul
    kubectl get pods -l app=%DEPLOYMENT_NAME% -n %NAMESPACE%
)
exit /b 0

:get_service_url
REM Check if service exists
kubectl get service %SERVICE_NAME% -n %NAMESPACE% >nul 2>&1
if errorlevel 1 (
    call :print_error "Service '%SERVICE_NAME%' not found"
    exit /b 1
)

REM For minikube, try to get service URL
for /f "delims=" %%i in ('minikube service %SERVICE_NAME% --url -n %NAMESPACE% 2^>nul') do (
    set SERVICE_URL=%%i
    exit /b 0
)

REM Fallback to port-forward
call :print_status "Using port-forward to access the service..."
start /b kubectl port-forward service/%SERVICE_NAME% 8080:80 -n %NAMESPACE%
timeout /t 3 /nobreak >nul
set SERVICE_URL=http://localhost:8080
exit /b 0

:perform_load_test
if "%WRK_AVAILABLE%"=="false" (
    call :print_warning "Skipping load test - wrk not installed"
    exit /b 0
)

call :print_status "Getting service URL for load testing..."
call :get_service_url
if errorlevel 1 exit /b 1

call :print_status "Service URL: %SERVICE_URL%"
call :print_status "Performing load test for %LOAD_TEST_DURATION% with %LOAD_TEST_CONNECTIONS% connections..."

echo.
echo Load Test Results:
wrk -t%LOAD_TEST_THREADS% -c%LOAD_TEST_CONNECTIONS% -d%LOAD_TEST_DURATION% --timeout=10s "%SERVICE_URL%/admin/"

REM Cleanup port-forward processes
taskkill /f /im kubectl.exe >nul 2>&1

call :print_success "Load test completed"
exit /b 0

:monitor_resources
call :print_status "Monitoring resource usage..."

REM Check if metrics-server is available
kubectl top nodes >nul 2>&1
if errorlevel 1 (
    call :print_warning "Metrics server not available. Resource monitoring will be limited."
    call :print_status "To enable metrics in minikube: minikube addons enable metrics-server"
    echo.
    echo Pod resource requests/limits:
    kubectl describe deployment %DEPLOYMENT_NAME% -n %NAMESPACE% | findstr /i "Limits Requests"
    exit /b 0
)

echo.
echo Node resource usage:
kubectl top nodes

echo.
echo Pod resource usage:
kubectl top pods -l app=%DEPLOYMENT_NAME% -n %NAMESPACE%

echo.
echo Pod resource requests and limits:
kubectl describe pods -l app=%DEPLOYMENT_NAME% -n %NAMESPACE% | findstr /i "Limits Requests"
exit /b 0

:show_deployment_status
echo.
echo Deployment Status:
kubectl get deployment %DEPLOYMENT_NAME% -n %NAMESPACE% -o wide

echo.
echo ReplicaSet Status:
kubectl get replicaset -l app=%DEPLOYMENT_NAME% -n %NAMESPACE%

echo.
echo Service Status:
kubectl get service %SERVICE_NAME% -n %NAMESPACE% -o wide
exit /b 0

:main
echo === Kubernetes Application Scaling Script ===
echo Target deployment: %DEPLOYMENT_NAME%
echo Target replicas: %TARGET_REPLICAS%
echo Namespace: %NAMESPACE%
echo.

REM Step 1: Check prerequisites
call :check_prerequisites
if errorlevel 1 exit /b 1

REM Step 2: Check if deployment exists
call :check_deployment
if errorlevel 1 exit /b 1

REM Step 3: Scale the deployment
call :scale_deployment
if errorlevel 1 exit /b 1

REM Step 4: Verify pods are running
call :verify_pods

REM Step 5: Show deployment status
call :show_deployment_status

REM Step 6: Perform load testing (if wrk is available and not skipped)
if not "%SKIP_LOAD_TEST%"=="true" (
    if "%WRK_AVAILABLE%"=="true" (
        call :perform_load_test
    )
) else (
    call :print_status "Skipping load test as requested"
)

REM Step 7: Monitor resource usage (if not skipped)
if not "%SKIP_MONITORING%"=="true" (
    call :monitor_resources
) else (
    call :print_status "Skipping resource monitoring as requested"
)

echo.
call :print_success "Kubernetes scaling demonstration completed!"
echo Useful commands for further monitoring:
echo   kubectl get pods -l app=%DEPLOYMENT_NAME% -w
echo   kubectl logs -l app=%DEPLOYMENT_NAME% --tail=50
echo   kubectl describe deployment %DEPLOYMENT_NAME%
echo   kubectl top pods -l app=%DEPLOYMENT_NAME%

exit /b 0