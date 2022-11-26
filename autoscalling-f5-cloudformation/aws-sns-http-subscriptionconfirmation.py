#!/usr/bin/env python
"""
Purpose: Script will be used to confirm aws sns http subscription. This works as webserver using python Flask framework
Future Plan :
  - will associate instance to a role based IAM profile
Usage :
python <scriptname>

Prerequisites:
 - make sure properties.py file has required content
 - Port used in run section should be accessible from AWS region
 - Post json based http post/get data

"""
__author__ = "kama maiti"
__copyright__ = "Copyright 2016, AWS SNS CONFIRM HTTP SUBSCRIPTION"
__credits__ = ["kamal maiti"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "kamal maiti"
__email__ = "kamal.maiti@gmail.com"
__status__ = "Production or Non-production"

from flask import Flask, request, json
#All details of properties.py are called by below
from properties import *
#Will use Boto3 instead of boto as boto3 is advanced one. Boto is going to be deprecated. Boto3 is very easy to use.
import boto3
from boto3.session import Session
import logging

#============== LOGGING setup =============
LOG=metadata["logfile"]
#Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# create a file handler
handler = logging.FileHandler(LOG)
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter(FORMAT, datefmt='%d/%m/%Y %I:%M:%S %p')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)
#EXAMPLE :
#logger.info('Service is started')
#logger.info('Hello baby')
#logger.debug("this is debug message")
#logger.debug('%s iteration, item=%s', i, item)
#============== LOGGING setup =============

#Took one object of Flask class.
app = Flask(__name__)
#AWS SNS endpoint will be used like : http://<public_ip>/scale
#While sns json data will be posted to above URL, below method will be executed.
@app.route("/scale", methods=['POST','GET'])
def scale():
    #---- This code can be used to confirm subscriptiopn for aws sns http notification----#
    input_json = request.data
    data = json.loads(input_json)
    msgtype = data["Type"]
    token = data["Token"]
    topicarn = data["TopicArn"]
    logger.debug("Received Token : %s",str(token))
    logger.debug("Received TopicArn : %s", str(topicarn))
    session = Session(aws_access_key_id=metadata["access_key"], aws_secret_access_key=metadata["secret_key"],region_name=metadata["aws_region"])
    sns = session.resource('sns')
    client = sns.meta.client
    response=client.confirm_subscription(TopicArn=topicarn,Token=token,AuthenticateOnUnsubscribe="false")
    logger.debug("Confirmed http sns subscription with following response :")
    logger.debug("%s",str(response))
    #-------- END -------------------------------------------#
@app.route("/")
def hello():
    return "OK"

if __name__ == "__main__":

    #Run actual application
    app.run(host="0.0.0.0",debug=True,port=5000)    
