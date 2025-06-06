# VCF Development Container
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
  # Core development tools
  curl \
  wget \
  git \
  vim \
  nano \
  build-essential \
  software-properties-common \
  # Python and development
  python3.11 \
  python3.11-dev \
  python3.11-venv \
  python3-pip \
  # HPC and performance tools
  htop \
  tree \
  jq \
  # Networking and utilities
  net-tools \
  openssh-client \
  # Cleanup
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Create symlinks for python
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
  ln -sf /usr/bin/python3.11 /usr/bin/python

# Install UV package manager - FIXED VERSION
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Alternative: Install UV via pip as backup
RUN python3 -m pip install --upgrade pip uv

# Create workspace directory
WORKDIR /workspace

# Install common Python development tools
COPY ./requirements-dev.txt /tmp/
RUN pip install -r /tmp/requirements-dev.txt

# Configure git (will be overridden by user)
RUN git config --global user.email "dev@vcf.local" && \
  git config --global user.name "VCF Developer" && \
  git config --global init.defaultBranch main

# Set up development environment
ENV PYTHONPATH="/workspace"
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Expose common development ports
EXPOSE 8000 8080 3000 5000

# Default command
CMD ["/bin/bash"]
