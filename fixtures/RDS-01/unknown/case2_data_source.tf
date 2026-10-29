data "aws_ssm_parameter" "db_exposure" {
  name = "/config/db_public"
}

resource "aws_db_instance" "db" {
  instance_class      = "db.t3.micro"
  engine              = "postgres"
  publicly_accessible = data.aws_ssm_parameter.db_exposure.value
}
