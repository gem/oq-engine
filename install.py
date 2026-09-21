# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4 expandtab
#
# Copyright (C) 2020-2026 GEM Foundation
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
Four installation methods are supported:

1. "server" installation, i.e. system-wide installation on /opt/openquake
2. "devel_server" installation, i.e. developement system-wide installation on
    /opt/openquake
3. "user" installation on $HOME/openquake
4. "devel" installation on $HOME/openquake from the engine repository

To disinstall use the --remove flag, which remove the services and the
directories /opt/openquake/venv or $HOME/openquake.
The calculations will NOT be removed since they live in
/opt/openquake/oqdata or $HOME/oqdata.
You have to remove the data directories manually, if you so wish.
"""
import os
import re
import sys
import json
import glob
import shutil
import getpass
import tempfile
import argparse
import platform
import subprocess
from urllib.request import urlopen, Request

VENV_ERROR = ("venv is missing! Please see the documentation of your "
              "Operating System to install it")
try:
    import ensurepip  # noqa
except ImportError:
    sys.exit("ensurepip is missing; on Ubuntu the solution is to install "
             "python3-venv with apt")
try:
    import venv
except ImportError:
    # check platform
    if sys.platform != "win32":
        sys.exit(VENV_ERROR)
    elif os.path.exists("python\\python._pth.old"):
        print("Installing on Windows")
    else:
        sys.exit(VENV_ERROR)

PYVER = sys.version_info
if PYVER < (3, 11, 0):
    sys.exit(f"Error: you need at least Python 3.11, but you have "
             f"{'.'.join(map(str, sys.version_info))}")

# check macOS
if sys.platform == "darwin":
    mac_version_str = platform.mac_ver()[0]
    major_version = int(mac_version_str.split(".")[0])
    if major_version < 15:
        sys.exit(f"Error: macOS {mac_version_str} is not supported. "
                 "Version 15 or higher is required.")

CDIR = os.path.dirname(os.path.abspath(__file__))


def remove_venv_msg(pyvenv):
    return f"""Found pre-existing venv {pyvenv}
If you proceeed you will have to reinstall manually any software other
than the engine that you may have there. Proceed? [y/N]"""


class server:
    """
    Parameters for a server installation (with root permissions)
    """

    #
    # For server and devel_server we do not (yet) support changing venv
    # if we support changing venv, we need also to replace CFG and other
    # dependent fields with methods
    #
    SERVER = True
    DEVEL = False
    NOVENV = False
    VENV = "/opt/openquake/venv"
    CFG = os.path.join(VENV, "openquake.cfg")
    OQ = "/usr/bin/oq"
    OQDATA = "/opt/openquake/oqdata"
    DBPATH = os.path.join(OQDATA, "db.sqlite3")
    CONFIG = f"""[dbserver]
    host = localhost
    file = {DBPATH}
    [directory]
    """
    USER = "openquake"

    @classmethod
    def manage_py(cls):
        return os.path.join(cls.VENV, 'lib',
                            f'python{PYVER[0]}.{PYVER[1]}',
                            'site-packages', 'openquake',
                            'server', 'manage.py')


class devel_server(server):
    """
    Parameters for a development on server installation (with root permissions)
    """

    DEVEL = True

    @classmethod
    def manage_py(cls):
        return os.path.join('openquake', 'server', 'manage.py')


class user:
    """
    Parameters for a user installation
    """

    SERVER = False
    DEVEL = False
    NOVENV = False

    if sys.platform == "win32":
        if os.path.exists("python\\python._pth.old"):
            VENV = r"C:\Program Files\\OpenQuake\\python"
            OQ = os.path.join(VENV, "\\Scripts\\oq")
            OQDATA = os.path.expanduser("~\\oqdata")
        else:
            VENV = os.path.expanduser("~\\openquake")
            OQ = os.path.join(VENV, "\\Scripts\\oq")
            OQDATA = os.path.expanduser("~\\oqdata")
    else:
        VENV = os.path.expanduser("~/openquake")
        OQ = os.path.join(VENV, "/bin/oq")
        OQDATA = os.path.expanduser("~/oqdata")

    CFG = os.path.join(VENV, "openquake.cfg")
    CONFIG = ""
    USER = None

    @classmethod
    def manage_py(cls):
        if sys.platform == "win32":
            return os.path.join(cls.VENV, 'lib',
                                'site-packages', 'openquake',
                                'server', 'manage.py')
        return os.path.join(cls.VENV, 'lib',
                            f'python{PYVER[0]}.{PYVER[1]}',
                            'site-packages', 'openquake',
                            'server', 'manage.py')


class devel(user):
    """
    Parameters for a devel installation (same as user)
    """

    DEVEL = True

    @classmethod
    def manage_py(cls):
        return os.path.join('openquake', 'server', 'manage.py')


PACKAGES = """It looks like you have an installation from packages.
Please remove it with `sudo apt remove oq-python38` on Debian derivatives
or with `sudo yum remove python3-oq-engine` on Red Hat derivatives.
Then give the command `sudo rm -rf /opt/openquake /etc/openquake/openquake.cfg`
"""
SERVICE = """\
[Unit]
Description=The OpenQuake Engine {service}
Documentation=https://github.com/gem/oq-engine/
After= {afterservice}

[Service]
User=openquake
Group=openquake
Environment=
WorkingDirectory={OQDATA}
ExecStart=/opt/openquake/venv/bin/oq {command}
Type=exec
Restart=always
RestartSec=30
KillMode=control-group
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
"""
PLATFORM = {
    "linux": ("linux64",),  # from sys.platform to requirements.txt
    "darwin": ("macos",),
    "win32": ("win64",),
}
# FIXME just for devel test
# URL_STANDALONE = "https://wheelhouse.openquake.org/py/standalone/latest/"
URL_STANDALONE = "https://wheelhouse.openquake.org/py/standalone/post-inst/"
WHEELHOUSE_URL = "https://wheelhouse.openquake.org/unified/"
STANDALONE_APP_INFO = [
    # All engine Django app need oq-platform-standalone
    {"pkg": "oq-platform-standalone", "name": None,
     "ver": "~=2.16.4"},
    # Django apps to install
    {"pkg": "oq-platform-ipt",        "name": "openquakeplatform_ipt",
     "ver": "~=1.21.0"},
    {"pkg": "oq-platform-taxonomy",   "name": "openquakeplatform_taxonomy",
     "ver": "~=1.2.0"},
    {"pkg": "django-gem-taxonomy",    "name": "django_gem_taxonomy",
     "ver": "~=1.4.4"},
]


def python_exe(inst):
    """
    Path of the python executable to use for the installation: the current
    one when --novenv is given, else the python inside the virtualenv.
    """
    if inst.NOVENV:
        return sys.executable
    if sys.platform == "win32":
        if os.path.exists("python\\python._pth.old"):
            return inst.VENV + "\\python.exe"
        return inst.VENV + "\\Scripts\\python.exe"
    return inst.VENV + "/bin/python3"


def ensure(pip=None, pyvenv=None):
    """
    Create venv and install pip
    """
    try:
        if pyvenv:
            if os.path.exists(pyvenv):
                if input(remove_venv_msg(pyvenv)).lower() == "y":
                    shutil.rmtree(pyvenv)
                else:
                    sys.exit(0)
            venv.EnvBuilder(with_pip=True).create(pyvenv)
        else:
            subprocess.check_call([pip, "-m", "ensurepip", "--upgrade"])
    except subprocess.CalledProcessError as exc:
        if "died with <Signals.SIGABRT" in str(exc):
            if pyvenv:
                shutil.rmtree(pyvenv)
            raise RuntimeError(
                f"Could not execute ensurepip --upgrade: {exc} (probably "
                f"you are using the system Python {sys.executable})")


def get_requirements_branch(version, inst, from_fork):
    """
    Convert "version" into a branch name
    """
    # in actions triggered by forks we want requirements to be taken from
    # master
    if from_fork:
        return "master"
    # in cases such as 'install.py user', for instance while running tests from
    # another gem repository, we need requirements to be read from the latest
    # stable version unless differently specified.
    if version is None:
        if inst.DEVEL:
            return "master"
        # retrieve the tag name of the current stable version
        with urlopen("https://pypi.org/pypi/openquake.engine/json") as resp:
            content = resp.read()
        version = json.loads(content)["info"]["version"]  # i.e. '3.24.1'
        return f"v{version}"
    mo = re.match(r"(\d+\.\d+)+", version)
    if mo:
        return "engine-" + mo.group(0)
    return version


def _run_subprocess(inst, args):
    # Run subprocess use sudo if inst.USER != None
    if inst.USER is None:
        subprocess.check_call(args)
    else:
        # user=inst.USER does not appear to work in the same
        # way as sudo -u $USER
        subprocess.check_call(['sudo', '-u', inst.USER] + args)


def install_standalone(inst):
    """
    Install the standalone Django applications if possible
    """
    print("The standalone applications are not installed yet")
    pycmd = python_exe(inst)
    errors = []
    for app in STANDALONE_APP_INFO:
        try:
            print(f"Applications {app['pkg']} are not installed yet \n")
            subprocess.check_call(
                [pycmd, "-m", "pip", "install",
                 "--no-index", "--no-cache-dir",
                 "--find-links", WHEELHOUSE_URL,
                 "--find-links", URL_STANDALONE,
                 app['pkg'] + app['ver']])
        except Exception as exc:
            # for instance if somebody removed a wheel from the wheelhouse
            errors.append(f"{exc}: could not install {app['pkg']}")
    return errors


def postinstall_standalone(inst):
    """
    Run '<app>_postinstall' command for each standalone Django application,
    if it exists.
    """
    print("Run '<app>_postinstall' command for each standalone\n"
          " Django applications, if it exists")
    # we cannot use site.getsitepackages here since we are not yet
    # running in the target environment
    pycmd = python_exe(inst)
    # Run python manage.py migrate before running app postinstall
    _run_subprocess(inst, [pycmd, inst.manage_py(), "migrate"])
    errors = []
    for app in STANDALONE_APP_INFO:
        if not app['name']:
            continue
        try:
            # Run python manage.py postinstall
            _run_subprocess(
                inst, [pycmd, inst.manage_py(),
                       "openquake_engine_postinstall", app['name']])
        except Exception as exc:
            # for instance if somebody removed a wheel from the wheelhouse
            errors.append(f"{exc}: error during {app['name']} postinstall "
                          "command execution")
    return errors


def check_venv(inst, args, usage):
    """
    Checks on the virtual environment and on the user running the script.
    """
    # check venv
    if args.novenv:
        if inst.SERVER:
            sys.exit("Error: --novenv is not supported for server installs")
        # install in the current Python environment
        inst.VENV = sys.prefix
        inst.NOVENV = True
    elif sys.prefix != sys.base_prefix:
        sys.exit("You are inside a virtual environment! Please deactivate")

    # server and devel_server installs are linux only and with fixed venv
    if inst.SERVER:
        if sys.platform != "linux":
            sys.exit("Error: this installation method is meant for linux!")
        if args.venv:
            sys.exit("Error: --venv with server install is not supported")
        if getpass.getuser() != "root":
            sys.exit(
                "Error: you cannot perform a server or devel_server "
                "installation unless you are root. If you do not have "
                "root permissions, you can install the engine in user "
                "mode.\n\n" + usage)

    if args.venv:
        inst.VENV = os.path.abspath(os.path.expanduser(args.venv))

    # check user
    if not inst.SERVER and getpass.getuser() == "root":
        sys.exit("Error: you cannot perform a user or devel installation"
                 " as root.")
    elif inst.DEVEL and not inst.SERVER:
        if shutil.which("git") is None:
            raise RuntimeError("git is missing, please install it")
        try:
            branch = subprocess.check_output(
                ['git', 'branch', '--show-current']).decode('utf8').strip()
        except subprocess.CalledProcessError:
            raise RuntimeError('install.py must be called from the engine '
                               f'repository, not from {os.getcwd()}')
        print(f'Devel install on branch {branch}')
        if args.version:
            print(f'WARNING: ignoring version flag for devel install on '
                  f'branch {branch}')
        # use version consistent with the branch, even if --version flag
        args.version = branch


def check_packages(inst):
    """
    Check for a pre-existing installation from packages or a conflicting
    symlink.
    """
    if inst.SERVER and os.path.exists("/etc/openquake/openquake.cfg"):
        sys.exit(PACKAGES)
    if (inst.SERVER and os.path.exists(inst.OQ)
            and os.readlink(inst.OQ) != f"{inst.VENV}/bin/oq"):
        sys.exit(f"Error: there is already a link {inst.OQ}->"
                 f"{os.readlink(inst.OQ)}; please remove it")


def before_checks(inst, args, usage):
    """
    Checks to perform before the installation
    """
    check_venv(inst, args, usage)
    check_packages(inst)


# this is only called for user or server installations
def latest_commit(branch):
    # Get the token from the environment variable provided by GitHub Actions
    # (if available)
    token = os.getenv('GITHUB_TOKEN')
    url = "https://api.github.com/repos/GEM/oq-engine/commits/" + branch
    # Create a request object and add the header (if present)
    req = Request(url)
    if token:
        req.add_header('Authorization', f'token {token}')
    with urlopen(req) as f:
        js = json.loads(f.read())
    return js["sha"]


def fix_version(commit, venv):
    """
    Fix the file baselib/__init__.py with the git version
    """
    if sys.platform == "win32":
        path = "/lib/site-packages/openquake/baselib/__init__.py"
    else:
        path = "/lib/python*/site-packages/openquake/baselib/__init__.py"
    [fname] = glob.glob(venv + path)
    lines = []
    for line in open(fname):
        if line.startswith("__version__ = ") and "-git" not in line:
            vers = line.split("=")[1].strip()[1:-1]  # i.e. '3.12.0'
            lines.append(f'__version__ = "{vers}-git{commit}"\n')
        else:
            lines.append(line)
    with open(fname, "w") as f:
        f.write("".join(lines))


def normalize_version(version):
    """
    Convert a user-supplied --version argument into a pip-compatible
    version specifier.
    """
    if version.count('.') == 1:
        # e.g. "3.23" -> latest patch in that series, expands to >=3.23.0,<3.24
        return f"~={version}.0"
    else:
        # e.g. "3.23.4" -> exact match
        return f"=={version}"


def create_openquake_user(inst):
    """
    Create the 'openquake' system user, if needed.
    """
    if not inst.SERVER:
        return
    import pwd

    try:
        pwd.getpwnam("openquake")
    except KeyError:
        subprocess.check_call(["useradd", "-m", "-U", "openquake"])
        print("Created user openquake")


def create_dbdir(inst):
    """
    Create the data directory, if needed.
    """
    if os.path.exists(inst.OQDATA):
        return
    os.makedirs(inst.OQDATA)
    if inst.SERVER:
        subprocess.check_call(["chown", "openquake", inst.OQDATA])


def upgrade_pip(pycmd, noupgrade):
    """
    Upgrade pip and wheel inside the virtualenv.
    """
    upgrade = [] if noupgrade else ["--upgrade"]
    if sys.platform != "win32":
        ensure(pip=pycmd)
        subprocess.check_call(
            [pycmd, "-m", "pip", "install"] + upgrade + ["pip", "wheel"])
    elif os.path.exists("python\\python._pth.old"):
        subprocess.check_call(
            [pycmd, "-m", "pip", "install"] + upgrade
            + ["pip", "wheel", "urllib3"])
    else:
        subprocess.check_call([pycmd, "-m", "ensurepip"] + upgrade)
        subprocess.check_call(
            [pycmd, "-m", "pip", "install"] + upgrade
            + ["pip", "wheel", "urllib3"])


def requirements_url(inst, version, from_fork):
    """
    Build the URL of the requirements file for the current platform.
    """
    branch = get_requirements_branch(version, inst, from_fork)
    if sys.platform == "darwin":
        mac = "_" + platform.machine()  # x86_64 or arm64
    else:
        mac = ""
    if inst.DEVEL:
        # use local requirements file for devel installs
        req_pre = CDIR
    else:
        # use github for user and server installs
        req_pre = f'https://raw.githubusercontent.com/gem/oq-engine/{branch}/'
    platform_ = PLATFORM[sys.platform][0]
    return (f"{req_pre}/requirements-py{PYVER[0]}{PYVER[1]}-"
            f"{platform_}{mac}.txt")


def install_requirements(inst, pycmd, version, from_fork):
    """
    Install the requirements file.
    """
    req = requirements_url(inst, version, from_fork)
    subprocess.check_call(
        [pycmd, "-m", "pip", "install", "--force-reinstall",
         "--trusted-host", "wheelhouse.openquake.org",
         "--trusted-host", "raw.githubusercontent.com", "-r", req])


def git_zip_url(commit):
    """
    URL of the zip archive of the engine at the given commit.
    """
    return f"https://github.com/gem/oq-engine/archive/{commit}.zip"


def install_engine(inst, pycmd, version, noupgrade):
    """
    Install the engine itself, from the local repo, from pypi or from a
    github branch.
    """
    upgrade = [] if noupgrade else ["--upgrade"]
    if inst.DEVEL:  # install from the local repo
        subprocess.check_call([pycmd, "-m", "pip", "install", "-e", CDIR])
    elif version is None:  # install the stable version
        subprocess.check_call(
            [pycmd, "-m", "pip", "install"] + upgrade
            + ["openquake.engine"])
    elif re.match(r"\d+(\.\d+)+", version):  # install an official version
        subprocess.check_call(
            [pycmd, "-m", "pip", "install"] + upgrade
            + [f"openquake.engine{normalize_version(version)}"])
    else:  # install a branch from github (only for user or server)
        commit = latest_commit(version)
        print("Installing commit", commit)
        with tempfile.TemporaryDirectory() as tmp:
            custom_env = os.environ.copy()
            custom_env["TMPDIR"] = tmp  # Linux/macOS
            custom_env["TEMP"] = tmp    # Windows
            subprocess.check_call(
                [pycmd, "-m", "pip", "install"] + upgrade
                + [git_zip_url(commit), "--no-clean"], env=custom_env)
        fix_version(commit, inst.VENV)


def create_cfg(inst):
    """
    Create the server openquake.cfg file, unless it already exists.
    """
    if not inst.SERVER:
        return
    if os.path.exists(inst.CFG):
        print(f"There is an old file {inst.CFG}; it will not be "
              f"overwritten, but consider updating it with\n{inst.CONFIG}")
    else:
        with open(inst.CFG, "w") as cfg:
            cfg.write(inst.CONFIG)
        print(f"Created {inst.CFG}")


def oq_path(inst):
    """
    Path of the 'oq' executable in the target environment.
    """
    if inst.NOVENV:
        exe = "oq.exe" if sys.platform == "win32" else "oq"
        return os.path.join(os.path.dirname(sys.executable), exe)
    if sys.platform == "win32":
        return f"{inst.VENV}\\Scripts\\oq"
    return f"{inst.VENV}/bin/oq"


def upgrade_db(inst, oqreal):
    """
    Create or upgrade the database.
    """
    if inst.SERVER:
        subprocess.run(
            ['sudo', '-u', 'openquake', oqreal, "engine", "--upgrade-db"])
    else:  # create/upgrade the db in the default location
        subprocess.run([oqreal, "engine", "--upgrade-db"])


def create_symlink(inst, oqreal):
    """
    Create the /usr/bin/oq symlink for server installations.
    """
    if inst.SERVER and not os.path.exists(inst.OQ):
        os.symlink(oqreal, inst.OQ)


def activation_message(inst):
    """
    Print the instructions to activate the virtualenv.
    """
    if inst.SERVER or inst.NOVENV:
        return
    if sys.platform == "win32":
        print(f"Please activate the virtualenv with {inst.VENV}"
              f"\\Scripts\\activate.bat (in CMD) or {inst.VENV}"
              "\\Scripts\\activate.ps1 (in PowerShell)")
    else:
        print(f"Please activate the venv with source {inst.VENV}"
              "/bin/activate")


def create_services(inst):
    """
    Create and start the systemd services for server installations.
    """
    if not (inst.SERVER and os.path.exists("/run/systemd/system")):
        return
    for service in ["webui"]:
        service_name = f"openquake-{service}.service"
        service_path = "/etc/systemd/system/" + service_name
        afterservice = "network.target"
        command = service + " -s start"
        if not os.path.exists(service_path):
            with open(service_path, "w") as f:
                srv = SERVICE.format(
                    service=service,
                    OQDATA=inst.OQDATA,
                    afterservice=afterservice,
                    command=command)
                f.write(srv)
        subprocess.check_call(["systemctl", "enable", "--now", service_name])
        subprocess.check_call(["systemctl", "start", service_name])


def success_message(inst, oqreal):
    """
    Print the final success message and a test command.
    """
    if inst.DEVEL:
        return
    path = os.path.join(
        inst.VENV, "demos", "hazard", "AreaSourceClassicalPSHA", "job.ini")
    msg = (
        "You can run a test calculation with the command\n"
        f"{oqreal} engine --run {path}")
    print("The engine was installed successfully.\n" + msg)


def install(inst, version, from_fork, noupgrade):
    """
    Install the engine in one of the four possible modes
    """
    create_openquake_user(inst)
    create_dbdir(inst)

    if not inst.NOVENV:
        # recreate the openquake venv
        ensure(pyvenv=inst.VENV)
        print(f"Created {inst.VENV}")
    pycmd = python_exe(inst)

    upgrade_pip(pycmd, noupgrade)
    install_requirements(inst, pycmd, version, from_fork)
    install_engine(inst, pycmd, version, noupgrade)

    errors = install_standalone(inst)

    create_cfg(inst)

    oqreal = oq_path(inst)
    print("Compiling python/numba modules")
    subprocess.run([oqreal, "--version"])  # compile numba
    upgrade_db(inst, oqreal)

    errors += postinstall_standalone(inst)

    create_symlink(inst, oqreal)
    activation_message(inst)
    create_services(inst)
    success_message(inst, oqreal)

    return errors


def remove(inst):
    """
    Remove the virtualenv directory. In case of a server installation, also
    remove the systemd services.
    """
    if inst.SERVER:
        for service in ["webui"]:
            service_name = f"openquake-{service}.service"
            service_path = "/etc/systemd/system/" + service_name
            if os.path.exists(service_path):
                subprocess.check_call(["systemctl", "stop", service_name])
                print("stopped " + service_name)
                os.remove(service_path)
                print("removed " + service_name)
        subprocess.check_call(["systemctl", "daemon-reload"])
    if inst.NOVENV:
        print("Not removing the current Python environment")
    elif os.path.exists(inst.VENV):
        shutil.rmtree(inst.VENV)
        print(f"{inst.VENV} has been removed")
    if inst.SERVER and os.path.exists(server.OQ):
        os.remove(server.OQ)
        print(f"{server.OQ} has been removed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "inst",
        choices=["server", "user", "devel", "devel_server"],
        nargs="?",
        help="the kind of installation you want")
    parser.add_argument("--venv", help="venv directory")
    parser.add_argument("--novenv", action="store_true",
                        help="install in the current Python environment")
    parser.add_argument("--noupgrade", action="store_true",
                        help="not use '--upgrade' in pip install calls")
    parser.add_argument("--remove", action="store_true",
                        help="disinstall the engine")
    parser.add_argument("--version",
                        help="version to install (default stable)")
    # NOTE: This flag should be set when installing the engine from an action
    #       triggered by a fork
    parser.add_argument(
        "--from_fork", dest="from_fork", action="store_true",
        help=argparse.SUPPRESS)
    parser.set_defaults(from_fork=False)
    args = parser.parse_args()
    if args.inst:
        # set inst to the class named as the string args.inst
        inst = globals()[args.inst]
        before_checks(inst, args, parser.format_usage())
        if args.remove:
            remove(inst)
        else:
            errors = install(inst, args.version, args.from_fork,
                             args.noupgrade)
            if errors:
                # NB: even if one of the tools is missing, the engine will work
                sys.exit('\n'.join(errors))
    else:
        sys.exit("Please specify the kind of installation")
