## Basic commands

> terraform plan

## Setup different terraform users

Read the values of the aws credential file

> nano ~/.aws/credentials

To set a different user

> export AWS_PROFILE=<name>

Example

> export AWS_PROFILE=oikoflow-integration-user

## Infracost

Infracost is a service that allows to calculate approximately the cost of the infrastructure being deployed with terraform. ex

> infracost breakdown --show-skipped --path .


## Terraform configs

Prod-simple env is a simple deployment with app runners exposed for easy testing and for product start

Prod is a more scalable solution with ecs deployments with a load balancer when transitioning is a simple way to evolve the platform



# Connect to Production database

1. Get the public key used for the bastion .pem file
2. Establish an ssh connection to the DNS or public IP of an ec2 instance. (This has to be located on a public subnet)
3. Use this as a tunnel to connect to the RDS database.