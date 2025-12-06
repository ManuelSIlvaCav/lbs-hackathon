## Creates one NAT Gateway per AZ

resource "aws_internet_gateway" "internet_gateway" {
  vpc_id = var.vpc_main_id

  tags = {
    Name = "igw_${var.environment}",
    Terraform = "true"
  }
}


## Creates one Elastic IP per AZ (one for each NAT Gateway in each AZ)

resource "aws_eip" "nat_gateway" {
  count  = var.enable_nat_gateway ? length(var.availability_zone_names) : 0
  domain = "vpc"
  tags = {
    Name = "eip_${count.index}_${var.environment}"
  }

}

/* If doing nat instance this is not nedeed */
resource "aws_nat_gateway" "nat_gateway" {
  count         = var.enable_nat_gateway ? length(var.availability_zone_names) : 0
  subnet_id     = var.public_subnets_ids[count.index] //aws_subnet.public[count.index].id
  allocation_id = aws_eip.nat_gateway[count.index].id

  tags = {
    Name = "nat_gateway_${count.index}_${var.environment}"
  }
}

