variable "unresolved_sse_algo" {
  type = string
}

resource "aws_s3_bucket" "b" {
  bucket = "unknown-sse-bucket"
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = var.unresolved_sse_algo
      }
    }
  }
}
