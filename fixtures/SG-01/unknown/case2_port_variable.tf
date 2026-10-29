variable "dynamic_ingress_port" {
  type = number
}

resource "aws_security_group" "sg" {
  name = "unknown-port-sg"
  ingress {
    from_port   = var.dynamic_ingress_port
    to_port     = var.dynamic_ingress_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
