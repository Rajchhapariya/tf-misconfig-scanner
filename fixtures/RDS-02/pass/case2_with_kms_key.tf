resource "aws_db_instance" "db" {
  instance_class    = "db.t3.micro"
  engine            = "postgres"
  storage_encrypted = true
  kms_key_id        = "arn:aws:kms:us-east-1:123456789012:key/sample-key"
}
