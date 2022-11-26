#!/usr/bin/env python
"""
Purpose: Script runs as a webserver using flask framwork of python. It receives POST/GET requests from aws SNS through autoscale. As per instance launch and terminate, it addes/deletes IP of instance in F5 load balancer.
Future Plan :
Usage :
        python <script name>
                or
        you can run it through POSIX complient script.

Prerequisites :

1. make sure properties.py is exisiting in same directory where this script is placed.

Credit :
1. akashbhunchal :  For developing all basic functions
        https://github.com/akashbhunchal/AWSAutoScalingWithF5

Improvements has been done in this script :

1. Script uses btot3 instead of boto
2. All delete functions use ip_address that doesn't come from notification. Hence, added a list to save them and reuse IP of corresponding instance_id
3. Some logics has been changed in scale method.
4. Added some codes to acknowledge subscriptionconfirmation first time. These needs to executed separately as it didn't work in scale or may be I don't know to make it working.

"""
__author__ = "kama maiti"
__copyright__ = "Copyright 2016, BIG IP F5 pool modification using aws ec2 instance IP"
__credits__ = ["kamal maiti"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "kamal maiti"
__email__ = "kamal.maiti@gmail.com"
__status__ = "Production or Non-production"

from flask import Flask, request, json
import requests
#All details of properties.py are called by below
from properties import *
import datetime
#Will use Boto3 instead of boto as boto3 is advanced one. Boto is going to be deprecated. Boto3 is very easy to use.
import boto3
from boto3.session import Session
#for enabling standatrd logging mechanism
import logging

#Below variable can be used in furture to directly acknowledge Subscription
SUBCONMSG="SubscriptionConfirmation"

F5VERSION=metadata["f5version"]

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
#logger.info('Service is started')
#logger.info('Hello baby')
#logger.debug("this is debug message")
#logger.debug('%s iteration, item=%s', i, item)
#============== LOGGING setup =============

#Taking a dictionary for keeping instance ID and its IP address
INSTANCEID_IP={}

#Took one object of Flask class.
app = Flask(__name__)

#AWS SNS endpoint will be used like : http://<public_ip>/scale
#While sns json data will be posted to above URL, below method will be executed.

@app.route("/scale", methods=['POST','GET'])
def scale():
    '''
    #---- This code can be used to confirm subscriptiopn for aws sns http notification----#
    input_json = request.data
    data = json.loads(input_json)
    msgtype = data["Type"]
    token = data["Token"]
    topicarn = data["TopicArn"]
    session = Session(aws_access_key_id=metadata["access_key"], aws_secret_access_key=metadata["secret_key"],region_name=metadata["aws_region"])
    sns = session.resource('sns')
    client = sns.meta.client
    client.confirm_subscription(TopicArn=topicarn,Token=token,AuthenticateOnUnsubscribe="false")
    #-------- END -------------------------------------------#
    '''
    input_json = request.data

    #data dictionary has pythonic data that can be processed but child data in it needs to be changed to make pythonic style too. That's why json.loads is used again.
    data = json.loads(input_json)

    #autoscale notification contains dictionary which has "Message" key.
    input_message = json.loads(data["Message"])
    event = input_message["Event"]
    if "EC2InstanceId" in input_message:
        instance_id = input_message["EC2InstanceId"]
    else:
        instance_id = None
    as_group_name_from_sns = input_message["AutoScalingGroupName"]

    aws_region = metadata["aws_region"]
    as_group_name_from_config =  mapping["AG_NAME1"]
    if as_group_name_from_config is as_group_name_from_sns or as_group_name_from_config in as_group_name_from_sns:
        as_group_name = as_group_name_from_config

    #Create a session using aws credentials, this is boto3 style
    session = Session(aws_access_key_id=metadata["access_key"], aws_secret_access_key=metadata["secret_key"],region_name=metadata["aws_region"])
    ec2 = session.resource('ec2')
    if instance_id:
        current_instance = ec2.Instance(id=instance_id)
        ip_address =  current_instance.private_ip_address

        #Checkpoint to see if I receive data:
        logger.info("==============================================")
        logger.info("Triggered Event : %s", str(event))
        logger.info("Instance ID : %s", str(instance_id))
        logger.info("IP Address : %s", str(ip_address))
        logger.info("Auto scaling group name : %s" , str(as_group_name_from_sns))

    if event == metadata["launch_event"] and instance_id is not None:
        logger.info("Launch_event is triggered with instance ID %s  and IP address %s", str(instance_id), str(ip_address))
        INSTANCEID_IP[instance_id] = ip_address
        logger.info("Current list INSTANCEID_IP[called in launch_event section] : %s", str(INSTANCEID_IP))
        if _does_node_exist(ip_address):
            status, pool_names = _is_node_in_a_pool(ip_address)
            if status:
                _delete_member_from_pool(ip_address,pool_names)
            _delete_node(ip_address)
        else:
            _add_node(ip_address, as_group_name, instance_id)
            _add_member_to_pool(ip_address, as_group_name, instance_id)
            return "OK"

    elif event == metadata["terminate_event"] or metadata["launch_fail_event"] and instance_id is not None:
        #While terminate_event or launch_fail_event triggers, we don't receive IP address. We receive only instance ID.
        #Hence, we'll keep instanceID and IP in a dictionary during launching of instance.
        #Then will look up dictionary and get the IP that needs to be passed to delete functions below.
        logger.info("Current list INSTANCEID_IP[called in terminate section] : %s", str(INSTANCEID_IP))
        if INSTANCEID_IP:
            if instance_id in INSTANCEID_IP:
                ip_address = INSTANCEID_IP[instance_id]
                #Checkpoint to see if I receive IP address:
                logger.info("Either terminate or launch fail event is triggered, IP Address to be removed : %s", str(ip_address))
                if ip_address:
                    if _does_node_exist(ip_address):
                        status, pool_name = _is_node_in_a_pool(ip_address)
                        if status:
                            _delete_member_from_pool(ip_address,pool_name)
                        _delete_node(ip_address)
                        if not _does_node_exist(ip_address) and instance_id in INSTANCEID_IP:
                            #whatever instnce IP is deleted, we need to remove its key and value from dictionary INSTANCEID_IP too. That's why below line is added.
                            del INSTANCEID_IP[instance_id]
                            logger.debug("After deleting instance id %s and IP %s , current list looks : %s", str(instance_id),  str(ip_address), str(INSTANCEID_IP))
                            return "ok"
                    else:
                        #END OF if _does_node_exist(ip_address):
                        logger.debug("ip_address doesnt exists in F5 pool")
                        return "ip_address doesnt exists in F5 pool"
                else:
                    #END of if ip_address:
                    logger.debug("ip_address variable is blank")
                    return "ipaddress is blank"
            else:
                #End of if instance_id in INSTANCEID_IP:
                logger.debug("Instance ID %s is not present in list %s", str(instance_id),str(INSTANCEID_IP))
                return "instance id is not in list"
        else:
            #End of if INSTANCEID_IP:
            logger.debug("List name INSTANCEID_IP is blank")
            return "List INSTANCEID_IP is blank"
    else:
        #END of EVENT check up
        logger.debug("Event not handled")
        return "Event not handled"

    #####  END OF scale METHOD  #####


def _does_node_exist(ip_address):
    node_list = _get_node_list()
    for node in node_list:
        if node["address"] == ip_address or node.get("description") == ip_address:
            logger.debug("Called from function: _does_node_exist, IP address %s exists", str(ip_address))
            return True
    return False

def _get_node_list():
    url=metadata["base_url"] + "node?ver="+F5VERSION
    r = requests.get(url, headers=metadata["headers"],auth=(metadata["username"], metadata["password"]),verify=False)
    node_list = json.loads(r.text)["items"]
    logger.debug("Called from function: _get_node_list, returned node_list contains : %s ", str(node_list))
    return node_list

def _is_node_in_a_pool(ip_address):
    url=metadata["base_url"] + "pool?expandSubcollections=true"
    r = requests.get(url, headers=metadata["headers"],auth=(metadata["username"], metadata["password"]),verify=False)
    pools = json.loads(r.text)["items"]
    pool_names = []
    for pool in pools:
        members = pool["membersReference"].get("items")
        if members is not None:
            for member in members:
                if member["address"] == ip_address or member.get("description") == ip_address:
                    pool_names.append(pool["name"])
    if len(pool_names) == 0:
        logger.debug("Called from function: _is_node_in_a_pool, returned boolian and pool names values : %s , %s ", False, str(pool_names))
        return (False, None)
    else:
        logger.debug("Called from function: _is_node_in_a_pool, returned boolian and pool names values : %s , %s ", True, str(pool_names))
        return (True, pool_names)

def _delete_member_from_pool(ip_address,pool_names):
    for pool_name in pool_names:
        url=metadata["base_url"] + "pool/"+pool_name+"/members?ver="+F5VERSION
        r = requests.get(url, headers=metadata["headers"],auth=(metadata["username"], metadata["password"]),verify=False)
        members = json.loads(r.text)["items"]
        for member in members:
            if member["address"] == ip_address or member.get("description") == ip_address:
                self_link = member["selfLink"]
                split_url = self_link.split("/")
                part_url = split_url[len(split_url) -1]
                url = metadata["base_url"] + "pool/" + pool_name + "/members/" + part_url
                r = requests.delete(url, headers=metadata["headers"],auth=(metadata["username"], metadata["password"]),verify=False)
                logger.debug("Called from function: _delete_member_from_pool, deleted IP address %s from pool member %s ", str(ip_address), str(member))

def _delete_node(ip_address):
    node_list=_get_node_list()
    for node in node_list:
        if node["address"] == ip_address or node.get("description") == ip_address:
            self_link = node["selfLink"]
            split_url = self_link.split("/")
            part_url = split_url[len(split_url) -1]
            url = metadata["base_url"] +"node/" + part_url
            r = requests.delete(url, headers=metadata["headers"],auth=(metadata["username"], metadata["password"]),verify=False)
            logger.debug("Called from function: _delete_node, deleted IP address %s from node list", str(ip_address))

def _add_node(ip_address, as_group_name, instance_id):
    data={"name":ip_address,"partition":mapping[as_group_name]["node_attributes"]["partition"], "address":ip_address, "connectionLimit":mapping[as_group_name]["node_attributes"]["connectionLimit"], "dynamicRatio":mapping[as_group_name]["node_attributes"]["dynamicRatio"], "logging":mapping[as_group_name]["node_attributes"]["logging"], "monitor":mapping[as_group_name]["node_attributes"]["monitor"], "rateLimit":mapping[as_group_name]["node_attributes"]["rateLimit"], "ratio":mapping[as_group_name]["node_attributes"]["ratio"],"description":instance_id}
    url=metadata["base_url"] + "node?ver="+F5VERSION
    r = requests.post(url, data=json.dumps(data), headers=metadata["headers"],auth=(metadata["username"], metadata["password"]),verify=False)
    logger.debug("Called from function: _add_node, added IP address %s in node list", str(ip_address))

def _add_member_to_pool(ip_address, as_group_name, instance_id):
    data={"name":ip_address+":"+mapping[as_group_name]["node_attributes"]["port"], "description":instance_id}
    for pool in mapping[as_group_name]["pools"]:
        url=metadata["base_url"] + "pool/" + pool+"/members?ver="+F5VERSION
        r = requests.post(url, data=json.dumps(data), headers=metadata["headers"],auth=(metadata["username"], metadata["password"]),verify=False)
        logger.debug("Called from function: _add_member_to_pool, added IP address %s in pool member  %s ", str(ip_address), str(pool))


@app.route("/")
def hello():
    return "OK"

if __name__ == "__main__":

    #Run actual application
    app.run(host="0.0.0.0",debug=True,port=5000)

