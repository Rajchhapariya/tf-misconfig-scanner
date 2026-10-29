data "terraform_remote_state" "net" {
  backend = "local"
}

resource "aws_security_group" "sg" {
  name = "unknown-remote-rdp-sg"
}

resource "aws_security_group_rule" "rdp_state" {
  type              = "ingress"
  from_port         = 3389
  to_port           = 3389
  protocol          = "tcp"
  cidr_blocks       = [data.terraform_remote_state.net.outputs.vpn_cidr]
  security_group_id = aws_security_group.sg.id
}
