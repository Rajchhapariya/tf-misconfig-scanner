resource "aws_db_instance" "db" {
  instance_class    = "db.t3.micro"
  engine            = "mysql"
  storage_encrypted = true
}
