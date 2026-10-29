resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1a"
  size              = 20
}
