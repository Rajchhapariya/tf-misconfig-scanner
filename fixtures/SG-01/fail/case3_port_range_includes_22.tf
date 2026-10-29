resource "aws_security_group" "sg" {
  name = "open-range-sg"
  ingress {
    from_port   = 20
    to_port     = 25
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
