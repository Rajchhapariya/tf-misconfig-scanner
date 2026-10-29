variable "public_db_flag" {
  type    = bool
  default = true
}

resource "aws_db_instance" "db" {
  instance_class      = "db.t3.micro"
  engine              = "postgres"
  publicly_accessible = var.public_db_flag
}
