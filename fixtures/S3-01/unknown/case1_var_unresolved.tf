variable "unresolved_block_flag" {
  type = bool
}

resource "aws_s3_bucket" "b" {
  bucket = "test-unknown-pab-bucket"
}

resource "aws_s3_bucket_public_access_block" "pab" {
  bucket                  = aws_s3_bucket.b.id
  block_public_acls       = var.unresolved_block_flag
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
