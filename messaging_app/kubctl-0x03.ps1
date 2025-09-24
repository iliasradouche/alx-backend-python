# kubctl-0x03.ps1: Rolling Update Management Script (PowerShell)
# This script performs rolling updates with zero-downtime monitoring
# Author: ALX Backend Python Course
# Version: 1.0

param(
    [Parameter(Position=0)]
    [ValidateSet("rolling-update", "apply-only", "monitor-only", "verify-only", "downtime-test", "help")]
    [string]$Command = "rolling-update",
    
    [string]$Namespace = "default",
    [int]$Timeout = 600,
    [string]$Deployment = "django-messaging-app-blue",
    [string]$DeploymentFile = "blue_deployment.yaml",
    [int]$TestInterval = 2,
    [int]$MaxDowntimeTests = 300
)

# Error handling
$ErrorActionPreference = "Stop"

# Configuration
$SERVICE = "django-messaging-service"

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

function Write-Test {
    param([string]$Message)
    Write-Host "[TEST] $Message" -ForegroundColor Cyan
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    # Check if kubectl is installed
    try {
        $null = kubectl version --client --short 2>$null
    }
    catch {
        Write-Error "kubectl is not installed or not in PATH"
        exit 1
    }
    
    # Check if curl is available (use Invoke-WebRequest as fallback)
    $script:UseCurl = $true
    try {
        $null = curl --version 2>$null
    }
    catch {
        $script:UseCurl = $false
        Write-Warning "curl not found, using Invoke-WebRequest instead"
    }
    
    # Check if cluster is accessible
    try {
        $null = kubectl cluster-info 2>$null
    }
    catch {
        Write-Error "Cannot connect to Kubernetes cluster"
        exit 1
    }
    
    # Check if deployment file exists
    if (-not (Test-Path $DeploymentFile)) {
        Write-Error "Deployment file $DeploymentFile not found"
        exit 1
    }
    
    # Check if deployment exists
    try {
        $null = kubectl get deployment $Deployment -n $Namespace 2>$null
    }
    catch {
        Write-Error "Deployment $Deployment not found in namespace $Namespace"
        exit 1
    }
    
    Write-Success "Prerequisites check passed"
}

# Function to get service URL for testing
function Get-ServiceUrl {
    try {
        $serviceType = kubectl get service $SERVICE -n $Namespace -o jsonpath='{.spec.type}' 2>$null
        
        switch ($serviceType) {
            "NodePort" {
                $nodePort = kubectl get service $SERVICE -n $Namespace -o jsonpath='{.spec.ports[0].nodePort}'
                try {
                    $minikubeIp = minikube ip 2>$null
                    if (-not $minikubeIp) { $minikubeIp = "localhost" }
                }
                catch {
                    $minikubeIp = "localhost"
                }
                return "http://${minikubeIp}:${nodePort}"
            }
            "LoadBalancer" {
                try {
                    $externalIp = kubectl get service $SERVICE -n $Namespace -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>$null
                    if ($externalIp) {
                        return "http://$externalIp"
                    }
                }
                catch { }
                return "port-forward"
            }
            default {
                return "port-forward"
            }
        }
    }
    catch {
        return "port-forward"
    }
}

# Function to start port-forward if needed
function Start-PortForward {
    param([string]$ServiceUrl)
    
    if ($ServiceUrl -eq "port-forward") {
        Write-Status "Starting port-forward for service $SERVICE..."
        $job = Start-Job -ScriptBlock {
            param($service, $namespace)
            kubectl port-forward service/$service 8080:80 -n $namespace
        } -ArgumentList $SERVICE, $Namespace
        
        Start-Sleep -Seconds 3  # Give port-forward time to start
        return @{
            Url = "http://localhost:8080"
            Job = $job
        }
    }
    else {
        return @{
            Url = $ServiceUrl
            Job = $null
        }
    }
}

# Function to stop port-forward
function Stop-PortForward {
    param($PortForwardInfo)
    
    if ($PortForwardInfo.Job) {
        Stop-Job $PortForwardInfo.Job -ErrorAction SilentlyContinue
        Remove-Job $PortForwardInfo.Job -ErrorAction SilentlyContinue
        Write-Status "Port-forward stopped"
    }
}

# Function to test application availability
function Test-Application {
    param([string]$Url, [int]$TimeoutSeconds = 5)
    
    try {
        if ($script:UseCurl) {
            $result = curl -s --max-time $TimeoutSeconds "$Url/" 2>$null
            return $LASTEXITCODE -eq 0
        }
        else {
            $response = Invoke-WebRequest -Uri "$Url/" -TimeoutSec $TimeoutSeconds -ErrorAction Stop
            return $response.StatusCode -eq 200
        }
    }
    catch {
        try {
            if ($script:UseCurl) {
                $result = curl -s --max-time $TimeoutSeconds "$Url/admin/" 2>$null
                return $LASTEXITCODE -eq 0
            }
            else {
                $response = Invoke-WebRequest -Uri "$Url/admin/" -TimeoutSec $TimeoutSeconds -ErrorAction Stop
                return $response.StatusCode -eq 200
            }
        }
        catch {
            return $false
        }
    }
}

# Function to monitor downtime during rolling update
function Start-DowntimeMonitoring {
    param([string]$ServiceUrl, $PortForwardInfo)
    
    Write-Status "Starting downtime monitoring..."
    Write-Test "Testing URL: $ServiceUrl"
    
    $downtimeCount = 0
    $totalTests = 0
    $consecutiveFailures = 0
    $maxConsecutiveFailures = 0
    $startTime = Get-Date
    
    # Create log file for detailed results
    $logFile = "downtime_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
    $logContent = @(
        "Rolling Update Downtime Test - $(Get-Date)",
        "Service URL: $ServiceUrl",
        "Test Interval: ${TestInterval}s",
        "----------------------------------------"
    )
    $logContent | Out-File -FilePath $logFile -Encoding UTF8
    
    Write-Status "Downtime monitoring started. Press Ctrl+C to stop."
    
    try {
        while ($totalTests -lt $MaxDowntimeTests) {
            $testStart = Get-Date
            
            if (Test-Application -Url $ServiceUrl -TimeoutSeconds 5) {
                $testEnd = Get-Date
                $responseTime = ($testEnd - $testStart).TotalSeconds
                
                Write-Host "`r✓ Test $($totalTests + 1): OK ($([math]::Round($responseTime, 3))s)" -NoNewline -ForegroundColor Green
                "$(Get-Date -Format 'HH:mm:ss') - Test $($totalTests + 1): SUCCESS ($([math]::Round($responseTime, 3))s)" | Out-File -FilePath $logFile -Append -Encoding UTF8
                
                if ($consecutiveFailures -gt 0) {
                    Write-Host ""  # New line after failures
                    Write-Success "Service recovered after $consecutiveFailures consecutive failures"
                    "$(Get-Date -Format 'HH:mm:ss') - Service recovered after $consecutiveFailures failures" | Out-File -FilePath $logFile -Append -Encoding UTF8
                }
                $consecutiveFailures = 0
            }
            else {
                $testEnd = Get-Date
                $responseTime = ($testEnd - $testStart).TotalSeconds
                
                Write-Host "`r✗ Test $($totalTests + 1): FAILED ($([math]::Round($responseTime, 3))s)" -NoNewline -ForegroundColor Red
                "$(Get-Date -Format 'HH:mm:ss') - Test $($totalTests + 1): FAILED ($([math]::Round($responseTime, 3))s)" | Out-File -FilePath $logFile -Append -Encoding UTF8
                
                $downtimeCount++
                $consecutiveFailures++
                
                if ($consecutiveFailures -gt $maxConsecutiveFailures) {
                    $maxConsecutiveFailures = $consecutiveFailures
                }
                
                if ($consecutiveFailures -eq 1) {
                    Write-Host ""  # New line before first failure
                    Write-Warning "Downtime detected!"
                }
            }
            
            $totalTests++
            Start-Sleep -Seconds $TestInterval
        }
    }
    catch {
        Write-Status "Downtime monitoring interrupted"
    }
    
    # Final statistics
    $endTime = Get-Date
    $totalDuration = ($endTime - $startTime).TotalSeconds
    $downtimePercentage = if ($totalTests -gt 0) { [math]::Round(($downtimeCount * 100 / $totalTests), 2) } else { 0 }
    $successRate = if ($totalTests -gt 0) { [math]::Round((($totalTests - $downtimeCount) * 100 / $totalTests), 2) } else { 0 }
    
    $finalStats = @(
        "",
        "----------------------------------------",
        "Final Statistics:",
        "Total Tests: $totalTests",
        "Failed Tests: $downtimeCount",
        "Success Rate: ${successRate}%",
        "Downtime Percentage: ${downtimePercentage}%",
        "Max Consecutive Failures: $maxConsecutiveFailures",
        "Total Duration: $([math]::Round($totalDuration, 2))s"
    )
    $finalStats | Out-File -FilePath $logFile -Append -Encoding UTF8
    
    Write-Host ""
    Write-Status "Downtime monitoring completed"
    Write-Status "Total tests: $totalTests"
    Write-Status "Failed tests: $downtimeCount"
    Write-Status "Downtime percentage: ${downtimePercentage}%"
    Write-Status "Max consecutive failures: $maxConsecutiveFailures"
    Write-Status "Detailed log saved to: $logFile"
    
    Stop-PortForward $PortForwardInfo
}

# Function to apply rolling update
function Invoke-RollingUpdate {
    Write-Status "Applying rolling update..."
    
    # Apply the updated deployment
    try {
        kubectl apply -f $DeploymentFile
        Write-Success "Deployment configuration applied"
    }
    catch {
        Write-Error "Failed to apply deployment configuration"
        return $false
    }
    
    # Trigger rolling update by adding annotation
    $timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    try {
        kubectl annotate deployment $Deployment -n $Namespace "deployment.kubernetes.io/revision=$timestamp" --overwrite
        Write-Success "Rolling update triggered"
    }
    catch {
        Write-Warning "Failed to add annotation, but deployment may still update"
    }
    
    return $true
}

# Function to monitor rollout status
function Watch-Rollout {
    Write-Status "Monitoring rollout status..."
    
    try {
        kubectl rollout status deployment/$Deployment -n $Namespace --timeout="${Timeout}s"
        Write-Success "Rolling update completed successfully"
        return $true
    }
    catch {
        Write-Error "Rolling update failed or timed out"
        return $false
    }
}

# Function to verify rolling update completion
function Test-RolloutCompletion {
    Write-Status "Verifying rolling update completion..."
    
    try {
        $readyReplicas = kubectl get deployment $Deployment -n $Namespace -o jsonpath='{.status.readyReplicas}' 2>$null
        $desiredReplicas = kubectl get deployment $Deployment -n $Namespace -o jsonpath='{.spec.replicas}' 2>$null
        
        if (-not $readyReplicas) { $readyReplicas = "0" }
        if (-not $desiredReplicas) { $desiredReplicas = "0" }
        
        if ($readyReplicas -eq $desiredReplicas -and [int]$readyReplicas -gt 0) {
            Write-Success "All replicas are ready ($readyReplicas/$desiredReplicas)"
        }
        else {
            Write-Error "Not all replicas are ready ($readyReplicas/$desiredReplicas)"
            return $false
        }
        
        # Check pod status
        Write-Status "Current pod status:"
        kubectl get pods -l app=$Deployment -n $Namespace -o wide
        
        # Verify image version
        Write-Status "Verifying image versions:"
        kubectl describe deployment $Deployment -n $Namespace | Select-String "Image:"
        
        # Check rollout history
        Write-Status "Rollout history:"
        kubectl rollout history deployment/$Deployment -n $Namespace
        
        return $true
    }
    catch {
        Write-Error "Failed to verify rollout completion"
        return $false
    }
}

# Function to show help
function Show-Help {
    Write-Host @"
kubctl-0x03.ps1: Rolling Update Management Script (PowerShell)

USAGE:
    .\kubctl-0x03.ps1 [COMMAND] [OPTIONS]

COMMANDS:
    rolling-update  Perform complete rolling update with monitoring
    apply-only      Apply deployment changes only
    monitor-only    Monitor existing rollout
    verify-only     Verify rollout completion
    downtime-test   Test for downtime only (no deployment changes)
    help            Show this help message

OPTIONS:
    -Namespace      Kubernetes namespace (default: default)
    -Timeout        Timeout in seconds (default: 600)
    -Deployment     Deployment name (default: django-messaging-app-blue)
    -DeploymentFile Deployment file (default: blue_deployment.yaml)

EXAMPLES:
    .\kubctl-0x03.ps1 rolling-update
    .\kubctl-0x03.ps1 apply-only
    .\kubctl-0x03.ps1 monitor-only
    .\kubctl-0x03.ps1 downtime-test
    .\kubctl-0x03.ps1 verify-only

"@
}

# Main function for complete rolling update
function Start-CompleteRollingUpdate {
    Write-Status "Starting complete rolling update process..."
    
    # Step 1: Check prerequisites
    Test-Prerequisites
    
    # Step 2: Get service URL for testing
    $serviceUrl = Get-ServiceUrl
    $portForwardInfo = Start-PortForward $serviceUrl
    $serviceUrl = $portForwardInfo.Url
    
    Write-Status "Service URL for testing: $serviceUrl"
    
    # Step 3: Test initial connectivity
    Write-Test "Testing initial connectivity..."
    if (Test-Application -Url $serviceUrl) {
        Write-Success "Initial connectivity test passed"
    }
    else {
        Write-Error "Initial connectivity test failed"
        Stop-PortForward $portForwardInfo
        exit 1
    }
    
    # Step 4: Start downtime monitoring in background
    $monitoringJob = Start-Job -ScriptBlock {
        param($scriptPath, $serviceUrl, $portForwardInfo, $TestInterval, $MaxDowntimeTests)
        & $scriptPath downtime-test
    } -ArgumentList $PSCommandPath, $serviceUrl, $portForwardInfo, $TestInterval, $MaxDowntimeTests
    
    # Give monitoring time to start
    Start-Sleep -Seconds 3
    
    # Step 5: Apply rolling update
    if (-not (Invoke-RollingUpdate)) {
        Write-Error "Failed to apply rolling update"
        Stop-Job $monitoringJob -ErrorAction SilentlyContinue
        Remove-Job $monitoringJob -ErrorAction SilentlyContinue
        Stop-PortForward $portForwardInfo
        exit 1
    }
    
    # Step 6: Monitor rollout status
    if (-not (Watch-Rollout)) {
        Write-Error "Rolling update failed"
        Stop-Job $monitoringJob -ErrorAction SilentlyContinue
        Remove-Job $monitoringJob -ErrorAction SilentlyContinue
        Stop-PortForward $portForwardInfo
        exit 1
    }
    
    # Step 7: Verify completion
    if (-not (Test-RolloutCompletion)) {
        Write-Error "Rolling update verification failed"
        Stop-Job $monitoringJob -ErrorAction SilentlyContinue
        Remove-Job $monitoringJob -ErrorAction SilentlyContinue
        Stop-PortForward $portForwardInfo
        exit 1
    }
    
    # Step 8: Stop monitoring and cleanup
    Write-Status "Stopping downtime monitoring..."
    Stop-Job $monitoringJob -ErrorAction SilentlyContinue
    Remove-Job $monitoringJob -ErrorAction SilentlyContinue
    
    Write-Success "Rolling update completed successfully!"
    Write-Status "Final application test..."
    
    if (Test-Application -Url $serviceUrl) {
        Write-Success "Final connectivity test passed"
    }
    else {
        Write-Warning "Final connectivity test failed"
    }
    
    Stop-PortForward $portForwardInfo
}

# Main script execution
switch ($Command) {
    "rolling-update" {
        Start-CompleteRollingUpdate
    }
    "apply-only" {
        Test-Prerequisites
        Invoke-RollingUpdate
    }
    "monitor-only" {
        Test-Prerequisites
        Watch-Rollout
    }
    "verify-only" {
        Test-Prerequisites
        Test-RolloutCompletion
    }
    "downtime-test" {
        Test-Prerequisites
        $serviceUrl = Get-ServiceUrl
        $portForwardInfo = Start-PortForward $serviceUrl
        Start-DowntimeMonitoring $portForwardInfo.Url $portForwardInfo
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