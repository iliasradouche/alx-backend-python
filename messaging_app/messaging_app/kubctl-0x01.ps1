# kubctl-0x01.ps1: Kubernetes Application Scaling Script (PowerShell)
# This script demonstrates how to scale applications in Kubernetes
# Author: ALX Backend Python Course
# Purpose: Scale Django messaging app, perform load testing, and monitor resources

param(
    [int]$Replicas = 3,
    [string]$Duration = "30s",
    [int]$Connections = 10,
    [switch]$SkipLoadTest,
    [switch]$SkipMonitoring,
    [switch]$Help
)

# Configuration
$DEPLOYMENT_NAME = "django-messaging-app"
$SERVICE_NAME = "django-messaging-service"
$NAMESPACE = "default"
$LOAD_TEST_THREADS = 2

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to show usage information
function Show-Usage {
    Write-Host "Usage: .\kubctl-0x01.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Replicas NUM           Set target number of replicas (default: 3)"
    Write-Host "  -Duration TIME          Set load test duration (default: 30s)"
    Write-Host "  -Connections NUM        Set load test connections (default: 10)"
    Write-Host "  -SkipLoadTest           Skip the load testing phase"
    Write-Host "  -SkipMonitoring         Skip the resource monitoring phase"
    Write-Host "  -Help                   Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\kubctl-0x01.ps1                           # Scale to 3 replicas and run full test"
    Write-Host "  .\kubctl-0x01.ps1 -Replicas 5               # Scale to 5 replicas"
    Write-Host "  .\kubctl-0x01.ps1 -Duration 60s -Connections 20  # Run 60s load test with 20 connections"
    Write-Host "  .\kubctl-0x01.ps1 -SkipLoadTest             # Scale and monitor without load testing"
}

# Function to check if required tools are installed
function Test-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    # Check kubectl
    try {
        $null = kubectl version --client --short 2>$null
    }
    catch {
        Write-Error "kubectl is not installed or not in PATH"
        Write-Status "Please install kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/"
        exit 1
    }
    
    # Check if Kubernetes cluster is accessible
    try {
        $null = kubectl cluster-info 2>$null
    }
    catch {
        Write-Error "Kubernetes cluster is not accessible. Make sure minikube is running."
        Write-Status "Try running: minikube start"
        exit 1
    }
    
    # Check wrk for load testing
    $wrkAvailable = $false
    try {
        $null = wrk --version 2>$null
        $wrkAvailable = $true
    }
    catch {
        Write-Warning "wrk is not installed. Load testing will be skipped."
        Write-Status "To install wrk on Windows, download from: https://github.com/wg/wrk/releases"
    }
    
    return $wrkAvailable
}

# Function to check if deployment exists
function Test-Deployment {
    Write-Status "Checking if deployment '$DEPLOYMENT_NAME' exists..."
    
    try {
        $null = kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE 2>$null
        Write-Success "Deployment '$DEPLOYMENT_NAME' found"
        return $true
    }
    catch {
        Write-Error "Deployment '$DEPLOYMENT_NAME' not found in namespace '$NAMESPACE'"
        Write-Status "Make sure to apply the deployment.yaml first:"
        Write-Status "kubectl apply -f deployment.yaml"
        exit 1
    }
}

# Function to get current replica count
function Get-CurrentReplicas {
    try {
        $replicas = kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>$null
        return [int]$replicas
    }
    catch {
        return 0
    }
}

# Function to scale the deployment
function Set-DeploymentScale {
    $currentReplicas = Get-CurrentReplicas
    Write-Status "Current replicas: $currentReplicas"
    
    if ($currentReplicas -eq $Replicas) {
        Write-Warning "Deployment is already scaled to $Replicas replicas"
        return
    }
    
    Write-Status "Scaling deployment '$DEPLOYMENT_NAME' to $Replicas replicas..."
    kubectl scale deployment $DEPLOYMENT_NAME --replicas=$Replicas -n $NAMESPACE
    
    Write-Status "Waiting for deployment to be ready..."
    kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=300s
    
    Write-Success "Successfully scaled deployment to $Replicas replicas"
}

# Function to verify pods are running
function Test-Pods {
    Write-Status "Verifying that multiple pods are running..."
    
    Write-Host "`nCurrent pods:" -ForegroundColor Blue
    kubectl get pods -l app=$DEPLOYMENT_NAME -n $NAMESPACE -o wide
    
    $runningPods = (kubectl get pods -l app=$DEPLOYMENT_NAME -n $NAMESPACE --field-selector=status.phase=Running --no-headers | Measure-Object).Count
    
    if ($runningPods -ge $Replicas) {
        Write-Success "$runningPods pods are running (target: $Replicas)"
    }
    else {
        Write-Warning "Only $runningPods pods are running (target: $Replicas)"
        Write-Status "Waiting a bit more for pods to start..."
        Start-Sleep -Seconds 10
        kubectl get pods -l app=$DEPLOYMENT_NAME -n $NAMESPACE
    }
}

# Function to get service URL for load testing
function Get-ServiceUrl {
    # Check if service exists
    try {
        $null = kubectl get service $SERVICE_NAME -n $NAMESPACE 2>$null
    }
    catch {
        Write-Error "Service '$SERVICE_NAME' not found"
        return $null
    }
    
    # For minikube, try to get service URL
    try {
        $serviceUrl = minikube service $SERVICE_NAME --url -n $NAMESPACE 2>$null
        if ($serviceUrl) {
            return $serviceUrl
        }
    }
    catch {
        # Minikube command failed, continue to port-forward
    }
    
    # Fallback to port-forward
    Write-Status "Using port-forward to access the service..."
    $job = Start-Job -ScriptBlock {
        kubectl port-forward service/$using:SERVICE_NAME 8080:80 -n $using:NAMESPACE
    }
    
    Start-Sleep -Seconds 3
    return "http://localhost:8080"
}

# Function to perform load testing
function Invoke-LoadTest {
    param([bool]$WrkAvailable)
    
    if (-not $WrkAvailable) {
        Write-Warning "Skipping load test - wrk not installed"
        return
    }
    
    Write-Status "Getting service URL for load testing..."
    $serviceUrl = Get-ServiceUrl
    
    if (-not $serviceUrl) {
        Write-Error "Could not determine service URL for load testing"
        return
    }
    
    Write-Status "Service URL: $serviceUrl"
    Write-Status "Performing load test for $Duration with $Connections connections..."
    
    Write-Host "`nLoad Test Results:" -ForegroundColor Blue
    
    try {
        wrk -t$LOAD_TEST_THREADS -c$Connections -d$Duration --timeout=10s "$serviceUrl/admin/"
        Write-Success "Load test completed"
    }
    catch {
        Write-Error "Load test failed: $_"
    }
    finally {
        # Cleanup any port-forward jobs
        Get-Job | Where-Object { $_.Command -like "*port-forward*" } | Stop-Job -PassThru | Remove-Job
    }
}

# Function to monitor resource usage
function Watch-Resources {
    Write-Status "Monitoring resource usage..."
    
    # Check if metrics-server is available
    try {
        $null = kubectl top nodes 2>$null
        
        Write-Host "`nNode resource usage:" -ForegroundColor Blue
        kubectl top nodes
        
        Write-Host "`nPod resource usage:" -ForegroundColor Blue
        kubectl top pods -l app=$DEPLOYMENT_NAME -n $NAMESPACE
    }
    catch {
        Write-Warning "Metrics server not available. Resource monitoring will be limited."
        Write-Status "To enable metrics in minikube: minikube addons enable metrics-server"
    }
    
    Write-Host "`nPod resource requests and limits:" -ForegroundColor Blue
    kubectl describe pods -l app=$DEPLOYMENT_NAME -n $NAMESPACE | Select-String -Pattern "Limits|Requests" -Context 2,3
}

# Function to show deployment status
function Show-DeploymentStatus {
    Write-Host "`nDeployment Status:" -ForegroundColor Blue
    kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o wide
    
    Write-Host "`nReplicaSet Status:" -ForegroundColor Blue
    kubectl get replicaset -l app=$DEPLOYMENT_NAME -n $NAMESPACE
    
    Write-Host "`nService Status:" -ForegroundColor Blue
    kubectl get service $SERVICE_NAME -n $NAMESPACE -o wide
}

# Main execution
function Main {
    if ($Help) {
        Show-Usage
        exit 0
    }
    
    Write-Host "=== Kubernetes Application Scaling Script ===" -ForegroundColor Green
    Write-Host "Target deployment: $DEPLOYMENT_NAME" -ForegroundColor Blue
    Write-Host "Target replicas: $Replicas" -ForegroundColor Blue
    Write-Host "Namespace: $NAMESPACE" -ForegroundColor Blue
    Write-Host ""
    
    # Step 1: Check prerequisites
    $wrkAvailable = Test-Prerequisites
    
    # Step 2: Check if deployment exists
    Test-Deployment
    
    # Step 3: Scale the deployment
    Set-DeploymentScale
    
    # Step 4: Verify pods are running
    Test-Pods
    
    # Step 5: Show deployment status
    Show-DeploymentStatus
    
    # Step 6: Perform load testing (if wrk is available and not skipped)
    if (-not $SkipLoadTest -and $wrkAvailable) {
        Invoke-LoadTest -WrkAvailable $wrkAvailable
    }
    elseif ($SkipLoadTest) {
        Write-Status "Skipping load test as requested"
    }
    
    # Step 7: Monitor resource usage (if not skipped)
    if (-not $SkipMonitoring) {
        Watch-Resources
    }
    else {
        Write-Status "Skipping resource monitoring as requested"
    }
    
    Write-Host ""
    Write-Success "Kubernetes scaling demonstration completed!"
    Write-Host "Useful commands for further monitoring:" -ForegroundColor Blue
    Write-Host "  kubectl get pods -l app=$DEPLOYMENT_NAME -w"
    Write-Host "  kubectl logs -l app=$DEPLOYMENT_NAME --tail=50"
    Write-Host "  kubectl describe deployment $DEPLOYMENT_NAME"
    Write-Host "  kubectl top pods -l app=$DEPLOYMENT_NAME"
}

# Run main function
Main