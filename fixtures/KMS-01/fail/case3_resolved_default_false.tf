variable "rotate_kms_keys" {
  type    = bool
  default = false
}

resource "aws_kms_key" "key" {
  description         = "key-var-false"
  enable_key_rotation = var.rotate_kms_keys
}
