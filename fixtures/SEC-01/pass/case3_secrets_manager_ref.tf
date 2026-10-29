data "aws_secretsmanager_secret_version" "creds" {
  secret_id = "prod/db/credentials"
}

resource "aws_db_instance" "db" {
  instance_class = "db.t3.micro"
  engine         = "mysql"
  username       = "admin"
  password       = data.aws_secretsmanager_secret_version.creds.secret_string
}
