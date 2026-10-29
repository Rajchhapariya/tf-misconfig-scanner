data "vault_generic_secret" "db" {
  path = "secret/db"
}

resource "aws_db_instance" "db" {
  instance_class = "db.t3.micro"
  engine         = "mysql"
  username       = "admin"
  password       = data.vault_generic_secret.db.data["password"]
}
