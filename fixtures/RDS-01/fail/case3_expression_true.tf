locals {
  is_exposed = true
}

resource "aws_db_instance" "db" {
  instance_class      = "db.t3.micro"
  engine              = "mariadb"
  publicly_accessible = local.is_exposed
}
