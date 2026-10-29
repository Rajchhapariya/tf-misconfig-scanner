resource "aws_cloudtrail" "trail" {
  name                          = "compliant-trail"
  s3_bucket_name                = "audit-bucket"
  is_multi_region_trail         = true
  enable_log_file_validation    = true
}
