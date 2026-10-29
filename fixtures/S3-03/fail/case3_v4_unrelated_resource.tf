resource "aws_s3_bucket" "b" {
  bucket = "unencrypted-target-bucket"
}

resource "aws_s3_bucket_versioning" "v" {
  bucket = aws_s3_bucket.b.id
  versioning_configuration {
    status = "Enabled"
  }
}
