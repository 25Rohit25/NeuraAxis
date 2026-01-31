
data "aws_availability_zones" "available" {}

locals {
  name   = "neuraxis-${var.environment}"
  azs    = slice(data.aws_availability_zones.available.names, 0, 3)
}

# 1. VPC Configuration
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${local.name}-vpc"
  cidr = var.vpc_cidr

  azs             = local.azs
  private_subnets = [for k, v in local.azs : cidrsubnet(var.vpc_cidr, 8, k)]
  public_subnets  = [for k, v in local.azs : cidrsubnet(var.vpc_cidr, 8, k + 4)]
  database_subnets = [for k, v in local.azs : cidrsubnet(var.vpc_cidr, 8, k + 8)]

  enable_nat_gateway   = true
  single_nat_gateway   = true # Save cost in non-critical prod, set false for HA
  enable_dns_hostnames = true
  
  # Tags required for EKS
  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}

# 2. EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "${local.name}-eks"
  cluster_version = "1.29"

  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  cluster_endpoint_public_access = true

  eks_managed_node_group_defaults = {
    ami_type = "AL2_x86_64"
  }

  eks_managed_node_groups = {
    general = {
      name = "node-general"
      instance_types = ["t3.medium"]
      min_size     = 1
      max_size     = 3
      desired_size = 2
    }
    
    ai_workload = {
      name = "node-ai"
      instance_types = ["g4dn.xlarge"] # GPU Instance for AI (or m5.large if CPU)
      min_size     = 1
      max_size     = 5
      desired_size = 1
      
      taints = {
        dedicated = {
          key    = "workload"
          value  = "ai"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }
}

# 3. RDS PostgreSQL
module "db" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${local.name}-db"

  engine               = "postgres"
  engine_version       = "15"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = "db.r6g.large"

  allocated_storage     = 20
  max_allocated_storage = 100

  db_name  = "neuraxis"
  username = "neuraxis_admin"
  password = var.db_password
  port     = 5432

  multi_az               = true
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [module.security_group_db.security_group_id]

  maintenance_window      = "Mon:00:00-Mon:03:00"
  backup_window           = "03:00-06:00"
  backup_retention_period = 35

  deletion_protection = true
}

# 4. Security Group for RDS
module "security_group_db" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = "${local.name}-db-sg"
  description = "PostgreSQL security group"
  vpc_id      = module.vpc.vpc_id

  # Ingress Rule
  ingress_with_cidr_blocks = [
    {
      from_port   = 5432
      to_port     = 5432
      protocol    = "tcp"
      description = "PostgreSQL access within VPC"
      cidr_blocks = module.vpc.vpc_cidr_block
    },
  ]
}

# 5. ElastiCache Redis
module "redis" {
  source = "terraform-aws-modules/elasticache/aws"
  version = "1.0.0" # approximate version check
  
  replication_group_id = "${local.name}-redis"
  description          = "NeurAxis Redis Cluster"
  engine               = "redis"
  node_type            = "cache.r6g.large"
  num_cache_clusters   = 2
  parameter_group_name = "default.redis7"
  port                 = 6379
  
  subnet_group_name  = module.vpc.database_subnet_group_name # reusing DB subnet usually fine, or create cache subnets
  security_group_ids = [module.security_group_redis.id]
}
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${local.name}-redis-subnet"
  subnet_ids = module.vpc.database_subnets
}

module "security_group_redis" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = "${local.name}-redis-sg"
  vpc_id      = module.vpc.vpc_id

  ingress_with_cidr_blocks = [
    {
      from_port   = 6379
      to_port     = 6379
      protocol    = "tcp"
      description = "Redis access within VPC"
      cidr_blocks = module.vpc.vpc_cidr_block
    },
  ]
}

# 6. S3 Buckets
module "s3_images" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 3.0"

  bucket = "${local.name}-medical-images"
  acl    = "private"

  versioning = {
    enabled = true
  }

  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
    }
  }
}
