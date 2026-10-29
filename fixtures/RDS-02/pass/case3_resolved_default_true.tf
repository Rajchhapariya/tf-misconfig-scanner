variable "encrypt_storage_flag" {
  type    = bool
  default = true
}

resource "aws_db_instance" "db" {
  instance_class    = "db.t3.micro"
  engine            = "mariadb"
  storage_encrypted = var.encrypt_storage_flag
}
