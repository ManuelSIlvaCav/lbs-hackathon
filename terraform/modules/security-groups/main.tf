## Security Group for ECS Task Container Instances (managed by Fargate)

resource "aws_security_group" "ecs_sg" {
  name        = "${var.service_name}_ecs_sg_${var.environment}"
  description = "Security group for ECS task running on Fargate"
  vpc_id      = var.vpc_id
  revoke_rules_on_delete      = true

  ingress {
    description     = "Allow ingress traffic from ALB on HTTP only"
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [var.alb_security_group_id]
    self            = true
  }

  egress {
    description                 = "Allow outbound traffic from ECS"
    from_port                   = 0
    to_port                     = 0
    protocol                    = -1
    cidr_blocks                 = ["0.0.0.0/0"]
    self                        = true
  }
}
