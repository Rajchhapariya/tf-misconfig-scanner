data "template_file" "rendered_policy" {
  template = "${file("${path.module}/policy.json")}"
}

resource "aws_iam_policy" "templated_policy" {
  name   = "templated-iam-policy"
  policy = data.template_file.rendered_policy.rendered
}
