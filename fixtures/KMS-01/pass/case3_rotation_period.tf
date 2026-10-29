resource "aws_kms_key" "key" {
  description              = "compliant-period-key"
  enable_key_rotation      = true
  rotation_period_in_days  = 90
}
