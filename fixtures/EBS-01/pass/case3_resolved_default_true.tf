variable "encrypt_volume" {
  type    = bool
  default = true
}

resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1c"
  size              = 80
  encrypted         = var.encrypt_volume
}
