metadata={
        "headers":{'Content-Type':'application/json'},
        "base_url":"https://<publicip>/mgmt/tm/ltm/", #publicip
        "username":"f5login",	#replace it
        "password":"f5password",  #replace it
        "f5version":"11.6.0",
	"TopicArn":"<sns_topic_arn>",
        "launch_event":"autoscaling:EC2_INSTANCE_LAUNCH",
        "launch_fail_event":"autoscaling:EC2_INSTANCE_LAUNCH_ERROR",
        "terminate_event":"autoscaling:EC2_INSTANCE_TERMINATE",
        "access_key":"XXXX",  #replace it
        "secret_key":"XXXX", #replace it
        "aws_region":"sa-east-1",
        "aws_region_ec2_endpoint":"ec2.sa-east-1.amazonaws.com"
	"loglevel":"DEBUG",
        "logfile":"/tmp/autoscale.log"
}



mapping={
"AG_NAME1":"XXXXtest123",	#autoscalinggroup name ie used in aws or in cloudformation
"XXXXtest123":{ # autoscalinggroup name ie used in aws or in cloudformation
        "pools":["AUTOSCALE-TESTING-80"],
        "node_attributes":{
                "partition":"Common",
                "connectionLimit":0,
                "dynamicRatio":1,
                "logging":"disabled",
                "monitor":"default",
                "rateLimit":"disabled",
                "ratio":1,
                "port":"80"
                }
        }
}

