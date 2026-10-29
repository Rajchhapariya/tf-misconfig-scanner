resource "aws_s3_bucket" "b" {
  bucket = "public-read-write-bucket"
  acl    = "public-read-write"
}
