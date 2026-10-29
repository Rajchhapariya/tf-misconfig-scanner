resource "aws_s3_bucket" "b" {
  bucket = "public-read-bucket"
  acl    = "public-read"
}
