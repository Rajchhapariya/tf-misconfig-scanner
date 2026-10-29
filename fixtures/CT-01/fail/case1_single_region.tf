resource "aws_cloudtrail" "trail" {
  name                          = "single-region-trail"
  s3_bucket_name                = "audit-bucket"
  is_multi_region_trail         = false
  enable_log_file_validation    = true
}
