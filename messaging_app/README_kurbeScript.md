# kurbeScript - Kubernetes Local Cluster Management

This directory contains scripts to set up and manage a local Kubernetes cluster using minikube. The scripts are available in multiple formats for cross-platform compatibility.

## Available Scripts

### 1. `kurbeScript` (Bash - Linux/macOS)
The original bash script for Unix-like systems (Linux, macOS, WSL).

**Usage:**
```bash
# Make executable (Linux/macOS/WSL)
chmod +x kurbeScript

# Run the script
./kurbeScript
```

### 2. `kurbeScript.bat` (Windows Batch)
Windows batch file for Command Prompt compatibility.

**Usage:**
```cmd
# Run from Command Prompt
kurbeScript.bat
```

### 3. `kurbeScript.ps1` (PowerShell)
PowerShell script with enhanced features and better error handling.

**Usage:**
```powershell
# Run from PowerShell
.\kurbeScript.ps1

# Show help
.\kurbeScript.ps1 -Help
```

## What These Scripts Do

1. **Check Prerequisites**
   - Verify minikube installation
   - Check kubectl availability
   - Provide installation instructions if missing

2. **Start Kubernetes Cluster**
   - Start minikube with optimal settings
   - Try multiple drivers (docker, hyperv, virtualbox)
   - Handle already running clusters

3. **Verify Cluster Status**
   - Run `kubectl cluster-info` to verify connectivity
   - Display cluster information
   - Show node status

4. **Retrieve Pods**
   - List all pods across namespaces
   - Show pods in default namespace
   - Display total pod count

5. **Provide Useful Information**
   - Dashboard access instructions
   - Common kubectl commands
   - Cluster management tips

## Prerequisites

### Required Software

1. **minikube** - Local Kubernetes cluster
   - Download: https://minikube.sigs.k8s.io/docs/start/
   - Windows: `winget install Kubernetes.minikube` or `choco install minikube`
   - macOS: `brew install minikube`
   - Linux: See official documentation

2. **kubectl** (Optional - included with minikube)
   - Download: https://kubernetes.io/docs/tasks/tools/
   - Can use `minikube kubectl --` if not installed separately

3. **Container Runtime** (One of the following):
   - **Docker Desktop** (Recommended)
   - Hyper-V (Windows)
   - VirtualBox
   - VMware

### System Requirements

- **CPU**: 2+ cores
- **Memory**: 2GB+ free RAM
- **Disk**: 10GB+ free space
- **Virtualization**: Enabled in BIOS/UEFI

## Installation Guide

### Windows

1. **Install Docker Desktop**
   ```powershell
   winget install Docker.DockerDesktop
   ```

2. **Install minikube**
   ```powershell
   # Using winget
   winget install Kubernetes.minikube
   
   # Or using chocolatey
   choco install minikube
   
   # Or using scoop
   scoop install minikube
   ```

3. **Install kubectl (optional)**
   ```powershell
   winget install Kubernetes.kubectl
   ```

### macOS

1. **Install Docker Desktop**
   ```bash
   brew install --cask docker
   ```

2. **Install minikube**
   ```bash
   brew install minikube
   ```

3. **Install kubectl (optional)**
   ```bash
   brew install kubectl
   ```

### Linux (Ubuntu/Debian)

1. **Install Docker**
   ```bash
   sudo apt update
   sudo apt install docker.io
   sudo usermod -aG docker $USER
   ```

2. **Install minikube**
   ```bash
   curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
   sudo install minikube-linux-amd64 /usr/local/bin/minikube
   ```

3. **Install kubectl (optional)**
   ```bash
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   ```

## Troubleshooting

### Common Issues

1. **"minikube start" fails**
   - Ensure virtualization is enabled in BIOS
   - Try different drivers: `minikube start --driver=virtualbox`
   - Check available drivers: `minikube start --help`

2. **"kubectl" command not found**
   - Use `minikube kubectl -- [command]` instead
   - Or install kubectl separately

3. **Insufficient resources**
   - Reduce resource allocation: `minikube start --cpus=1 --memory=1024mb`
   - Close other applications to free up resources

4. **Docker driver issues**
   - Ensure Docker Desktop is running
   - Try: `minikube delete` then `minikube start`

### Useful Commands

```bash
# Check minikube status
minikube status

# Stop the cluster
minikube stop

# Delete the cluster
minikube delete

# Access Kubernetes dashboard
minikube dashboard

# Get dashboard URL
minikube dashboard --url

# SSH into minikube VM
minikube ssh

# View minikube logs
minikube logs

# List available addons
minikube addons list

# Enable an addon (e.g., ingress)
minikube addons enable ingress
```

## Next Steps

After running the script successfully:

1. **Explore the Dashboard**
   ```bash
   minikube dashboard
   ```

2. **Deploy a Sample Application**
   ```bash
   kubectl create deployment hello-minikube --image=k8s.gcr.io/echoserver:1.4
   kubectl expose deployment hello-minikube --type=NodePort --port=8080
   minikube service hello-minikube
   ```

3. **Learn kubectl Commands**
   ```bash
   kubectl get pods
   kubectl get services
   kubectl get deployments
   kubectl describe pod [pod-name]
   ```

4. **Try Kubernetes Tutorials**
   - Official Kubernetes tutorials: https://kubernetes.io/docs/tutorials/
   - minikube tutorials: https://minikube.sigs.k8s.io/docs/tutorials/

## Support

For issues and questions:
- minikube documentation: https://minikube.sigs.k8s.io/docs/
- Kubernetes documentation: https://kubernetes.io/docs/
- GitHub issues: https://github.com/kubernetes/minikube/issues

---

**Note**: These scripts are designed for learning and development purposes. For production Kubernetes clusters, consider using managed services like EKS, GKE, or AKS.