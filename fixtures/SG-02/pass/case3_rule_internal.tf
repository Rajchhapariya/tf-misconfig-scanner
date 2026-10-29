resource "aws_security_group" "sg" {
  name = "internal-rdp-sg"
}

resource "aws_security_group_rule" "rdp_internal" {
  type              = "ingress"
  from_port         = 3389
  to_port           = 3389
  protocol          = "tcp"
  cidr_blocks       = ["10.1.0.0/16"]
  security_group_id = aws_security_group.sg.id
}
