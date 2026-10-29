resource "aws_s3_bucket" "b" {
  bucket = "unknown-v4-sse-bucket"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sse" {
  bucket = aws_s3_bucket.b.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = module.shared_kms.key_arn
    }
  }
}
