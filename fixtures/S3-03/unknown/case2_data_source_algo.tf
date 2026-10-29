data "aws_ssm_parameter" "sse_algo" {
  name = "/platform/s3/sse_algorithm"
}

resource "aws_s3_bucket" "b" {
  bucket = "unknown-v4-sse-algo-from-ssm"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sse" {
  bucket = aws_s3_bucket.b.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = data.aws_ssm_parameter.sse_algo.value
    }
  }
}
