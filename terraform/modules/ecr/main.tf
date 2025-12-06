## --------- ECR Repository ---------
resource "aws_ecr_repository" "ecr" {
  name                 = var.ecr_repository_name
  force_delete         = true
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "main" {
  repository = aws_ecr_repository.ecr.name

  policy = jsonencode({
    "rules":[
        {
            "rulePriority"      : 1,
            "description"       : "Expire images older than 30 days",
            "selection": {
                "tagStatus"     : "any",
                "countType"     : "sinceImagePushed",
                "countUnit"     : "days",
                "countNumber"   : 30
            },
            "action": {
                "type"          : "expire"
            }
        }
    ]
  })
}