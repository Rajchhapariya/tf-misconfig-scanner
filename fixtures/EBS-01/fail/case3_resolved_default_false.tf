variable "encrypt_volume" {
  type    = bool
  default = false
}

resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1b"
  size              = 50
  encrypted         = var.encrypt_volume
}
