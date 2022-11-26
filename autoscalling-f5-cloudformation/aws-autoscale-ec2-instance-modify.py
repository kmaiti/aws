#!/usr/bin/env python
"""
Purpose : Extract next sequence number of auto-scaled instance and set new tag to self instance. Script will be running from new instance.
will take input from command line instead of from json file
Future Plan :
will associate instance to a role based IAM profile
Usage :
python ec2-autoscale-instance-modify.py  -a <your aws access_key> -s <aws secret key> -g <auto scale group that used in cloudformation file> -r <region> -n <min_server_number> -c <customer> -t <uat/plab/prod> -p <appname> -d <domainname ie example.net>
"""
__author__ = "kama maiti"
__copyright__ = "Copyright 2016, AWS autoscaled instance tag modification project"
__credits__ = ["kamal maiti"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "kamal maiti"
__email__ = "kamal.maiti@gmail.com"
__status__ = "production/Non-production"
import re
import argparse
import boto.ec2.autoscale
from boto.ec2 import EC2Connection
import shlex, subprocess

akey = ""
skey = ""
ag = ""
rg = ""
min_num = ""
def find_server_number(str):
    #Assuming first match only with consecutive three digits
    match = []
    match = re.findall(r'\d\d\d', str)
    if match:
        return match            #will return a list containg server number
    else:
        return match            #will return blank list
def main():
    arg_parser = argparse.ArgumentParser(description='Read autoscale instance')
    arg_parser.add_argument('-a', dest='akey',help='Provide AWS_ACCESS_KEY')
    arg_parser.add_argument('-s', dest='skey',help='Provide AWS_SECRET_ACCESS_KEY')
    arg_parser.add_argument('-g', dest='ag',help='Provide User provided autoscale group name')
    arg_parser.add_argument('-r', dest='rg',help='Provide region name')
    arg_parser.add_argument('-n', dest='min_num',help='Minimum Server name')
    arg_parser.add_argument('-c', dest='customer',help='Name of the customer in short')
    arg_parser.add_argument('-t', dest='servertype',help='Type of the server ie prod or uat or plab')
    arg_parser.add_argument('-p', dest='purpose',help='Purpose of the Server')
    arg_parser.add_argument('-d', dest='domain',help='Domain name that will be appended to server name')
    args = arg_parser.parse_args()
    #print(args)

    access_key = args.akey
    secret_key = args.skey
    region = args.rg
    group_name = str(args.ag)
    min_server_num = int(args.min_num)
    customer = str(args.customer)
    servertype = str(args.servertype)
    purpose = str(args.purpose)
    domain = str(args.domain)
    #created two objects below. One for autocale connection and another for ec2 instance
    as_conn = boto.ec2.autoscale.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    ec2_conn = boto.ec2.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    try:
        groups = as_conn.get_all_groups()
        all_groups = [group.name for group in groups]
        for g in all_groups:
            if group_name in g:                 #searching autocaling group that we are concerned with. Note all autoscalling group name should be unique
                FOUND_GROUP = g                 #FOUND_GROUP will save exact AG name. Note that exact AG name is not same as user provided name. It'll check if group_name is subset of g
        FOUND_GROUP_WITH_DES = as_conn.get_all_groups(names=[FOUND_GROUP])[0]
        instance_ids = [i.instance_id for i in FOUND_GROUP_WITH_DES.instances]
        #reservations = ec2_conn.get_all_instances(instance_ids)
        instances = ec2_conn.get_only_instances(instance_ids)
        #instances = [i for r in reservations for i in r.instances]
        lNameTag = []
        #collect all tags of all instances and sort Name tags and save them in list.
        for i,j in enumerate(instances):
            a = instances[i].tags
            lNameTag.append(a['Name'])
        #process each instances and take their server number in one list
        lServerNum = []
        if not lNameTag:                                        #checking if list is empty or not. If empty then this is first instance whose server num will be min_server_num
            next_number = min_server_num
        else:
            for server in lNameTag:                             #iterating each value of "Name" tag
                if not find_server_number(server):              #if method find_server_number returns null list
                    next_number = min_server_num
                else:
                    val = find_server_number(server)            #got value like [u'101']. Below comand will remove [],' and u
                    actual_num=str(val).strip('[]').strip('u').strip('\'')
                    lServerNum.append(int(actual_num))                           #actual_num is string, need to convert to int
        if not lServerNum:                                      #check if list of server number is blank or not
            next_number = min_server_num
        else:
            maximum_number = max(lServerNum)                     #used max function to find out maximum number in the list
            next_number = maximum_number + 1
        #Now we need to save this next_number in a file so that we can collect it and send to other commands.
        with open('/tmp/serverno','w') as fd:                   #created a file and save the number as string. Then read it and used later
            fd.write(str(next_number))
        with open('/tmp/serverno','r') as fd:
            num=fd.read()

        #Will modify tag of current instance. Let's build a new tag.
        delm = "-"                                              #Delimeter that will be used to join multiple string
        seq = ( customer, servertype, purpose, num, domain)     #created a tuple
        new_tag = delm.join(seq)                                #joined tuple strings
        with open('/tmp/nodename','w') as fd:
            fd.write(str(new_tag))

        #will extract current instance ID using curl. ie curl http://169.254.169.254/latest/meta-data/instance-id
        #
        cmd = 'curl http://169.254.169.254/latest/meta-data/instance-id'
        #shlex is simple lexical analyser for splitting a large string into tokens
        args = shlex.split(cmd)                                 #args will have value like : ['curl', 'http://169.254.169.254/latest/meta-data/instance-id']
        output,error = subprocess.Popen(args,stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()       #out and error are saved in variable. communicate will execute comamnd
        #o="i-fd96291f"                                         #used for testing
        cur_instance_reservation = ec2_conn.get_all_instances(instance_ids=output)
        cur_instance = cur_instance_reservation[0].instances[0]
        cur_instance.add_tag('Name', new_tag)

    finally:

        as_conn.close()
        ec2_conn.close()
if __name__ == '__main__':
    main()

