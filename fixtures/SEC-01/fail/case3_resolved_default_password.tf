variable "db_password" {
  type    = string
  default = "ProductionSecretPass!99"
}

resource "aws_db_instance" "db" {
  instance_class = "db.t3.micro"
  engine         = "postgres"
  username       = "dbadmin"
  password       = var.db_password
}
