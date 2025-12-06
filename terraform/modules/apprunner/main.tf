resource "aws_iam_role" "apprunnerroles" {
  name = "apprunnerroles"
  assume_role_policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service":  [
                  "build.apprunner.amazonaws.com",
                  "tasks.apprunner.amazonaws.com"
                ]
            },
            "Action": "sts:AssumeRole"
        }
    ]
})
}

resource "aws_iam_role_policy_attachment" "myrolespolicy" {
  role = aws_iam_role.apprunnerroles.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

// Wait for other resources to be created if needed
resource "time_sleep" "waitrolecreate" {
  depends_on = [aws_iam_role.apprunnerroles]
  create_duration = "60s"
}

resource "aws_apprunner_auto_scaling_configuration_version" "app-runner-config" {                            
  auto_scaling_configuration_name = "app-runner-config"
  # scale between 1-5 containers
  min_size = 1
  max_size = 1
}

resource "aws_apprunner_service" "demo-app-runner" {
  depends_on = [time_sleep.waitrolecreate]                 
  service_name = "demo-app-runner"
  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.app-runner-config.arn

  source_configuration {
    authentication_configuration {
      access_role_arn = "${aws_iam_role.apprunnerroles.arn}"
    }
    image_repository {
      image_identifier      = "${var.ecr_repository_url}:latest"
      image_repository_type = "ECR"
      image_configuration {
        port = 80
      }
    }
    auto_deployments_enabled = true
  }
}