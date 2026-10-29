resource "aws_s3_bucket" "b" {
  bucket = "private-bucket"
  acl    = "private"
}
