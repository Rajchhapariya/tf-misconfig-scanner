variable "custom_raw_policy" {
  type = string
}

resource "aws_iam_policy" "dynamic_policy" {
  name   = "dynamic-iam-policy"
  policy = var.custom_raw_policy
}
