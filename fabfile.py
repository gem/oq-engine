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
