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
OQL = ['sudo', '-H', '-u', USER, OQ]
OQDATA = '/var/lib/openquake/oqdata'
DBPATH = os.path.join(OQDATA, 'db.sqlite3')
DBSERVER_PORT = 1907
CONFIG = '''[dbserver]
port = %d
multi_user = true
file = %s
shared_dir = /var/lib
''' % (DBSERVER_PORT, DBPATH)
PACKAGES = '''It looks like you have an installation from packages.
Please remove it with `sudo apt remove python3-oq-engine`
on Debian derivatives or with `sudo yum remove python3-oq-engine`
on Red Hat derivatives. If it does not work, just remove everything with
sudo rm -rf /opt/openquake /etc/openquake/openquake.cfg /usr/bin/oq
'''
SERVICE = '''\
[Unit]
Description=The OpenQuake Engine {service}
Documentation=https://github.com/gem/oq-engine/
After=network.target

[Service]
User=openquake
Group=openquake
Environment=
WorkingDirectory={OQDATA}
ExecStart=/opt/openquake/bin/oq {service} start
Restart=always
RestartSec=30
KillMode=control-group
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
'''


def before_checks():
    # check platform
    if sys.platform != 'linux':
        sys.exit('Error: this installation method is meant for linux!')

    # check python version
    if sys.version_info[:2] < (3, 6):
        sys.exit('Error: you need at least Python 3.6, but you have %s' %
                 '.'.join(map(str, sys.version_info)))

    # check if there is a DbServer running
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        errcode = sock.connect_ex(('localhost', DBSERVER_PORT))
    finally:
        sock.close()
    if errcode == 0:  # no error, the DbServer is up
        sys.exit('There is DbServer running on port %d from a previous '
                 'installation. Please run `oq dbserver stop`. '
                 'If it does not work, try `sudo fuser -k %d/tcp`' %
                 (DBSERVER_PORT, DBSERVER_PORT))

    # check if there is an installation from packages
    if os.path.exists('/etc/openquake/openquake.cfg'):
        sys.exit(PACKAGES)

    user = getpass.getuser()
    if user != 'root':
        sys.exit('Error: you cannot run this script unless you are root. If '
                 'you do not have root permissions, you can always install '
                 'the engine in single-user mode.')
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

    # create the database
    if not os.path.exists(OQDATA):
        os.makedirs(OQDATA)
        subprocess.check_call(['chown', USER, OQDATA])

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
            cfg.write(CONFIG)
        print('Created %s' % OQ_CFG)

    # create symlink to oq
    if not os.path.exists(OQ):
        os.symlink('%s/bin/oq' % VENV, OQ)

    # create systemd services
    for service in ['dbserver', 'webui']:
        service_name = 'openquake-%s.service' % service
        service_path = '/lib/systemd/system/' + service_name
        with open(service_path, 'w') as f:
            f.write(SERVICE.format(OQDATA=OQDATA, service=service))
        subprocess.check_call(['systemctl', 'enable', service_name])
        subprocess.check_call(['systemctl', 'start', service_name])


if __name__ == '__main__':
    before_checks()
    install()
