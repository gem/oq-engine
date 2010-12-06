# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
    Basic deployment script for openquake.
"""

import getpass
import sys

from fabric.api import env, run, sudo, cd
from fabric.state import output as fabric_output
from time import gmtime, strftime

# We really don't care about warnings.
fabric_output.warnings = False

# temporary
OPENQUAKE_DEMO_PKG_URL = "http://gemsun04.ethz.ch/geonode-client/temp/\
openquake-0.11.tar.gz"

@hosts('gemsun04.ethz.ch')
def server():
    """Restart redis-server and rabbitmq-server.

    Note: This function assumes rabbitmq and redis are already installed."""
    # Note: the target host of this deploy script should configure sudoer
    # privileges of env.user such that the following commands (such as 
    # rabbitmqctl, apt-get, etc.) can be run as sudo without a password.
    env.user = 'gemadmin'
    if not _pip_is_installed():
        _install_pip()

    redis = 'redis-server'
    rabbitmq = 'rabbitmq-server'
    
    # stop server processes
    _stop(redis)
    _stop(rabbitmq)

    # update the openquake package
    _install_openquake()

    # restart server processes
    _start(redis)
    _start(rabbitmq) 


@hosts('gemsun03.ethz.ch', 'gemsun04.ethz.ch')
def worker():
    """Update and restart celery.

    Note: This function assumes that celery is already installed and configured
    on the client."""
    
    env.user = 'gemadmin'
    if not _pip_is_installed():
        _install_pip()
    # kill celeryd processes
    _stop('celeryd')
    
    # update openquake package
    _install_openquake() 
    
    # restart celery
    _start('celeryd')

def _pip_is_installed():
    return _warn_only(run, 'which pip')

def _install_pip():
    _sudo_no_shell('apt-get install python-pip -y')

def _install_openquake():
    _sudo_no_shell('pip install openquake -f %s' % OPENQUAKE_DEMO_PKG_URL)

def _sudo_no_shell(command):
    sudo(command, shell=False)

def _start(service):
    """Start a service (as sudo) using its init script."""
    _sudo_no_shell('/etc/init.d/%s start' % service)

def _stop(service):
    """Stop a service (as sudo) using its init script."""
    _sudo_no_shell('/etc/init.d/%s stop' % service)

def development():
    """ Specify development hosts """
    env.user = getpass.getuser()
    env.hosts = ["localhost"] #"host1", "host2", "host3"]

def production():
    """ Specify production hosts """
    env.user = "deploy"
    env.hosts = ["productionhost1", "productionhost2",
                 "productionhost3", "productionhost4"]

def bootstrap(deploy_dir="/tmp/openquake/"):
    """ Bootstraps an environment for runtime """
    if not ls("%s/releases" % deploy_dir):
        run("mkdir -p %s/releases" % deploy_dir)

def deploy(git_url="git@github.com:gem/openquake.git",
           deploy_dir="/tmp/openquake/"):
    """ Deploy openquake to a series of hosts """

    if not env.hosts:
        usage()
        sys.exit()

    deploy_fmt = "%Y%m%d%H%M%S"
    deploy_timestamp = strftime(deploy_fmt, gmtime())

    with cd("%s/releases" % deploy_dir):
        # Clone into a timestamp file.
        run("git clone %s %s" % (git_url, deploy_timestamp))
        with cd(".."):
            if ls("current"):
                sudo("unlink current")
            sudo("ln -s releases/%s current" % deploy_timestamp)


def usage():
    print "OpenGEM deployment."
    print "To bootstrap run: fab [environment] bootstrap"
    print "To deploy run: fab [environment] deploy"
    print
    print "available environments:"
    print "development"
    print "production"

def ls(file):
    env.warn_only = True
    res = run("ls %s" % file)
    env.warn_only = False
    
    print type(res)

    return res
