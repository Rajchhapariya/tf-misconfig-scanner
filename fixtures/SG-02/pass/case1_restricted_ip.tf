resource "aws_security_group" "sg" {
  name = "restricted-rdp-sg"
  ingress {
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["192.168.1.50/32"]
  }
}
