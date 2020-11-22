import os
import sys
import pwd
import socket
import getpass
import argparse
import subprocess
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


def before_checks(kind):
    # check python version
    if sys.version_info[:2] < (3, 6):
        sys.exit('Error: you need at least Python 3.6, but you have %s' %
                 '.'.join(map(str, sys.version_info)))

    # check platform
    if kind is server and sys.platform != 'linux':
        sys.exit('Error: this installation method is meant for linux!')

    # check if there is a DbServer running
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        errcode = sock.connect_ex(('localhost', kind.DBPORT))
    finally:
        sock.close()
    if errcode == 0:  # no error, the DbServer is up
        sys.exit('There is DbServer running on port %d from a previous '
                 'installation. Please run `oq dbserver stop`. '
                 'If it does not work, try `sudo fuser -k %d/tcp`' %
                 (kind.DBPORT, kind.DBPORT))

    # check if there is an installation from packages
    if kind is server and os.path.exists('/etc/openquake/openquake.cfg'):
        sys.exit(PACKAGES)

    user = getpass.getuser()
    if kind is server and user != 'root':
        sys.exit('Error: you cannot run this script unless you are root. If '
                 'you do not have root permissions, you can always install '
                 'the engine in single-user mode.')
    if (kind is server and os.path.exists(kind.OQ) and
            os.readlink(kind.OQ) != '%s/bin/oq' % kind.VENV):
        sys.exit('Error: there is already a link %s->%s; please remove it' %
                 (kind.OQ, os.readlink(kind.OQ)))


def install(kind):
    if kind is server:
        # create the openquake user if necessary
        try:
            pwd.getpwnam('openquake')
        except KeyError:
            subprocess.check_call(['useradd', 'openquake'])
            print('Created user openquake')

    # create the database
    if not os.path.exists(kind.OQDATA):
        os.makedirs(kind.OQDATA)
        subprocess.check_call(['chown', 'openquake', kind.OQDATA])

    # create the openquake venv if necessary
    if not os.path.exists(kind.VENV):
        # create venv
        venv.EnvBuilder(with_pip=True).create(kind.VENV)
        print('Created %s' % kind.VENV)

    # upgrade pip
    subprocess.check_call(['%s/bin/pip' % kind.VENV, 'install', 'pip', 'wheel',
                           '--upgrade'])
    # install the engine
    if kind is devel:
        subprocess.check_call(['%s/bin/pip' % kind.VENV, 'install',
                               '-e', '.'])
    else:
        subprocess.check_call(['%s/bin/pip' % kind.VENV, 'install',
                               'openquake.engine', '--upgrade'])

    # create openquake.cfg
    if os.path.exists(kind.OQ_CFG):
        print('There is an old file %s, I not touching it, but consider '
              'updating it with\n%s' % (kind.OQ_CFG, kind.CONFIG))
    else:
        with open(kind.OQ_CFG, 'w') as cfg:
            cfg.write(kind.CONFIG)
        print('Created %s' % kind.OQ_CFG)

    # create symlink to oq
    if kind is server and not os.path.exists(kind.OQ):
        os.symlink('%s/bin/oq' % kind.VENV, kind.OQ)

    # create systemd services
    if kind is server and os.path.exists('/lib/systemd/system'):
        for service in ['dbserver', 'webui']:
            service_name = 'openquake-%s.service' % service
            service_path = '/lib/systemd/system/' + service_name
            if not os.path.exists(service_path):
                with open(service_path, 'w') as f:
                    f.write(SERVICE.format(vars(kind)))
            subprocess.check_call(['systemctl', 'enable', service_name])
            subprocess.check_call(['systemctl', 'start', service_name])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=['devel', 'user', 'server'],
                        default='server', nargs='?',
                        help='the kind of installation you want')
    kind = globals()[parser.parse_args().kind]
    before_checks(kind)
    install(kind)
