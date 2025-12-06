## Creates an ECS Cluster

resource "aws_ecs_cluster" "default" {
  name = "${var.service_name}_cluster"

  lifecycle {
    create_before_destroy = true
  }
}

## Creates an ECS Service running on Fargate
resource "aws_ecs_service" "default_service" {
  name                               = "${var.service_name}_service"
  cluster                            = aws_ecs_cluster.default.id
  task_definition                    = aws_ecs_task_definition.default_definition.arn
  desired_count                      = var.ecs_task_desired_count
  deployment_minimum_healthy_percent = var.ecs_task_deployment_minimum_healthy_percent
  deployment_maximum_percent         = var.ecs_task_deployment_maximum_percent
  launch_type                        = "FARGATE"

  load_balancer {
    target_group_arn = var.alb_target_group_arn
    container_name   = var.service_name
    container_port   = var.container_port
  }

  network_configuration {
    security_groups  = [var.ecs_sg_id, var.alb_security_group_id]
    subnets          = var.private_subnet_ids
    assign_public_ip = false
  }

  lifecycle {
    ignore_changes = [desired_count]
  }
}

## Creates ECS Task Definition
resource "aws_ecs_task_definition" "default_definition" {
  family                   = "${var.service_name}_task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  cpu    = var.cpu_units
  memory = var.memory

  container_definitions = jsonencode([
    {
      name      = var.service_name
      image     = "${var.ecr_repository_url}:${var.tag}"
      cpu       = var.cpu_units
      memory    = var.memory
      essential = true
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ],
      healthCheck = {
        command : [
          "CMD",
          "curl -f http://localhost:${var.container_port}/health | grep -q 'ok' || exit 1"
        ],
        interval    = 30
        retries     = 3
        timeout     = 5,
        startPeriod = 30
      }
      environment = [
        {
          name  = "PORT"
          value = tostring(var.container_port)
        }
      ],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name,
          "awslogs-region"        = var.logs_region,
          "awslogs-stream-prefix" = "${var.service_name}-log-stream-${var.environment}"
        }
      }
    }
  ])
}
## --------- IAM Roles for ECS Task Execution and Task Definition ---------


## IAM Role for ECS Task execution

resource "aws_iam_role" "ecs_task_execution_role" {
  name               = "${var.service_name}_ecs_task_execution_role_${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.task_assume_role_policy.json
}

data "aws_iam_policy_document" "task_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task_role" {
  name               = "${var.service_name}_ecs_task_role_${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.task_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_role_policy_rds" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonRDSFullAccess"
}


## --------- Other -------
resource "aws_cloudwatch_log_group" "ecs" {
  name = "ecs/${var.service_name}-${var.environment}"

}
