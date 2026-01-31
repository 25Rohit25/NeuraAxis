# Infrastructure

> Infrastructure as Code and Deployment Configurations

## Overview

This directory contains infrastructure configuration files for deploying NEURAXIS to various environments.

## Contents

### Kubernetes
- `k8s/` - Kubernetes manifests
  - `base/` - Base configurations
  - `overlays/` - Environment-specific overlays (dev, staging, prod)

### Terraform
- `terraform/` - Infrastructure as Code
  - `modules/` - Reusable Terraform modules
  - `environments/` - Environment configurations

### Scripts
- `scripts/` - Deployment and utility scripts

## Deployment Environments

| Environment | Description |
|-------------|-------------|
| development | Local Docker Compose |
| staging | Pre-production testing |
| production | Live production environment |

## Getting Started

See the main README for development setup using Docker Compose.

For production deployments, refer to the [Deployment Guide](../docs/deployment.md).
