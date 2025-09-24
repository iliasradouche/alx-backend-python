# kurbeScript.ps1 - Kubernetes Local Cluster Management Script for PowerShell
# This script sets up and manages a local Kubernetes cluster using minikube

param(
    [switch]$Help
)

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$ForegroundColor = "White"
    )
    Write-Host $Message -ForegroundColor $ForegroundColor
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[SUCCESS] $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

# Function to check if a command exists
function Test-CommandExists {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Function to check minikube installation
function Test-MinikubeInstallation {
    Write-Info "Checking minikube installation..."
    
    if (Test-CommandExists "minikube") {
        try {
            $version = minikube version --short 2>$null
            Write-Success "minikube is installed (version: $version)"
            return $true
        }
        catch {
            $version = "unknown"
            Write-Success "minikube is installed (version: $version)"
            return $true
        }
    }
    else {
        Write-Error "minikube is not installed!"
        Write-Info "Please install minikube from: https://minikube.sigs.k8s.io/docs/start/"
        Write-Info "For Windows:"
        Write-Info "  - Download from: https://github.com/kubernetes/minikube/releases/latest"
        Write-Info "  - Or use chocolatey: choco install minikube"
        Write-Info "  - Or use winget: winget install Kubernetes.minikube"
        Write-Info "  - Or use scoop: scoop install minikube"
        return $false
    }
}

# Function to check kubectl installation
function Test-KubectlInstallation {
    Write-Info "Checking kubectl installation..."
    
    if (Test-CommandExists "kubectl") {
        try {
            $version = (kubectl version --client --short 2>$null).Split(' ')[2]
            Write-Success "kubectl is installed (version: $version)"
            return $true
        }
        catch {
            Write-Success "kubectl is installed"
            return $true
        }
    }
    else {
        Write-Warning "kubectl is not installed separately!"
        Write-Info "kubectl will be available through 'minikube kubectl' command"
        return $false
    }
}

# Function to start minikube cluster
function Start-MinikubeCluster {
    Write-Info "Starting Kubernetes cluster with minikube..."
    
    # Check if minikube is already running
    try {
        $status = minikube status 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Warning "minikube cluster is already running"
            minikube status
            return $true
        }
    }
    catch {
        # Cluster is not running, continue to start it
    }
    
    Write-Info "Starting new minikube cluster..."
    
    # Try different drivers in order of preference
    $drivers = @("docker", "hyperv", "virtualbox")
    
    foreach ($driver in $drivers) {
        Write-Info "Trying to start with $driver driver..."
        try {
            minikube start --driver=$driver --cpus=2 --memory=2048mb --disk-size=10gb
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Kubernetes cluster started successfully with $driver driver!"
                return $true
            }
        }
        catch {
            Write-Warning "Failed to start with $driver driver"
        }
    }
    
    Write-Error "Failed to start Kubernetes cluster with any driver"
    return $false
}

# Function to verify cluster is running
function Test-ClusterStatus {
    Write-Info "Verifying cluster status with kubectl cluster-info..."
    
    # Wait a moment for cluster to be fully ready
    Start-Sleep -Seconds 5
    
    $kubectlAvailable = Test-CommandExists "kubectl"
    
    try {
        if ($kubectlAvailable) {
            kubectl cluster-info 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Cluster is running and accessible!"
                Write-Host ""
                Write-Info "Cluster Information:"
                kubectl cluster-info
                Write-Host ""
                Write-Info "Node Status:"
                kubectl get nodes
                return $true
            }
        }
        
        # Try with minikube kubectl
        minikube kubectl -- cluster-info 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Cluster is running and accessible!"
            Write-Host ""
            Write-Info "Cluster Information:"
            minikube kubectl -- cluster-info
            Write-Host ""
            Write-Info "Node Status:"
            minikube kubectl -- get nodes
            return $true
        }
    }
    catch {
        # Continue to error handling
    }
    
    Write-Error "Cluster verification failed!"
    Write-Info "Trying to diagnose the issue..."
    minikube status
    return $false
}

# Function to retrieve available pods
function Get-KubernetesPods {
    Write-Info "Retrieving available pods..."
    
    $kubectlAvailable = Test-CommandExists "kubectl"
    
    Write-Host ""
    Write-Info "Pods in all namespaces:"
    
    try {
        if ($kubectlAvailable) {
            kubectl get pods --all-namespaces 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Info "Pods in default namespace:"
                kubectl get pods
                
                $podCount = (kubectl get pods --all-namespaces --no-headers 2>$null | Measure-Object).Count
                Write-Success "Total pods found: $podCount"
                return
            }
        }
        
        # Use minikube kubectl
        minikube kubectl -- get pods --all-namespaces
        Write-Host ""
        Write-Info "Pods in default namespace:"
        minikube kubectl -- get pods
        
        $podCount = (minikube kubectl -- get pods --all-namespaces --no-headers 2>$null | Measure-Object).Count
        Write-Success "Total pods found: $podCount"
    }
    catch {
        Write-Error "Failed to retrieve pods"
    }
}

# Function to show dashboard info
function Show-DashboardInfo {
    Write-Info "Kubernetes Dashboard Information:"
    Write-Info "To access the Kubernetes dashboard, run: minikube dashboard"
    Write-Info "To get the dashboard URL, run: minikube dashboard --url"
}

# Function to show useful commands
function Show-UsefulCommands {
    Write-Host ""
    Write-Info "Useful commands for managing your cluster:"
    Write-Host "  minikube status          - Check cluster status"
    Write-Host "  minikube stop            - Stop the cluster"
    Write-Host "  minikube delete          - Delete the cluster"
    Write-Host "  minikube dashboard       - Open Kubernetes dashboard"
    Write-Host "  kubectl get nodes        - List cluster nodes"
    Write-Host "  kubectl get pods         - List pods in default namespace"
    Write-Host "  kubectl get services     - List services"
    Write-Host "  kubectl get deployments - List deployments"
    Write-Host "  minikube kubectl -- [cmd] - Use kubectl through minikube"
}

# Function to show help
function Show-Help {
    Write-Host "kurbeScript.ps1 - Kubernetes Local Cluster Management Script"
    Write-Host ""
    Write-Host "This script helps you set up and manage a local Kubernetes cluster using minikube."
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\kurbeScript.ps1        - Run the full setup process"
    Write-Host "  .\kurbeScript.ps1 -Help  - Show this help message"
    Write-Host ""
    Write-Host "What this script does:"
    Write-Host "  1. Checks if minikube is installed"
    Write-Host "  2. Checks if kubectl is installed"
    Write-Host "  3. Starts a Kubernetes cluster using minikube"
    Write-Host "  4. Verifies the cluster is running with kubectl cluster-info"
    Write-Host "  5. Retrieves and displays available pods"
    Write-Host "  6. Shows useful commands for cluster management"
}

# Main execution
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    Write-Host "======================================" -ForegroundColor Magenta
    Write-Host "    Kubernetes Local Setup Script    " -ForegroundColor Magenta
    Write-Host "======================================" -ForegroundColor Magenta
    Write-Host ""
    
    # Step 1: Check prerequisites
    if (-not (Test-MinikubeInstallation)) {
        Write-Host ""
        Write-Host "Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        return
    }
    
    Test-KubectlInstallation
    Write-Host ""
    
    # Step 2: Start the cluster
    if (-not (Start-MinikubeCluster)) {
        Write-Host ""
        Write-Host "Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        return
    }
    Write-Host ""
    
    # Step 3: Verify the cluster
    if (-not (Test-ClusterStatus)) {
        Write-Host ""
        Write-Host "Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        return
    }
    
    # Step 4: Get available pods
    Get-KubernetesPods
    Write-Host ""
    
    # Step 5: Show additional information
    Show-DashboardInfo
    Show-UsefulCommands
    
    Write-Host ""
    Write-Success "Kubernetes cluster setup completed successfully!"
    Write-Host "======================================" -ForegroundColor Magenta
    
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Run main function
Main