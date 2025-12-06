output "alb_security_group_id" {
  value = aws_security_group.alb.id
}

output "alb_target_group_arn" {
  value = aws_alb_target_group.service_target_group.arn
}
