#!/bin/bash

# PixelTracker CI/CD Setup Script
# This script commits and pushes the CI/CD configuration to GitHub

echo "🚀 Setting up CI/CD for PixelTracker"
echo "===================================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ This is not a git repository. Please run 'git init' first."
    exit 1
fi

# Check if we have a remote origin
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "❌ No remote origin found. Please add your GitHub repository:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/PixelTracker.git"
    exit 1
fi

echo "📋 Current git status:"
git status --short

echo ""
echo "📦 Adding CI/CD files..."

# Add all the CI/CD related files
git add .github/
git add Dockerfile
git add .dockerignore
git add docker-compose.yml
git add monitoring/
git add setup-cicd.sh

echo "✅ Files added to git"

echo ""
echo "📝 Committing changes..."
git commit -m "feat: Add comprehensive CI/CD pipeline with GitHub Actions

- Add matrix builds for core, full, and enterprise configurations
- Implement lint → type-check → unit tests → integration tests → benchmarks pipeline
- Add automated Docker image build and push to GHCR
- Integrate security scanning with CodeQL, Trivy, and Bandit
- Add Dependabot for automated dependency updates
- Include coverage reporting and benchmark regression checks
- Add monitoring setup with Prometheus and Grafana
- Create multi-stage Dockerfiles for different environments
- Add manual test workflow for CI/CD validation"

echo "✅ Changes committed"

echo ""
echo "🔄 Pushing to GitHub..."
git push origin $(git rev-parse --abbrev-ref HEAD)

echo "✅ Changes pushed to GitHub"

echo ""
echo "🎯 Next steps:"
echo "=============="
echo "1. Go to your GitHub repository"
echo "2. Click on the 'Actions' tab"
echo "3. You should see the workflows are now available"
echo "4. To test the setup:"
echo "   - Click on 'Manual CI/CD Test' workflow"
echo "   - Click 'Run workflow'"
echo "   - Select your preferred configuration"
echo "   - Click 'Run workflow' button"
echo ""
echo "5. Set up branch protection (recommended):"
echo "   - Go to Settings → Branches"
echo "   - Add rule for 'main' branch"
echo "   - Require status checks to pass"
echo "   - Select the CI/CD workflow checks"
echo ""
echo "🔗 Your repository: $(git remote get-url origin)"

echo ""
echo "🏁 CI/CD setup complete!"
