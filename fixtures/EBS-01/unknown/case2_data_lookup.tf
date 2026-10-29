data "external" "volume_flags" {
  program = ["python", "-c", "import sys, json; json.dump({'encrypted': 'true'}, sys.stdout)"]
}

resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1a"
  size              = 15
  encrypted         = data.external.volume_flags.result.encrypted
}
