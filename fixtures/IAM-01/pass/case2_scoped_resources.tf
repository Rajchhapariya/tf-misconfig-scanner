resource "aws_iam_policy" "bucket_admin" {
  name = "bucket-admin-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "*"
        Resource = "arn:aws:s3:::my-special-bucket/*"
      }
    ]
  })
}
