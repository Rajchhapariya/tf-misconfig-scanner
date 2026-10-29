variable "unresolved_ebs_enc" {
  type = bool
}

resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1a"
  size              = 10
  encrypted         = var.unresolved_ebs_enc
}
