resource "aws_cloudtrail" "trail" {
  name                          = "no-log-validation-trail"
  s3_bucket_name                = "audit-bucket"
  is_multi_region_trail         = true
  enable_log_file_validation    = false
}
