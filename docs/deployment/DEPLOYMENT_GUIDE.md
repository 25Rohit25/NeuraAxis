# Production Deployment Guide

## Prerequisites

1. **AWS CLI** configured (`aws configure`)
2. **Terraform** v1.0+ (`terraform version`)
3. **Kubectl** (`kubectl version`)
4. **Helm** (`helm version`)

## Phase 1: Infrastructure Provisioning (Terraform)

Navigate to `infrastructure/terraform`:

```bash
cd infrastructure/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

**Outputs to Note:**

- `cluster_endpoint`
- `db_instance_endpoint`

## Phase 2: Kubernetes Configuration

1. **Connect kubectl to EKS:**
   ```bash
   aws eks update-kubeconfig --region us-east-1 --name neuraxis-prod-eks
   ```
2. **Setup Secrets:**
   ```bash
   kubectl create secret generic db-credentials \
     --from-literal=username=neuraxis_admin \
     --from-literal=password=$DB_PASSWORD
   ```

## Phase 3: Application Deployment (Helm)

We use a custom Helm chart for consistency.

```bash
cd infrastructure/helm/neuraxis
helm upgrade --install neuraxis-app . \
  --namespace production \
  --create-namespace \
  --set database.host=<DB_ENDPOINT>
```

## Phase 4: CI/CD Setup

Github Actions are configured in `.github/workflows/deploy.yml`.
Ensure the following Secrets are set in GitHub Repository:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `ECR_REPOSITORY` (Create this manually in AWS Console first)

## Rollback Procedure

If a deployment fails:

```bash
helm rollback neuraxis-app --namespace production
```
