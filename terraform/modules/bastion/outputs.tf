output "bastion_public_ip" {
  value = aws_instance.bastion.public_ip
}
output "instance_public_dns" {
  description = "Public DNS of the bastion EC2 instance"
  value       = aws_instance.bastion.public_dns
}

output "bastion_sg_id" {
  description = "Security group ID for the bastion host"
  value = aws_security_group.bastion_sg.id
}