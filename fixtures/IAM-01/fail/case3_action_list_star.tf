resource "aws_iam_user_policy" "user_admin" {
  name = "user-admin-policy"
  user = "admin-user"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["*"]
        Resource = ["*"]
      }
    ]
  })
}
