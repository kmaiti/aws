# SQS quque creation
resource "aws_sqs_queue" "my_sqs_queue" {
  name                      = "my_sqs_queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10

}
# sqs policy:
resource "aws_sqs_queue_policy" "test" {
  queue_url = aws_sqs_queue.my_sqs_queue.id

  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Id": "sqspolicy",
  "Statement": [
    {
      "Sid": "First",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "${aws_sqs_queue.my_sqs_queue.arn}",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "${var.sns_topic_arn}"
        }
      }
    }
  ]
}
POLICY
}

# Subscribe to sns
resource "aws_sns_topic_subscription" "sns_sends_to_sqs" {
  topic_arn = var.sns_topic_arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.my_sqs_queue.arn
}

