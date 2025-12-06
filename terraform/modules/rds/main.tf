resource "aws_security_group" "rds_security_group" {
  name        = "rds_sg"
  description = "enable postgre access on port 5432"
  vpc_id = var.vpc_id

  ingress {
    protocol        = "tcp"
    from_port       = 5432
    to_port         = 5432
    cidr_blocks     = ["0.0.0.0/0"]
    security_groups = flatten([
      var.ecs_sg_id != null ? [var.ecs_sg_id] : [],
      var.bastion_sg_id != null ? [var.bastion_sg_id] : []
    ])
  }

  egress {
    protocol    = "tcp"
    from_port   = 0
    to_port     = 65535
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Terraform   = "true"
    Environment = var.environment
  }
}

resource "aws_db_subnet_group" "rds" {
  name        = "${var.service_name}_private_subnet_group"
  description = "Private Subnet Group"
  subnet_ids  = var.private_subnet_ids

  tags = {
    Terraform   = "true"
    Environment = var.environment
  }
}

resource "aws_db_parameter_group" "postgres_pm" {
  name        = "${var.postgres_identifier}-postgres16"
  family      = "postgres16"
  description = "Custom Parameter Group for Postgres 16"
  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }
  parameter {
    name         = "log_statement"
    value        = "all"
    apply_method = "pending-reboot"
  }

  parameter {
    name  = "rds.force_ssl"
    value = "0"
  }

  tags = {
    Terraform   = "true"
    Environment = var.environment
  }

}

resource "aws_db_instance" "postgres_db" {
  identifier = var.postgres_identifier

  allocated_storage = 20
  storage_type      = "gp2"
  engine            = "postgres"
  engine_version    = "16.3"
  instance_class    = "db.t3.micro"

  username = var.postgres_user_name
  password = var.postgres_db_password
  port     = var.postgres_port
  db_name  = var.postgres_db_name

  parameter_group_name = aws_db_parameter_group.postgres_pm.name
  db_subnet_group_name = aws_db_subnet_group.rds.id
  vpc_security_group_ids = [aws_security_group.rds_security_group.id]

  publicly_accessible  = false
  skip_final_snapshot  = true
  tags = {
    Terraform   = "true"
    Environment = var.environment
  }
}
