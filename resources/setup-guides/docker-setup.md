# Docker Setup Guide for VCF

## Prerequisites
- Docker or Docker Desktop installed
- Git configured
- VS Code with Remote containers extension (recommended)

## Quick Start
```bash
# Clone the repository
git clone https://github.com/grc-iit/vcf.git
cd vcf

# Pull pre-built container
docker pull [YOUR_DOCKERHUB_USERNAME]/vcf-dev:latest

# Run development container
docker run -it -v $(pwd):/workspace [YOUR_DOCKERHUB_USERNAME]/vcf-dev:latest
```
