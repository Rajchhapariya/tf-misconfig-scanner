resource "aws_kms_key" "key" {
  description         = "key-without-rotation"
  enable_key_rotation = false
}
