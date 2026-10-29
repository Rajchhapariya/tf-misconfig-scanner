variable "office_rdp_cidr" {
  type = string
}

resource "aws_security_group" "sg" {
  name = "unknown-rdp-sg"
  ingress {
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = [var.office_rdp_cidr]
  }
}
