# lbaas-magic.py
# setup of nova, salt-master, etc for lbaas shenanigans
# to be run on a prospective salt-master
# This will:
#    configure the vm to be an lbaas-salt-master
#    run the appropriate salt-cloud mappings
#    set up the environment (secgroups, floating_ips, highstate, etc)
#    test the environment

###########
# imports
###########
import os
import ast
import sys
import time
import yaml
import logging
import argparse
import commands

##########
# parser
##########
parser = argparse.ArgumentParser(description='saltmagic.py - your gateway to the wonderful world of cloud-based lbaas')
parser.add_argument( '--verbose'
                   , action = 'count'
                   , dest = 'verbose'
                   , default = 0
                   , help = 'Controls internal output.  Utilize multiple times to increase output'
                   )
parser.add_argument( '--config'
                   , action = 'store'
                   , dest ='configfile'
                   , default = 'saltmagic.cfg'
                   , help = 'path to a config file containing options.  Command line options will supercede any options specified in the config'
                   )
parser.add_argument( '--create-saltmaster'
                   , action = 'store_true'
                   , dest = 'createsaltmaster'
                   , default = True
                   , help = 'Flag to signal if you need us to create the saltmaster vm for you.  Entails additional checks and setup steps'
                   )
parser.add_argument( '--delete-saltmaster'
                   , action = 'store_true'
                   , dest = 'deletesaltmaster'
                   , default = False
                   , help = 'Flag to signal if you need us to delete the saltmaster vm we create for you post-script'
                   )
parser.add_argument( '--os_username'
                   , action = 'store'
                   , dest ='osusername'
                   , default = None
                   , help = 'OpenStack username for the account that will own the saltmaster.'
                   )
parser.add_argument( '--os_tenant'
                   , action = 'store'
                   , dest ='ostenant'
                   , default = None
                   , help = 'OpenStack tenant name for the account that will own the saltmaster.'
                   )
parser.add_argument( '--os_password'
                   , action = 'store'
                   , dest ='ospassword'
                   , default = None
                   , help = 'OpenStack password for the account that will own the saltmaster.'
                   )

# functions
def report_nova_item(title, nova_item, logging, depth=1):
    """ Utility function for reporting info we receive from nova actions in a fancy manner :) """
    logging.info(title)
    indent = (' '*4)*depth
    for item in nova_item:
        for key, value in vars(item).items():
            if not key.startswith('_'):
                if type(value) is list:
                    logging.info("%s%s:" %(indent,key))
                    for list_item in value:
                        logging.info("%s%s" %(indent*2,list_item))
                elif type(value) is dict:
                    report_nova_item(key, value, logging, depth+1)
                else:
                    logging.info("%s%s: %s" %(indent,key, value))
        logging.info("")

######
# main
######
# configure logging
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y%m%d-%H%M%S %p', level=logging.INFO)

args = parser.parse_args(sys.argv[1:])
if args.verbose:
    logging.info("argument values:")
    for key, item in vars(args).items():
        logging.info("\t%s: %s" %(key, item))
if args.configfile:
    # We have a magic config file that we expect to be in key: value format
    # get our test input variants (nodes, names, etc)
    inputs_file = open(args.configfile,'r')
    saltmagic_inputs = yaml.load(inputs_file)
    inputs_file.close()
saltmaster_inputs = saltmagic_inputs['saltmaster_inputs']

print "Welcome to lbaas saltmagic, where we usher you into the wonderful world of tomorrow..."
time.sleep(.5)
print "Now on to business."
#sys.exit(0)

##############################
# create salt-master instance
##############################
if args.createsaltmaster:
    logging.info("Creating vm instance for salt-master: %s..." %saltmaster_inputs['saltmaster_name'])
    cmd = "nova --os-username='%s' --os-tenant-name='%s' --os-password='%s' --os-region-name='%s' --os-auth-url='%s' boot --flavor=%s --image=%s --key_name=%s --security_groups=%s %s" %( saltmaster_inputs['saltmaster_user']
                                      , saltmaster_inputs['saltmaster_tenant']
                                      , saltmaster_inputs['saltmaster_password']
                                      , saltmaster_inputs['saltmaster_region']
                                      , saltmaster_inputs['saltmaster_auth_url']
                                      , saltmaster_inputs['saltmaster_flavor']
                                      , saltmaster_inputs['saltmaster_image']
                                      , saltmaster_inputs['saltmaster_keypair']
                                      , saltmaster_inputs['saltmaster_secgroup']
                                      , saltmaster_inputs['saltmaster_name'])
    retcode, result = commands.getstatusoutput(cmd)
    logging.info(cmd)
    logging.info(retcode)
    logging.info("\n%s" %result)
    # get info:
    saltmaster_info = {}
    for line in result.split('\n')[3:-1]:
        data = line.split('|')
        key = data[1].strip()
        value = data[2].strip()
        saltmaster_info[key]=value
    if args.verbose:
        logging.info("preliminary saltmaster_info:")
        for key, value in saltmaster_info.items():
            logging.info("    %s: %s" %(key, value))
    ###################################
    # wait for salt-master to be ready
    ###################################
    logging.info("Waiting for instance to be in ACTIVE state...")
    saltmaster_ready = False
    attempts_remain = 120
    wait_time = 1
    while not saltmaster_ready and attempts_remain:
        cmd = "nova --os-username='%s' --os-tenant-name='%s' --os-password='%s' --os-region-name='%s' --os-auth-url='%s' show %s" %( saltmaster_inputs['saltmaster_user']
                                      , saltmaster_inputs['saltmaster_tenant']
                                      , saltmaster_inputs['saltmaster_password']
                                      , saltmaster_inputs['saltmaster_region']
                                      , saltmaster_inputs['saltmaster_auth_url']
                                      , saltmaster_info['id'])
        retcode, result = commands.getstatusoutput(cmd)
        for line in result.split('\n')[3:-1]:
            data = line.split('|')
            key = data[1].strip()
            value = data[2].strip()
            if key == 'status':
                if value == "ACTIVE":
                    saltmaster_ready=True
                else:
                    attempts_remain -= 1
                    logging.info("Node: %s, id: %s not in ACTIVE status.  Status: %s." %(saltmaster_inputs['saltmaster_name'], key, value))
                    logging.info("Waiting %d seconds.  %d attempts remain" %(wait_time, attempts_remain))
                    time.sleep(wait_time)
    if not saltmaster_ready:
        logging.error("Salt-master vm: %s, id: %s not ACTIVE in %d seconds.  Fail!" %(saltmaster_inputs['saltmaster_name'], saltmaster_info['id'], (attempts_remain*wait_time)))
        sys.exit(1)
    saltmaster_info = {}
    for line in result.split('\n')[3:-1]:
        data = line.split('|')
        key = data[1].strip()
        value = data[2].strip()
        saltmaster_info[key]=value
    if args.verbose:
        logging.info("saltmaster_info:")
        for key, value in saltmaster_info.items():
                logging.info("    %s: %s" %(key, value))
    saltmaster_ip = [ipaddr.strip() for ipaddr in saltmaster_info['private network'].split(',') if ipaddr.strip().startswith('15.')][0]
    logging.info("Saltmaster ip: %s" %saltmaster_ip)
    logging.info("Testing ssh readiness...")
    ssh_ready = False
    attempts_remain = 300
    wait_time = 1
    while not ssh_ready and attempts_remain:
        cmd = "fab -H %s check_ls" %saltmaster_ip
        retcode, result = commands.getstatusoutput(cmd)
        if args.verbose:
            logging.info(cmd)
            logging.info(retcode)
            logging.info(result)
        if retcode != 0:
            attempts_remain -= 1
            logging.info("saltmaster not yet ssh ready")
            logging.info("Waiting %d seconds.  %d attempts remain" %(wait_time, attempts_remain))  
            time.sleep(wait_time)
        else:
            ssh_ready=True
    if not ssh_ready:
        logging.error("Salt-master vm: %s, id: %s not ssh ready in %d seconds.  Fail!" %(saltmaster_inputs['saltmaster_name'], saltmaster_info['id'], (attempts_remain*wait_time)))
        sys.exit(1)
    logging.info("Salt-master ready for action!")

################################
# write a bootstrap pillar file
################################
bootstrap_pillar_file = 'bootstrap_pillar.sls'
logging.info("Writing bootstrap pillar file to %s" %bootstrap_pillar_file)
with open(bootstrap_pillar_file,'w') as outfile:
    for key, value in saltmagic_inputs['saltmaster_pillar'].items():
        if key == 'saltmaster_ip' and int(value) == 0:
            value = saltmaster_ip
        elif key == 'lbaas-saltmaster-id-rsa':
            value = '|\n    ' + value.replace('\n','\n    ')
        if args.verbose:
            logging.info( "    %s: %s" %(key, value))
        outfile.write("%s: %s\n" %(key, value))

########################
# configure salt-master
########################
logging.info("Starting saltmaster: %s bootstrap..." %saltmaster_inputs['saltmaster_name'])
cmd = "fab -H %s install_salt" %saltmaster_ip
retcode, result = commands.getstatusoutput(cmd)
logging.info(cmd)
logging.info(retcode)
logging.info("\n%s" %result)
###############################

logging.info("Installing salt-cloud...")
cmd = "fab -H %s install_salt_cloud" %saltmaster_ip
retcode, result = commands.getstatusoutput(cmd)
logging.info(cmd)
logging.info(retcode)
logging.info("\n%s" %result)

###############################
"""
# testing salt-cloud
logging.info("Starting test of salt-cloud on our master...")
cmd = "fab -H %s test_salt_cloud" %saltmaster_ip
retcode, result = commands.getstatusoutput(cmd)
logging.info(cmd)
logging.info(retcode)
logging.info("\n%s" %result)
logging.info("Taking a moment to bask in the results of our efforts...")
time.sleep(20)
"""
# call infrastructure mapping for salt-cloud
# this magic is handled in the in-repo salt-cloud deploy script
logging.info("Calling salt-cloud to deploy basic libra environment...")
cmd = "fab -H %s deploy_libra_env:%s,%s,%s,%s,%s,'/etc/salt/cloudconfigs/cloud_az3','/srv/lbaas-staging-salt/cloudmaps/basic_staging_az3.dat'" %(saltmaster_ip, saltmaster_inputs['saltmaster_user']
, saltmaster_inputs['saltmaster_tenant']
, saltmaster_inputs['saltmaster_password']
, saltmaster_inputs['saltmaster_region']
, saltmaster_inputs['saltmaster_auth_url'])

retcode, result = commands.getstatusoutput(cmd)
logging.info(cmd)
logging.info(retcode)
logging.info("\n%s" %result)

# test
################
# fin / cleanup
################
if args.deletesaltmaster:
    logging.info("Deleting vm instance for salt-master: %s..." %saltmaster_inputs['saltmaster_name'])
    cmd = "nova --os-username='%s' --os-tenant-name='%s' --os-password='%s' --os-region-name='%s' --os-auth-url='%s' delete %s" %( saltmaster_inputs['saltmaster_user']
                                      , saltmaster_inputs['saltmaster_tenant']
                                      , saltmaster_inputs['saltmaster_password']
                                      , saltmaster_inputs['saltmaster_region']
                                      , saltmaster_inputs['saltmaster_auth_url']
                                      , saltmaster_info['id'])
    retcode, result = commands.getstatusoutput(cmd)
    logging.info(cmd)
    logging.info(retcode)
    logging.info(result)
logging.info("Yay, we made it!")
