resource "aws_s3_bucket" "b" {
  bucket = "unknown-v4-acl-bucket"
}

resource "aws_s3_bucket_acl" "b_acl" {
  bucket = aws_s3_bucket.b.id
  acl    = module.policy_loader.calculated_acl
}
