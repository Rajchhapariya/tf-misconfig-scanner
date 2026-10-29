variable "unresolved_db_public" {
  type = bool
}

resource "aws_db_instance" "db" {
  instance_class      = "db.t3.micro"
  engine              = "mysql"
  publicly_accessible = var.unresolved_db_public
}
