# kubctl-0x02.ps1: Blue-Green Deployment Management Script (PowerShell)
# This script manages blue-green deployments for the Django messaging app
# Author: ALX Backend Python Course
# Version: 1.0

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    
    [string]$Namespace = "default",
    [int]$Timeout = 300
)

# Configuration
$BLUE_DEPLOYMENT = "django-messaging-app-blue"
$GREEN_DEPLOYMENT = "django-messaging-app-green"
$MAIN_SERVICE = "django-messaging-service"

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

# Function to check prerequisites
function Test-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    # Check if kubectl is installed
    try {
        $null = Get-Command kubectl -ErrorAction Stop
    }
    catch {
        Write-Error "kubectl is not installed or not in PATH"
        exit 1
    }
    
    # Check if cluster is accessible
    try {
        kubectl cluster-info | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Cluster not accessible"
        }
    }
    catch {
        Write-Error "Cannot connect to Kubernetes cluster"
        exit 1
    }
    
    # Check if required files exist
    $files = @("blue_deployment.yaml", "green_deployment.yaml", "kubeservice.yaml")
    foreach ($file in $files) {
        if (-not (Test-Path $file)) {
            Write-Error "Required file $file not found"
            exit 1
        }
    }
    
    Write-Success "Prerequisites check passed"
}

# Function to deploy blue version
function Deploy-Blue {
    Write-Status "Deploying blue version..."
    
    kubectl apply -f blue_deployment.yaml
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to apply blue deployment"
        return $false
    }
    Write-Success "Blue deployment applied successfully"
    
    # Wait for blue deployment to be ready
    Write-Status "Waiting for blue deployment to be ready..."
    kubectl wait --for=condition=available --timeout="$($Timeout)s" deployment/$BLUE_DEPLOYMENT -n $Namespace
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Blue deployment failed to become ready within timeout"
        return $false
    }
    Write-Success "Blue deployment is ready"
    return $true
}

# Function to deploy green version
function Deploy-Green {
    Write-Status "Deploying green version..."
    
    kubectl apply -f green_deployment.yaml
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to apply green deployment"
        return $false
    }
    Write-Success "Green deployment applied successfully"
    
    # Wait for green deployment to be ready
    Write-Status "Waiting for green deployment to be ready..."
    kubectl wait --for=condition=available --timeout="$($Timeout)s" deployment/$GREEN_DEPLOYMENT -n $Namespace
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Green deployment failed to become ready within timeout"
        return $false
    }
    Write-Success "Green deployment is ready"
    return $true
}

# Function to apply services
function Apply-Services {
    Write-Status "Applying service configurations..."
    
    kubectl apply -f kubeservice.yaml
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to apply service configurations"
        return $false
    }
    Write-Success "Service configurations applied successfully"
    return $true
}

# Function to check logs for errors
function Test-Logs {
    param(
        [string]$Deployment,
        [string]$Version
    )
    
    Write-Status "Checking logs for $Version version..."
    
    # Get pods for the deployment
    $pods = kubectl get pods -l app=$Deployment -n $Namespace -o jsonpath='{.items[*].metadata.name}'
    
    if ([string]::IsNullOrEmpty($pods)) {
        Write-Warning "No pods found for $Deployment"
        return $false
    }
    
    $errorFound = $false
    
    foreach ($pod in $pods.Split(' ')) {
        if ([string]::IsNullOrEmpty($pod)) { continue }
        
        Write-Status "Checking logs for pod: $pod"
        
        # Check for errors in logs (last 50 lines)
        $logs = kubectl logs $pod -n $Namespace --tail=50 2>$null
        
        if ($logs -match "(?i)(error|exception|failed|traceback)") {
            Write-Error "Errors found in $pod logs:"
            $logs | Select-String "(?i)(error|exception|failed|traceback)" | Select-Object -First 10
            $errorFound = $true
        }
        else {
            Write-Success "No errors found in $pod logs"
        }
    }
    
    return -not $errorFound
}

# Function to get deployment status
function Get-DeploymentStatus {
    Write-Status "Current deployment status:"
    Write-Host ""
    kubectl get deployments -n $Namespace -l 'version in (blue,green)' -o wide
    Write-Host ""
    kubectl get pods -n $Namespace -l 'version in (blue,green)' -o wide
    Write-Host ""
    kubectl get services -n $Namespace -l 'app=django-messaging-app'
}

# Function to switch traffic to green
function Switch-ToGreen {
    Write-Status "Switching traffic from blue to green..."
    
    kubectl patch service $MAIN_SERVICE -n $Namespace -p '{"spec":{"selector":{"app":"django-messaging-app-green","version":"green"}}}'
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to switch traffic to green deployment"
        return $false
    }
    Write-Success "Traffic switched to green deployment"
    return $true
}

# Function to switch traffic to blue
function Switch-ToBlue {
    Write-Status "Switching traffic from green to blue..."
    
    kubectl patch service $MAIN_SERVICE -n $Namespace -p '{"spec":{"selector":{"app":"django-messaging-app-blue","version":"blue"}}}'
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to switch traffic to blue deployment"
        return $false
    }
    Write-Success "Traffic switched to blue deployment"
    return $true
}

# Function to cleanup green deployment
function Remove-GreenDeployment {
    Write-Status "Cleaning up green deployment..."
    
    kubectl delete deployment $GREEN_DEPLOYMENT -n $Namespace --ignore-not-found=true
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Green deployment cleaned up"
    }
    else {
        Write-Warning "Failed to cleanup green deployment"
    }
}

# Function to show help
function Show-Help {
    @"
kubctl-0x02.ps1: Blue-Green Deployment Management Script (PowerShell)

USAGE:
    .\kubctl-0x02.ps1 [COMMAND] [OPTIONS]

COMMANDS:
    deploy-blue     Deploy blue version only
    deploy-green    Deploy green version only
    deploy-both     Deploy both blue and green versions
    switch-green    Switch traffic to green deployment
    switch-blue     Switch traffic to blue deployment
    check-logs      Check logs for both deployments
    status          Show deployment status
    full-deploy     Full blue-green deployment process
    cleanup         Cleanup green deployment
    help            Show this help message

OPTIONS:
    -Namespace      Kubernetes namespace (default: default)
    -Timeout        Timeout in seconds (default: 300)

EXAMPLES:
    .\kubctl-0x02.ps1 full-deploy
    .\kubctl-0x02.ps1 deploy-green
    .\kubctl-0x02.ps1 switch-green
    .\kubctl-0x02.ps1 status
    .\kubctl-0x02.ps1 check-logs

"@
}

# Main function for full blue-green deployment
function Start-FullDeployment {
    Write-Status "Starting full blue-green deployment process..."
    
    # Step 1: Check prerequisites
    Test-Prerequisites
    
    # Step 2: Deploy blue version
    if (-not (Deploy-Blue)) {
        Write-Error "Blue deployment failed"
        exit 1
    }
    
    # Step 3: Apply services
    if (-not (Apply-Services)) {
        Write-Error "Service application failed"
        exit 1
    }
    
    # Step 4: Check blue logs
    if (-not (Test-Logs $BLUE_DEPLOYMENT "blue")) {
        Write-Warning "Errors found in blue deployment logs"
    }
    
    # Step 5: Deploy green version
    if (-not (Deploy-Green)) {
        Write-Error "Green deployment failed"
        exit 1
    }
    
    # Step 6: Check green logs
    if (-not (Test-Logs $GREEN_DEPLOYMENT "green")) {
        Write-Error "Errors found in green deployment logs"
        Write-Status "Keeping traffic on blue deployment due to green deployment errors"
        Get-DeploymentStatus
        exit 1
    }
    
    # Step 7: Switch traffic to green if no errors
    Write-Status "Green deployment is healthy, switching traffic..."
    if (-not (Switch-ToGreen)) {
        Write-Error "Failed to switch traffic to green"
        exit 1
    }
    
    # Step 8: Final status
    Write-Success "Blue-green deployment completed successfully!"
    Get-DeploymentStatus
}

# Main script logic
switch ($Command.ToLower()) {
    "deploy-blue" {
        Test-Prerequisites
        Deploy-Blue
    }
    "deploy-green" {
        Test-Prerequisites
        Deploy-Green
    }
    "deploy-both" {
        Test-Prerequisites
        Deploy-Blue
        Apply-Services
        Deploy-Green
    }
    "switch-green" {
        Switch-ToGreen
    }
    "switch-blue" {
        Switch-ToBlue
    }
    "check-logs" {
        Test-Logs $BLUE_DEPLOYMENT "blue"
        Test-Logs $GREEN_DEPLOYMENT "green"
    }
    "status" {
        Get-DeploymentStatus
    }
    "full-deploy" {
        Start-FullDeployment
    }
    "cleanup" {
        Remove-GreenDeployment
    }
    "help" {
        Show-Help
    }
    default {
        Write-Error "Unknown command: $Command"
        Show-Help
        exit 1
    }
}