resource "aws_kms_key" "key" {
  description         = "compliant-kms-key"
  enable_key_rotation = true
}
