variable "multi_region" {
  type    = bool
  default = true
}

variable "log_validation" {
  type    = bool
  default = true
}

resource "aws_cloudtrail" "trail" {
  name                          = "compliant-var-trail"
  s3_bucket_name                = "audit-bucket"
  is_multi_region_trail         = var.multi_region
  enable_log_file_validation    = var.log_validation
}
