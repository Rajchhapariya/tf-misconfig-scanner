resource "aws_s3_bucket" "b" {
  bucket = "log-bucket"
}

resource "aws_s3_bucket_acl" "b_acl" {
  bucket = aws_s3_bucket.b.id
  acl    = "log-delivery-write"
}
