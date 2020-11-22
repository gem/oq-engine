import os
import sys
import pwd
import socket
import getpass
import argparse
import subprocess
from urllib.request import urlopen
try:
    import venv
except ImportError:
    sys.exit('venv is missing! If you are on Ubuntu, please run '
             '`sudo apt install python3-venv`')


class server:
    """
    Parameters for a server installation (with root permissions)
    """
    VENV = '/opt/openquake'
    OQ_CFG = os.path.join(VENV, 'openquake.cfg')
    OQ = '/usr/bin/oq'
    OQL = ['sudo', '-H', '-u', 'openquake', OQ]
    OQDATA = '/var/lib/openquake/oqdata'
    DBPATH = os.path.join(OQDATA, 'db.sqlite3')
    DBPORT = 1907
    CONFIG = '''[dbserver]
    port = %d
    multi_user = true
    file = %s
    shared_dir = /var/lib
    ''' % (DBPORT, DBPATH)


class user:
    """
    Parameters for a user installation
    """
    VENV = os.path.expanduser('~/openquake')
    OQ_CFG = os.path.join(VENV, 'openquake.cfg')
    OQ = os.path.join(VENV, '/bin/oq')
    OQDATA = os.path.expanduser('~/oqdata')
    DBPATH = os.path.join(OQDATA, 'db.sqlite3')
    DBPORT = 1908
    CONFIG = ''


class devel(user):
    """
    Parameters for a devel installation (same as user)
    """


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

PYVER = sys.version_info[:2]


def before_checks(inst):
    # check python version
    if PYVER < (3, 6):
        sys.exit('Error: you need at least Python 3.6, but you have %s' %
                 '.'.join(map(str, sys.version_info)))

    # check platform
    if inst is server and sys.platform != 'linux':
        sys.exit('Error: this installation method is meant for linux!')

    # check user
    user = getpass.getuser()
    if inst is server and user != 'root':
        sys.exit('Error: you cannot perform a server installation unless '
                 'you are root. If you do not have root permissions, you '
                 'can install the engine in user mode.')
    elif user == 'root':
        sys.exit('Error: you cannot perform a user or devel installation'
                 ' as root.')

    # check if there is a DbServer running
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        errcode = sock.connect_ex(('localhost', inst.DBPORT))
    finally:
        sock.close()
    if errcode == 0:  # no error, the DbServer is up
        sys.exit('There is DbServer running on port %d from a previous '
                 'installation. Please run `oq dbserver stop`. '
                 'If it does not work, try `sudo fuser -k %d/tcp`' %
                 (inst.DBPORT, inst.DBPORT))

    # check if there is an installation from packages
    if inst is server and os.path.exists('/etc/openquake/openquake.cfg'):
        sys.exit(PACKAGES)
    if (inst is server and os.path.exists(inst.OQ) and
            os.readlink(inst.OQ) != '%s/bin/oq' % inst.VENV):
        sys.exit('Error: there is already a link %s->%s; please remove it' %
                 (inst.OQ, os.readlink(inst.OQ)))


def install(inst):
    if inst is server:
        # create the openquake user if necessary
        try:
            pwd.getpwnam('openquake')
        except KeyError:
            subprocess.check_call(['useradd', 'openquake'])
            print('Created user openquake')

    # create the database
    if not os.path.exists(inst.OQDATA):
        os.makedirs(inst.OQDATA)
        if inst is server:
            subprocess.check_call(['chown', 'openquake', inst.OQDATA])

    # create the openquake venv if necessary
    if not os.path.exists(inst.VENV):
        # create venv
        venv.EnvBuilder(with_pip=True).create(inst.VENV)
        print('Created %s' % inst.VENV)

    # upgrade pip
    subprocess.check_call(['%s/bin/pip' % inst.VENV, 'install', 'pip', 'wheel',
                           '--upgrade'])
    # install the engine
    if inst is devel:
        req = 'requirements-py%d%d-linux64.txt' % PYVER
        subprocess.check_call(['%s/bin/pip' % inst.VENV, 'install',
                               '-r', req])
        subprocess.check_call(['%s/bin/pip' % inst.VENV, 'install',
                               '-e', '.'])
    else:
        subprocess.check_call(['%s/bin/pip' % inst.VENV, 'install',
                               'openquake.engine', '--upgrade'])

    # create openquake.cfg
    if inst is server:
        if os.path.exists(inst.OQ_CFG):
            print('There is an old file %s, I not touching it, but consider '
                  'updating it with\n%s' % (inst.OQ_CFG, inst.CONFIG))
        else:
            with open(inst.OQ_CFG, 'w') as cfg:
                cfg.write(inst.CONFIG)
            print('Created %s' % inst.OQ_CFG)

    # create symlink to oq
    oqreal = '%s/bin/oq' % inst.VENV
    if inst is server and not os.path.exists(inst.OQ):
        os.symlink(oqreal, inst.OQ)
    if inst is not server:
        print(f'Please add an alias oq={oqreal} in your .bashrc or similar')

    # create systemd services
    if inst is server and os.path.exists('/lib/systemd/system'):
        for service in ['dbserver', 'webui']:
            service_name = 'openquake-%s.service' % service
            service_path = '/lib/systemd/system/' + service_name
            if not os.path.exists(service_path):
                with open(service_path, 'w') as f:
                    f.write(SERVICE.format(vars(inst)))
            subprocess.check_call(['systemctl', 'enable', service_name])
            subprocess.check_call(['systemctl', 'start', service_name])

    # download a test calculation
    path = os.path.join(os.path.dirname(inst.OQDATA), 'classical.zip')
    with urlopen('https://github.com/gem/oq-engine/blob/master/openquake/'
                 'server/tests/data/classical.zip?raw=true') as f:
        open(path, 'wb').write(f.read())
    print('The engine was installed successfully.')
    print('You can run a test calculation with the command')
    print(f'{oqreal} engine --run {path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("inst", choices=['devel', 'user', 'server'],
                        default='server', nargs='?',
                        help='the kind of installation you want '
                        '(default server)')
    inst = globals()[parser.parse_args().inst]
    before_checks(inst)
    install(inst)
