variable "unresolved_multi_region" {
  type = bool
}

resource "aws_cloudtrail" "trail" {
  name                          = "unknown-trail-1"
  s3_bucket_name                = "audit-bucket"
  is_multi_region_trail         = var.unresolved_multi_region
  enable_log_file_validation    = true
}
