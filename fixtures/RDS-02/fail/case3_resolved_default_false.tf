variable "encrypt_storage_flag" {
  type    = bool
  default = false
}

resource "aws_db_instance" "db" {
  instance_class    = "db.t3.micro"
  engine            = "mysql"
  storage_encrypted = var.encrypt_storage_flag
}
