from fabric.api import run, env, put, sudo, settings, cd
from fabric.contrib.files import append, comment
from fabric.context_managers import cd
import time

env.user = 'ubuntu'

def check_ls():
    run('ls')

def install_salt_ppa():
    run('sudo add-apt-repository -y ppa:saltstack/salt')
    run('sudo apt-get update')

def install_salt_master():
    run('sudo apt-get install -y salt-master')

def install_salt_minion():
    run('sudo apt-get install -y salt-minion')

def install_salt_cloud():
    run('sudo apt-get install python-pip python-m2crypto debconf-utils build-essential python-setuptools python-dev')
    run('sudo pip install pyzmq PyYAML pycrypto msgpack-python jinja2 psutil apache-libcloud salt-cloud')
    #run('sudo git clone -b 0.8.9 https://github.com/saltstack/salt-cloud.git ')
    #with cd('/home/ubuntu/salt-cloud'):
    #    run('sudo python setup.py install')

def install_git():
    run('sudo apt-get install -y git')

def clone_state_tree():
    run('sudo git clone https://github.com/pcrews/lbaas-salt.git /srv/lbaas-staging-salt')

def append_saltmaster_config():
    data = ['file_client: local'
           ,'file_roots:\n    stage:\n        - /srv/lbaas-staging-salt\n'
           ,'pillar_roots:\n    stage:\n        - /srv/lbaas-staging-pillar\n'
           ]
    append('/etc/salt/minion',data, use_sudo=True)
    append('/etc/salt/master',data, use_sudo=True)

def comment_saltmaster_topfile():
  # hacky method to ensure we don't apply logging on our test-monkey salt masters
  comment('/srv/lbaas-staging-salt/top.sls', '    - common_logging', use_sudo=True)

def copy_bootstrap_pillar():
    run('sudo mkdir /srv/lbaas-staging-pillar')
    put('top.sls', '/srv/lbaas-staging-pillar', use_sudo=True)
    put('bootstrap_pillar.sls', '/srv/lbaas-staging-pillar', use_sudo=True)

def check_state_tree():
    run('sudo ls -al /srv/lbaas-staging-salt')

def install_salt():
    install_salt_ppa()
    install_salt_master()
    install_salt_minion()
    install_git()
    #install_salt_cloud()
    clone_state_tree()
    check_state_tree()
    copy_bootstrap_pillar()
    append_saltmaster_config()
    comment_saltmaster_topfile()
    run('sudo salt-call state.highstate --local')
    run('sudo service salt-master restart')

def test_salt_cloud():
    run('sudo salt-cloud -P -C /etc/salt/cloudconfigs/cloud_az3 -m /srv/lbaas-staging-salt/cloudmaps/test_webservers_az3.dat -y')
    run('sudo salt \*web* state.highstate')
    run('sudo salt-cloud -C /etc/salt/cloudconfigs/cloud_az3 -m /srv/lbaas-staging-salt/cloudmaps/test_webservers_az3.dat -d -y')

def deploy_libra_env(os_user, os_tenant, os_pass, os_region, os_url, config_file_path, map_file_path):
    with cd('/srv/lbaas-staging-salt/scripts'):
        run('sudo python deploy_libra_env.py --os_user=%s --os_tenant=%s --os_password=%s --os_region=%s --os_auth_url=%s --salt-cloud-config=%s --salt-cloud-map=%s' %(os_user, os_tenant, os_pass, os_region, os_url, config_file_path, map_file_path))
