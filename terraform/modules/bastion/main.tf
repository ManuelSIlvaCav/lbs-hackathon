data "aws_ami" "latest_amazon_linux" {
    most_recent = true

    filter {
        name   = "name"
        values = ["al2023-ami-2023.*-arm64"] # Using ARM for cost optimization
    }

    filter {
        name   = "virtualization-type"
        values = ["hvm"]
    }

    owners = ["amazon"]
}


resource "aws_security_group" "bastion_sg" {
  name        = "${var.service_name}-bastion-sg"
  description = "Security group for the bastion host"
  vpc_id      = var.vpc_main_id
  # Allow SSH access from anywhere but can be restricted to specific IPs such as your office IP
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    #cidr_blocks = ["<your_office_ip>/32"] # Uncomment to restrict access
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}


# EC2 instance for the bastion host
resource "aws_instance" "bastion" {
  ami                    = data.aws_ami.latest_amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnets_ids[0]

  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.bastion_sg.id]
  user_data              = <<-EOF
              #!/bin/bash
              dnf update -y
              dnf install mariadb105 -y
            EOF
  tags                   = { Name = "bastion-host" }
}