variable "bucket_acl_choice" {
  type = string
}

resource "aws_s3_bucket" "b" {
  bucket = "unknown-acl-bucket"
  acl    = var.bucket_acl_choice
}
