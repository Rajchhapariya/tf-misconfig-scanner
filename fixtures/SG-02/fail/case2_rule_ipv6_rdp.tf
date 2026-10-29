resource "aws_security_group" "sg" {
  name = "open-rdp-rule"
}

resource "aws_security_group_rule" "rdp_rule" {
  type              = "ingress"
  from_port         = 3389
  to_port           = 3389
  protocol          = "tcp"
  ipv6_cidr_blocks  = ["::/0"]
  security_group_id = aws_security_group.sg.id
}
