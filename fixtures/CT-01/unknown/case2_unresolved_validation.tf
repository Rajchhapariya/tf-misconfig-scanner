variable "unresolved_validation" {
  type = bool
}

resource "aws_cloudtrail" "trail" {
  name                          = "unknown-trail-2"
  s3_bucket_name                = "audit-bucket"
  is_multi_region_trail         = true
  enable_log_file_validation    = var.unresolved_validation
}
