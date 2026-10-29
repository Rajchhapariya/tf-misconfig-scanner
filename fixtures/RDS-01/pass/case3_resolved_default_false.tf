variable "public_db_flag" {
  type    = bool
  default = false
}

resource "aws_db_instance" "db" {
  instance_class      = "db.t3.micro"
  engine              = "oracle-ee"
  publicly_accessible = var.public_db_flag
}
