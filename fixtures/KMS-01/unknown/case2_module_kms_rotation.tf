resource "aws_kms_key" "key" {
  description         = "unknown-module-key"
  enable_key_rotation = module.kms_policy.rotation_enabled
}
