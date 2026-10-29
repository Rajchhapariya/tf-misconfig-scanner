variable "unresolved_key_rotation" {
  type = bool
}

resource "aws_kms_key" "key" {
  description         = "unknown-rotation-key"
  enable_key_rotation = var.unresolved_key_rotation
}
