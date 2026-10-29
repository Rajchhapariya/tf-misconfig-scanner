resource "aws_cloudtrail" "trail" {
  name                          = "corporate-audit-trail"
  s3_bucket_name                = "sec-logs-bucket"
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  kms_key_id                    = "arn:aws:kms:us-east-1:123456789012:key/trail-key"
}
