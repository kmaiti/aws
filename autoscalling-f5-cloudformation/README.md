## AWS Autoscalling with BiG IP F5, Cloudformation, SNS, Dynamic Server name & Puppet

- This project includes complete integration of **AWS Auto Scaling with Big IP F5 through CloudFormation and SNS**. 
- While Autoscale is used with ELB of AWS, it works fine but due to limitation of ELB, Big IP F5 service is used now a days as a replacement. It is a big challenge to modify load balancer pool using autoscaling instance IP. This project overcomes this.
- SNS http endpoint notification goes to python based app server and it processes IP and instance ID. Then it addes/deletes IP in/from desired LOAD BALANCER POOL.
- aws-autoscale-ec2-instance-modify.py script is responsible to make sure to increase sequence number of node. It sets TAG and hostname accordingly. 

## Code 
- View all scripts and get idea. Most of them has notes to understand them.

## Motivation
-  Due to limitation of AWS loadbalancer, F5 is used sometimes. In order to integrate autoscale with Big IP F5, IP of the instance needs to be added or removed dynamically in pool. [Akash Bhunchal](https://github.com/akashbhunchal/AWSAutoScalingWithF5/) has already developed base functions but during testing I observed that few important functions are not working due to missing input or some reasons. Hence, I had to rectify those areas. I added more concise logics, logging mechanism, boto3 etc.
- Auto scaling resource is created through cloudformation to make auto scale deploy automated. You have to change endpoint notification section too.
- SNS notification is also added. It may not work with CF, better you can manually setup SNS.
- One script will acknowledge sns http subscription.
- Puppet client section is added in cloudformation file to integtate and control node through puppet server.
- For puppet master setup, you can follow [this link](https://github.com/kmaiti/automation/blob/master/util-puppetmaster.json)


## Installation
1. Following files are required to complete the setup for autoscaling with F5 using cloudformation 
```
aws-autoscale-ec2-instance-modify.py
aws-autoscale-with-f5-cf-v2.json
aws-autoscaling-with-f5-app.py
aws-sns-http-endpoint.json
aws-sns-http-subscriptionconfirmation.py
properties.py
```
2. Setup a linux machine which is publically accessible. Bind a public IP in it. 
3. Make sure port mentioned in app script[aws-autoscaling-with-f5-app.py] is accessible from AWS region from where sns http notification will come
4. Put proper values in properties.py
5. Run script aws-sns-http-subscriptionconfirmation.py to acknowledge subscription.
6. Now setup sns with http endpoint. Use above public IP. It will be like *`http://publicIP/scale`*
7. Once subscription is confirmed, it will look like ![alt text](subscription.jpg?raw=true "this") in aws console.
8. Stop aws-sns-http-subscriptionconfirmation.py now.
9. Run aws-autoscaling-with-f5-app.py. If you want to run app in different port, please modify this script accordingly.
10. Put script aws-autoscale-ec2-instance-modify.py in AMI and change AMI ID in CF script. Python should be pre-installed in AMI. Note down the path of script.
11. Modify necessary parameters in aws-autoscale-with-f5-cf-v2.json.
12. Deploy autoscale using aws-autoscale-with-f5-cf-v2.json. 
13. Take look in app log file to see progress.

## API Reference

- boto3
- Flask
- requests

## Tests

- Sequence of auto scalled nodes in AWS will look like ![alt text](3.jpg?raw=true)
- If you run application in debug mode, output will look whatever is mentioned in file `app-output-in-debug-mode.txt`
- While node will be added in F5 will, it will look like ![alt text](node-added-in-f5.jpg?raw=true "this")
- While two nodes are added, F5 console looks ![alt text](two-nodes-added-in-f5-pool.jpg?raw=true "this")


## Contributors
- Akash Bhunchal : 
   - For developing Big IP F5 integration script as mentioned above.
- Kamal Maiti : 
    - Improved Big IP F5 integration script a lot, Enabled logging, deletion function etc.
    - Created Cloudformation script for autoscale
    - Created aws-autoscale-ec2-instance-modify
    - Created aws-sns-http-endpoint.json for sns setup
    - created aws-sns-http-subscriptionconfirmation.py for acknowledging subscription-confirmation

## License

GPLV3 , [refer this for more detail](https://github.com/kmaiti/AWSAutoScalingWithF5andCloudFormation/blob/master/LICENSE).
