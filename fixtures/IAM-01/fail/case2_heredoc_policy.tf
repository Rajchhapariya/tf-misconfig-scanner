resource "aws_iam_role_policy" "role_admin" {
  name = "role-admin-policy"
  role = "admin-role"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}
EOF
}
