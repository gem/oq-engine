# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020-2021 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
Universal installation script for the OpenQuake engine.
Three installation methods are supported:

1. "server" installation, i.e. system-wide installation on /opt/openquake
1. "devel_server" installation, i.e. developement system-wide installation on /opt/openquake
2. "user" installation on $HOME/openquake
3. "devel" installation on $HOME/openquake from the engine repository

To disinstall use the --remove flag, which remove the services and the
directories /opt/openquake or $HOME/openquake.
The calculations will NOT be removed since they live in
/var/lib/openquake/oqdata or $HOME/oqdata.
You have to remove the data directories manually, if you so wish.
"""
import os
import sys
import shutil
import socket
import getpass
import zipfile
import tempfile
import argparse
import subprocess
from urllib.request import urlopen
try:
    import venv
except ImportError:
    # check platform
    if sys.platform != 'win32':
        sys.exit('venv is missing! Please see the documentation of your '
                 'Operating System to install it')
    else:
        if os.path.exists('python\\python._pth.old'):
            print('This is method of the installation from the installer '
                  'windows')
        else:
            sys.exit('venv is missing! Please see the documentation of your '
                     'Operating System to install it')


class server:
    """
    Parameters for a server installation (with root permissions)
    """
    VENV = '/opt/openquake'
    CFG = os.path.join(VENV, 'openquake.cfg')
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


class devel_server:
    """
    Parameters for a development on server installation (with root permissions)
    """
    VENV = '/opt/openquake'
    CFG = os.path.join(VENV, 'openquake.cfg')
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
    if sys.platform == 'win32':
        if os.path.exists('python\\python._pth.old'):
            VENV = r'C:\Program Files\\OpenQuake\\python'
            OQ = os.path.join(VENV, '\\Scripts\\oq')
            OQDATA = os.path.expanduser('~\\oqdata')
        else:
            VENV = os.path.expanduser('~\\openquake')
            OQ = os.path.join(VENV, '\\Scripts\\oq')
            OQDATA = os.path.expanduser('~\\oqdata')
    else:
        VENV = os.path.expanduser('~/openquake')
        OQ = os.path.join(VENV, '/bin/oq')
        OQDATA = os.path.expanduser('~/oqdata')

    CFG = os.path.join(VENV, 'openquake.cfg')
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
PLATFORM = {'linux': ('linux64',),  # from sys.platform to requirements.txt
            'darwin': ('macos',),
            'win32': ('win64',)}
DEMOS = 'https://artifacts.openquake.org/travis/demos-master.zip'
GITBRANCH = 'https://github.com/gem/oq-engine/archive/%s.zip'
STANDALONE = 'https://github.com/gem/oq-platform-%s/archive/master.zip'

def install_standalone(venv):
    """
    Install the standalone Django applications if possible
    """
    print("The standalone applications are not installed yet")
    return
    for app in 'standalone ipt taxtweb taxonomy'.split():
        env = {'PYBUILD_NAME': 'oq-taxonomy'} if app == 'taxonomy' else {}
        try:
            subprocess.check_call(['%s/bin/pip' % venv, 'install',
                                   '--upgrade', STANDALONE % app], env=env)
        except Exception as exc:
            print('%s: could not install %s' % (exc, STANDALONE % app))

def before_checks(inst, remove, usage):
    """
    Checks to perform before the installation
    """
    # check python version
    if PYVER < (3, 6):
        sys.exit('Error: you need at least Python 3.6, but you have %s' %
                 '.'.join(map(str, sys.version_info)))

    # check platform
    if ((inst is server and sys.platform != 'linux') or (
            inst is devel_server and sys.platform != 'linux')):
        sys.exit('Error: this installation method is meant for linux!')

    # check venv
    if sys.prefix != sys.base_prefix:
        sys.exit('You are inside a virtual environment! Please deactivate')

    # check user
    user = getpass.getuser()
    if ((inst is server and user != 'root') or (
            inst is devel_server and user != 'root')):
        sys.exit('Error: you cannot perform a server or devel_server '
                 'installation unless '
                 'you are root. If you do not have root permissions, you '
                 'can install the engine in user mode.\n\n' + usage)
    elif ((inst is user and user == 'root') or (
            inst is devel and user == 'root')):
        sys.exit('Error: you cannot perform a user or devel installation'
                 ' as root.')

    # check if there is a DbServer running
    if not remove:
        cmd = ('sudo systemctl stop openquake-dbserver' if (
            inst is server or inst is devel_server) else 'oq dbserver stop')
        cmd = ('oq dbserver stop')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            errcode = sock.connect_ex(('localhost', inst.DBPORT))
        finally:
            sock.close()
        if errcode == 0:  # no error, the DbServer is up
            sys.exit('There is DbServer running on port %d from a previous '
                     'installation. Please run `%s`. '
                     'If it does not work, try `sudo fuser -k %d/tcp`' %
                     (inst.DBPORT, cmd, inst.DBPORT))

    # check if there is an installation from packages
    if ((inst is server and os.path.exists('/etc/openquake/openquake.cfg'))
        or (inst is devel_server and
            os.path.exists('/etc/openquake/openquake.cfg'))):
        sys.exit(PACKAGES)
    if ((inst is server and os.path.exists(inst.OQ) and
            os.readlink(inst.OQ) != '%s/bin/oq' % inst.VENV) or
            (inst is devel_server and os.path.exists(inst.OQ) and
            os.readlink(inst.OQ) != '%s/bin/oq' % inst.VENV)):
        sys.exit('Error: there is already a link %s->%s; please remove it' %
                 (inst.OQ, os.readlink(inst.OQ)))


def install(inst, version):
    """
    Install the engine in one of the three possible modes
    """
    if inst is server or inst is devel_server:
        import pwd
        # create the openquake user if necessary
        try:
            pwd.getpwnam('openquake')
        except KeyError:
            subprocess.check_call(['useradd', '-m', '-U', 'openquake'])
            print('Created user openquake')

    # create the database
    if not os.path.exists(inst.OQDATA):
        os.makedirs(inst.OQDATA)
        if inst is server or inst is devel_server:
            subprocess.check_call(['chown', 'openquake', inst.OQDATA])

    # create the openquake venv if necessary
    if not os.path.exists(inst.VENV) or not os.listdir(inst.VENV):
        # create venv
        venv.EnvBuilder(with_pip=True).create(inst.VENV)
        print('Created %s' % inst.VENV)

    if sys.platform == 'win32':
        if os.path.exists('python\\python._pth.old'):
            pycmd = inst.VENV + '\\python.exe'
        else:
            pycmd = inst.VENV + '\\Scripts\\python.exe'
    else:
        pycmd = inst.VENV + '/bin/python'
    # upgrade pip
    subprocess.check_call([pycmd, '-m', 'pip', 'install', '--upgrade', 
                          'pip', 'wheel'])

    # install the requirements
    req = 'https://raw.githubusercontent.com/gem/oq-engine/master/' \
        'requirements-py%d%d-%s.txt' % (PYVER + PLATFORM[sys.platform])

    subprocess.check_call([pycmd, '-m', 'pip', 'install', '-r', req])

    if (inst is devel or inst is devel_server):  # install from the local repo
        subprocess.check_call([pycmd, '-m', 'pip', 'install', '-e', '.'])
    elif version is None:  # install the stable version
        subprocess.check_call([pycmd, '-m', 'pip', 'install',
                               '--upgrade', 'openquake.engine'])
    elif '.' in version:  # install an official version
        subprocess.check_call([pycmd, '-m', 'pip', 'install',
                               '--upgrade', 'openquake.engine==' + version])
    else:  # install a branch from github
        subprocess.check_call([pycmd, '-m', 'pip', 'install',
                               '--upgrade', GITBRANCH % version])

    install_standalone(inst.VENV)

    # create openquake.cfg
    if (inst is server or inst is devel_server):
        if os.path.exists(inst.CFG):
            print('There is an old file %s; it will not be overwritten, '
                  'but consider updating it with\n%s' %
                  (inst.CFG, inst.CONFIG))
        else:
            with open(inst.CFG, 'w') as cfg:
                cfg.write(inst.CONFIG)
            print('Created %s' % inst.CFG)

    # create symlink to oq
    oqreal = '%s/bin/oq' % inst.VENV
    if sys.platform == 'win32':
        oqreal = '%s\\Scripts\\oq' % inst.VENV
    else:
        oqreal = '%s/bin/oq' % inst.VENV

    if ((inst is server and not os.path.exists(inst.OQ)) or
       (inst is devel_server and not os.path.exists(inst.OQ))):
        os.symlink(oqreal, inst.OQ)
    if inst is user:
        if sys.platform == 'win32':
            print(f'Please activate the virtualenv with {inst.VENV}'
                  '\\Scripts\\activate.bat')
        else:
            print(f'Please add an alias oq={oqreal} in your .bashrc or similar')
    elif inst is devel:
        if sys.platform == 'win32':
            print(f'Please activate the virtualenv with {inst.VENV}'
                  '\\Scripts\\activate.bat')
        else:
            print(f'Please activate the venv with source {inst.VENV}'
                  '/bin/activate')

    # create systemd services
    if ((inst is server and os.path.exists('/usr/lib/systemd/system')) or
       (inst is devel_server and os.path.exists('/usr/lib/systemd/system'))):
        for service in ['dbserver', 'webui']:
            service_name = 'openquake-%s.service' % service
            service_path = '/etc/systemd/system/' + service_name
            if not os.path.exists(service_path):
                with open(service_path, 'w') as f:
                    srv = SERVICE.format(service=service, OQDATA=inst.OQDATA)
                    f.write(srv)
            subprocess.check_call(
                ['systemctl', 'enable', '--now', service_name])
            subprocess.check_call(['systemctl', 'start', service_name])

    # download and unzip the demos
    try:
        with urlopen(DEMOS) as f:
            data = f.read()
    except OSError:
        msg = 'However, we could not download the demos from %s' % DEMOS
    else:
        th, tmp = tempfile.mkstemp(suffix='.zip')
        with os.fdopen(th, 'wb') as t:
            t.write(data)
        zipfile.ZipFile(tmp).extractall(inst.VENV)
        os.remove(tmp)
        path = os.path.join(inst.VENV, 'demos', 'hazard',
                            'AreaSourceClassicalPSHA', 'job.ini')
        msg = ('You can run a test calculation with the command\n'
               f'{oqreal} engine --run {path}')
    print('The engine was installed successfully.\n' + msg)


def remove(inst):
    """
    Remove the virtualenv directory. In case of a server installation, also
    remove the systemd services.
    """
    if inst is server or inst is devel_server:
        for service in ['dbserver', 'webui']:
            service_name = 'openquake-%s.service' % service
            service_path = '/usr/lib/systemd/system/' + service_name
            if os.path.exists(service_path):
                subprocess.check_call(['systemctl', 'stop', service_name])
                print('stopped ' + service_name)
                os.remove(service_path)
        subprocess.check_call(['systemctl', 'daemon-reload'])
    shutil.rmtree(inst.VENV)
    print('%s has been removed' % inst.VENV)
    if inst is server and os.path.exists(server.OQ) or (
            inst is devel_server and os.path.exists(server.OQ)):
        os.remove(server.OQ)
        print('%s has been removed' % server.OQ)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inst", choices=['server', 'user', 'devel',
                                         'devel_server'],
                        default='server', nargs='?',
                        help='the kind of installation you want '
                        '(default server)')
    parser.add_argument("--remove",  action="store_true",
                        help="disinstall the engine")
    parser.add_argument("--version",
                        help="version to install (default stable)")
    args = parser.parse_args()
    inst = globals()[args.inst]
    before_checks(inst, args.remove, parser.format_usage())
    if args.remove:
        remove(inst)
    else:
        install(inst, args.version)
