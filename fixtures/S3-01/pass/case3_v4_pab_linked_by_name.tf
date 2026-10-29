resource "aws_s3_bucket" "b" {
  bucket = "secure-corporate-logs"
}

resource "aws_s3_bucket_public_access_block" "pab" {
  bucket                  = "secure-corporate-logs"
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
