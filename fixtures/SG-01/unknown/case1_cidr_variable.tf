variable "remote_admin_cidr" {
  type = string
}

resource "aws_security_group" "sg" {
  name = "unknown-cidr-ssh-sg"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.remote_admin_cidr]
  }
}
