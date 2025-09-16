# Docker Hub Integration Setup for GitHub Actions

This guide explains how to set up GitHub secrets for Docker Hub integration with the `dep.yml` workflow.

## Required GitHub Secrets

You need to configure the following secrets in your GitHub repository:

### 1. DOCKERHUB_USERNAME
- **Description**: Your Docker Hub username
- **Value**: Your Docker Hub account username (e.g., `johndoe`)

### 2. DOCKERHUB_TOKEN
- **Description**: Docker Hub access token for authentication
- **Value**: A Docker Hub access token (NOT your password)

## How to Set Up GitHub Secrets

### Step 1: Create Docker Hub Access Token

1. Log in to [Docker Hub](https://hub.docker.com/)
2. Go to **Account Settings** → **Security**
3. Click **New Access Token**
4. Enter a description (e.g., "GitHub Actions CI/CD")
5. Select permissions:
   - **Read, Write, Delete** (recommended for full CI/CD functionality)
   - Or **Read, Write** (minimum required for pushing images)
6. Click **Generate**
7. **IMPORTANT**: Copy the token immediately - you won't be able to see it again!

### Step 2: Add Secrets to GitHub Repository

1. Go to your GitHub repository: `https://github.com/YOUR_USERNAME/alx-backend-python`
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**

#### Add DOCKERHUB_USERNAME:
- **Name**: `DOCKERHUB_USERNAME`
- **Secret**: Your Docker Hub username
- Click **Add secret**

#### Add DOCKERHUB_TOKEN:
- **Name**: `DOCKERHUB_TOKEN`
- **Secret**: The access token you generated in Step 1
- Click **Add secret**

## Workflow Behavior

### When the workflow runs:

1. **On Pull Requests**: 
   - Builds the Docker image for testing
   - Does NOT push to Docker Hub (for security)
   - Runs vulnerability scanning

2. **On Push to main/develop branches**:
   - Builds the Docker image
   - Pushes to Docker Hub with appropriate tags
   - Runs security vulnerability scanning
   - Uploads scan results to GitHub Security tab

3. **On Git Tags (v*)**: 
   - Creates semantic version tags (e.g., v1.0.0 → 1.0.0, 1.0, 1)
   - Pushes versioned images to Docker Hub

### Image Tags Generated:

- `latest` (for main branch)
- `main` or `develop` (branch names)
- `v1.0.0`, `1.0`, `1` (for version tags)
- `main-abc1234` (branch + commit SHA)

## Docker Hub Repository

Your images will be pushed to:
```
docker.io/YOUR_DOCKERHUB_USERNAME/messaging-app
```

## Testing the Setup

1. Ensure both secrets are configured
2. Push a commit to the `main` or `develop` branch
3. Check the **Actions** tab in GitHub to see the workflow running
4. Verify the image appears in your Docker Hub repository

## Troubleshooting

### Common Issues:

1. **Authentication Failed**:
   - Verify `DOCKERHUB_USERNAME` is correct
   - Ensure `DOCKERHUB_TOKEN` is an access token, not your password
   - Check that the access token has write permissions

2. **Repository Not Found**:
   - The Docker Hub repository will be created automatically on first push
   - Ensure your Docker Hub account has sufficient permissions

3. **Workflow Fails on PR**:
   - This is expected - PRs don't push to Docker Hub for security
   - The workflow should still build the image successfully

## Security Best Practices

- ✅ Use access tokens instead of passwords
- ✅ Limit token permissions to what's needed
- ✅ Regularly rotate access tokens
- ✅ Never commit secrets to your repository
- ✅ Use GitHub's encrypted secrets feature

## Next Steps

After setting up the secrets:
1. Test the workflow by pushing to main branch
2. Verify images are pushed to Docker Hub
3. Check security scan results in GitHub Security tab
4. Consider setting up automated deployments using the pushed images