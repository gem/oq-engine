import os
import sys
import pwd
import socket
import getpass
import subprocess
try:
    import venv
except ImportError:
    sys.exit('venv is missing! If you are on Ubuntu, please run '
             '`sudo apt install python3-venv`')

USER = 'openquake'
VENV = '/opt/openquake'
OQ_CFG = os.path.join(VENV, 'openquake.cfg')
OQ = '/usr/bin/oq'
DBSERVER_PORT = 1907


def before_checks():
    # check if there is a DbServer running
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        errcode = sock.connect_ex(('localhost', DBSERVER_PORT))
    finally:
        sock.close()
    if errcode == 0:  # no error, the DbServer is up
        sys.exit('There is DbServer running on port %d from a previous '
                 'installation. Please run `oq dbserver stop`' % DBSERVER_PORT)
    user = getpass.getuser()
    if user != 'root':
        sys.exit('Error: you cannot run this script unless you are root. If '
                 'you do not have root permissions, you can always install '
                 'the engine in single-user mode.')
    if sys.version_info[:2] < (3, 6):
        sys.exit('Error: you need at least Python 3.6, but you have %s' %
                 '.'.join(map(str, sys.version_info)))
    if os.path.exists(OQ) and os.readlink(OQ) != '%s/bin/oq' % VENV:
        sys.exit('Error: there is already a link %s->%s; please remove it' %
                 (OQ, os.readlink(OQ)))


def install():
    # create the openquake user if necessary
    try:
        pwd.getpwnam('openquake')
    except KeyError:
        subprocess.check_call(['useradd', USER])
        print('Created user %s' % USER)

    # create the openquake venv if necessary
    if not os.path.exists(VENV):
        # create venv
        venv.EnvBuilder(with_pip=True).create(VENV)
        print('Created %s' % VENV)

    # upgrade pip
    subprocess.check_call(['%s/bin/pip' % VENV, 'install', 'pip', 'wheel',
                           '--upgrade'])
    # install the engine
    subprocess.check_call(['%s/bin/pip' % VENV, 'install',
                           'openquake.engine', '--upgrade'])

    # create openquake.cfg
    if not os.path.exists(OQ_CFG):
        with open(OQ_CFG, 'w') as cfg:
            cfg.write('[dbserver]\nport = %d\n' % DBSERVER_PORT)
        print('Created %s' % OQ_CFG)

    # if the installation went correctly, create a symlink to oq
    if not os.path.exists(OQ):
        os.symlink('%s/bin/oq' % VENV, OQ)

    # start the DbServer
    subprocess.check_call(['%s/bin/oq' % VENV, 'dbserver', 'start'])


if __name__ == '__main__':
    before_checks()
    install()
