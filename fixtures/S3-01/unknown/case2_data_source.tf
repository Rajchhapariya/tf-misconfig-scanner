data "aws_ssm_parameter" "block_policy" {
  name = "/infra/s3/block_policy"
}

resource "aws_s3_bucket" "b" {
  bucket = "test-unknown-data-pab-bucket"
}

resource "aws_s3_bucket_public_access_block" "pab" {
  bucket                  = aws_s3_bucket.b.id
  block_public_acls       = true
  block_public_policy     = data.aws_ssm_parameter.block_policy.value
  ignore_public_acls      = true
  restrict_public_buckets = true
}
