resource "aws_cloudtrail" "trail" {
  name           = "default-trail"
  s3_bucket_name = "audit-bucket"
}
