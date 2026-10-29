variable "rotate_kms_keys" {
  type    = bool
  default = true
}

resource "aws_kms_key" "key" {
  description         = "compliant-var-key"
  enable_key_rotation = var.rotate_kms_keys
}
