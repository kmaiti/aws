resource "aws_sns_topic" "my_sns_topic" {
  name            = "my_sns_topic"
  delivery_policy = <<EOF
{
  "http": {
    "defaultHealthyRetryPolicy": {
      "minDelayTarget": 20,
      "maxDelayTarget": 20,
      "numRetries": 3,
      "numMaxDelayRetries": 0,
      "numNoDelayRetries": 0,
      "numMinDelayRetries": 0,
      "backoffFunction": "linear"
    },
    "disableSubscriptionOverrides": false,
    "defaultThrottlePolicy": {
      "maxReceivesPerSecond": 1
    }
  }
}
EOF
}
resource "aws_sns_topic_policy" "default" {
  arn = aws_sns_topic.my_sns_topic.arn

  policy = data.aws_iam_policy_document.sns_topic_policy.json
}

data "aws_iam_policy_document" "sns_topic_policy" {
  policy_id = "MyTopicSubscribePolicy"

  statement {
    sid = "Allow-other-account-to-subscribe-to-topic"
    principals {
      type        = "AWS"
      identifiers = ["${var.aws_acc_of_sqs}"]
    }
    effect = "Allow"
    actions = [
      "SNS:Subscribe",
    ]
    resources = [
      aws_sns_topic.my_sns_topic.arn,
    ]

  }
}
