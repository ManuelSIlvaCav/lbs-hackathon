resource "aws_elasticache_parameter_group" "custom_redis_parameter_group_dev" {
  name   = "custom-redis-parameter-group-dev"
  family = "redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "3600"
  }
}

resource "aws_elasticache_subnet_group" "redis_public_subnet_group_dev" {
  name       = "redis-public-subnet-group-dev"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "redis-public-subnet-group-dev"
  }
}


resource "aws_elasticache_cluster" "redis_cluster_dev" {
  cluster_id           = "redis-cluster-dev"
  engine               = "redis"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  parameter_group_name = aws_elasticache_parameter_group.custom_redis_parameter_group_dev.name
  port                 = 6379
  security_group_ids   = [aws_security_group.redis_dev_sg.id]
  subnet_group_name    = aws_elasticache_subnet_group.redis_public_subnet_group_dev.name
}


resource "aws_security_group" "redis_dev_sg" {
  name        = "redis-sg-dev"
  description = "Security group for Redis cluster"
  vpc_id      = var.vpc_id

  ingress {
    description = "Allow Redis access from ECS"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
  }
}
