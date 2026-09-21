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
import pwd
import tempfile
import argparse
import platform
import subprocess
from urllib.request import urlopen, Request

try:
    import ensurepip  # noqa
except ImportError:
    sys.exit(
        "ensurepip is missing; on Ubuntu the solution is "
        "to install python3-venv with apt")
try:
    import venv
except ImportError:
    # check platform
    if sys.platform != "win32":
        sys.exit(
            "venv is missing! Please see the documentation "
            "of your Operating System to install it")
    else:
        if os.path.exists("python\\python._pth.old"):
            print("Installing on Windows")
        else:
            sys.exit("venv is missing! Please see the documentation "
                     "of your Operating System to install it")

PYVER = sys.version_info
if PYVER < (3, 11, 0):
    sys.exit("Error: you need at least Python 3.11, "
             f"but you have {'.'.join(map(str, sys.version_info))}")

# check macOS
if sys.platform == "darwin":
    mac_version_str = platform.mac_ver()[0]
    major_version = int(mac_version_str.split(".")[0])
    if major_version < 15:
        sys.exit(f"Error: macOS {mac_version_str} "
                 "is not supported. Version 15 or "
                 "higher is required.")

CDIR = os.path.dirname(os.path.abspath(__file__))
def _remove_venv_msg(pyvenv):
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
    VENV = "/opt/openquake/venv"
    CFG = os.path.join(VENV, "openquake.cfg")
    OQ = "/usr/bin/oq"
    OQL = ["sudo", "-H", "-u", "openquake", OQ]
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


class devel_server:
    """
    Parameters for a development on server installation (with root
    permissions)
    """
    VENV = "/opt/openquake/venv"
    CFG = os.path.join(VENV, "openquake.cfg")
    OQ = "/usr/bin/oq"
    OQL = ["sudo", "-H", "-u", "openquake", OQ]
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
        return os.path.join('openquake', 'server', 'manage.py')


class user:
    """
    Parameters for a user installation
    """
    if sys.platform == "win32":
        if os.path.exists("python\\python._pth.old"):
            VENV = "C:\\Program Files\\OpenQuake\\python"
            OQ = os.path.join(VENV, "Scripts", "oq")
            OQDATA = os.path.expanduser("~\\oqdata")
        else:
            VENV = os.path.expanduser("~\\openquake")
            OQ = os.path.join(VENV, "Scripts", "oq")
            OQDATA = os.path.expanduser("~\\oqdata")
    else:
        VENV = os.path.expanduser("~/openquake")
        OQ = os.path.join(VENV, "bin", "oq")
        OQDATA = os.path.expanduser("~/oqdata")

    CFG = os.path.join(VENV, "openquake.cfg")
    DBPATH = os.path.join(OQDATA, "db.sqlite3")
    CONFIG = ""
    USER = None

    @classmethod
    def manage_py(cls):
        if sys.platform == "win32":
            return os.path.join(cls.VENV, 'lib',
                                'site-packages', 'openquake',
                                'server', 'manage.py')
        else:
            return os.path.join(cls.VENV, 'lib',
                                f'python{PYVER[0]}.{PYVER[1]}',
                                'site-packages', 'openquake',
                                'server', 'manage.py')


class devel(user):
    """
    Parameters for a devel installation (same as user)
    """
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
def _git_branch_url(commit):
    return ("https://github.com/gem/oq-engine/"
            f"archive/{commit}.zip")
# FIXME just for devel test
# URL_STANDALONE = "https://wheelhouse.openquake.org/py/standalone/latest/"
URL_STANDALONE = "https://wheelhouse.openquake.org/py/standalone/post-inst/"
WHEELHOUSE_URL = "https://wheelhouse.openquake.org/unified/"


def ensure(pip=None, pyvenv=None):
    """Create venv and install pip."""
    try:
        if pyvenv:
            if os.path.exists(pyvenv):
                if input(
                        _remove_venv_msg(pyvenv)).lower() == "y":
                    shutil.rmtree(pyvenv)
                else:
                    sys.exit(0)
            venv.EnvBuilder(
                with_pip=True).create(pyvenv)
        else:
            subprocess.check_call(
                [pip, "-m", "ensurepip", "--upgrade"])
    except subprocess.CalledProcessError as exc:
        if "died with <Signals.SIGABRT" in str(exc):
            shutil.rmtree(inst.VENV)
            raise RuntimeError(
                f"ensurepip --upgrade failed: "
                f"using system Python "
                f"({sys.executable})")


def get_requirements_branch(version, inst, from_fork):
    """Convert version into a branch name."""
    if from_fork:
        return "master"
    if version is None:
        if inst in (devel, devel_server):
            return "master"
        with urlopen(
                "https://pypi.org/pypi/"
                "openquake.engine/json") as resp:
            version = json.loads(
                resp.read())["info"]["version"]
        return f"v{version}"
    mo = re.match(r"(\d+\.\d+)+", version)
    if mo:
        return "engine-" + mo.group(0)
    return version


def _run_subprocess(inst, args):
    """Run subprocess, using sudo if inst.USER is not None."""
    if inst.USER is None:
        subprocess.check_call(args)
    else:
        subprocess.check_call(['sudo', '-u', inst.USER] + args)


def _get_python_cmd(inst):
    """Return the python command path."""
    if sys.platform == "win32":
        if os.path.exists("python\\python._pth.old"):
            return inst.VENV + "\\python.exe"
        return inst.VENV + "\\Scripts\\python.exe"
    return inst.VENV + "/bin/python3"


def _ensure_pip(pycmd, noupgrade):
    """Upgrade pip in the virtualenv."""
    if sys.platform != "win32":
        ensure(pip=pycmd)
        subprocess.check_call(
            [pycmd, "-m", "pip", "install"] +
            ([] if noupgrade else ["--upgrade"]) +
            ["pip", "wheel"])
    elif os.path.exists(
            "python\\python._pth.old"):
        subprocess.check_call(
            [pycmd, "-m", "pip", "install"] +
            ([] if noupgrade else ["--upgrade"]) +
            ["pip", "wheel", "urllib3"])
        subprocess.check_call(
            [pycmd, "-m", "ensurepip"] +
            ([] if noupgrade else ["--upgrade"]))
        subprocess.check_call(
            [pycmd, "-m", "pip", "install"] +
            ([] if noupgrade else ["--upgrade"]) +
            ["pip", "wheel", "urllib3"])


# Standalone Django app installation info
# (moved to module level for reuse)
STANDALONE_APP_INFO = [
    # All engine Django app need
    # oq-platform-standalone
    {"pkg": "oq-platform-standalone",
     "name": None, "ver": "~=2.16.4"},
    # Django apps to install
    {"pkg": "oq-platform-ipt",
     "name": "openquakeplatform_ipt",
     "ver": "~=1.21.0"},
    {"pkg": "oq-platform-taxonomy",
     "name": "openquakeplatform_taxonomy",
     "ver": "~=1.2.0"},
    {"pkg": "django-gem-taxonomy",
     "name": "django_gem_taxonomy",
     "ver": "~=1.4.4"},
]


def standalone(inst, mode):
    """Install or postinstall standalone apps."""
    errors = []
    if mode == "install":
        print(
            "The standalone applications "
            "are not installed yet")
    else:
        print(
            "Run '<app>_postinstall' "
            "command for each standalone\n"
            " Django applications, if it "
            "exists")
    pycmd = _get_python_cmd(inst)
    if mode == "install":
        for app in STANDALONE_APP_INFO:
            try:
                print(f"Applications {app['pkg']} are not installed yet \n")
                subprocess.check_call(
                    [pycmd, "-m", "pip",
                     "install",
                     "--no-index",
                     "--no-cache-dir",
                     "--find-links",
                     WHEELHOUSE_URL,
                     "--find-links",
                     URL_STANDALONE,
                     app['pkg'] + app['ver']])
            except Exception as exc:
                errors.append(f"{exc}: could not install {app['pkg']}")
    else:
        _postinstall_standalone_apps(inst, errors)
    return errors


def _check_server_install(args, usage, inst):
    """Check server installation conditions."""
    if sys.platform != "linux":
        sys.exit("server/devel_server installation requires Linux")
    if args.venv:
        sys.exit("--venv with server install is not supported")
    if getpass.getuser() != "root":
        sys.exit(
            "you cannot perform a server or "
            "devel_server installation unless "
            "you are root. If you do not have "
            "root permissions, you can install "
            "the engine in user mode.\n\n" + usage)


def _check_venv_dir(inst, args):
    """Check and set venv directory."""
    if args.venv:
        inst.VENV = os.path.abspath(os.path.expanduser(args.venv))
    if args.novenv and sys.platform == "win32":
        inst.VENV = os.path.join(
            os.getenv('LocalAppData'),
            'Programs', 'OpenQuake Engine', 'python3')


def _check_existing_install(inst, args):
    """Check for existing installation."""
    if (inst in (server, devel_server)
            and os.path.exists(
                "/etc/openquake/openquake.cfg")):
        sys.exit(PACKAGES)
    oq_target = os.path.join(
        inst.VENV, "bin" if sys.platform != "win32" else "Scripts", "oq")
    if (inst in (server, devel_server) and os.path.exists(inst.OQ)
        and os.readlink(inst.OQ) != oq_target):
        sys.exit(f"a link {inst.OQ} -> {os.readlink(inst.OQ)}; "
                 "please remove it")


def _postinstall_standalone_apps(inst, errors):
    """Run postinstall for standalone apps."""
    # Obtain paths for python and manage.py in VENV, we cannot use
    # site.getsitepackages here since we are not yet running in the venv
    if sys.platform == "win32":
        python = ['Scripts', 'python.exe']
    else:
        python = ["bin", "python"]

    # Run python manage.py migrate
    # before running app postinstall
    _run_subprocess(inst,
        [os.path.join(inst.VENV, *python), inst.manage_py(), "migrate"])

    for app in STANDALONE_APP_INFO:
        if not app['name']:
            continue

        try:
            # Run python manage.py postinstall
            _run_subprocess(
                inst, [os.path.join(inst.VENV, *python),
                 inst.manage_py(), "openquake_engine_postinstall",
                 app['name']])
        except Exception as exc:
            # for instance is somebody
            # removed a wheel from the
            # wheelhouse
            errors.append(f"{exc}: error during {app['name']} postinstall "
                          "command execution")


def before_checks(inst, args, usage):
    """Checks to perform before installation."""
    # TODO consider moving inst-specific
    # checks to inst.check(args, usage)
    if sys.prefix != sys.base_prefix:
        sys.exit("inside a virtual environment! Please deactivate")
    if inst in (server, devel_server):
        _check_server_install(args, usage, inst)
    _check_venv_dir(inst, args)
    if inst in (user, devel) and getpass.getuser() == "root":
        sys.exit("cannot perform a user or devel installation as root")
    if inst is devel:
        _check_devel(inst, args)
    _check_existing_install(inst, args)


def _check_devel(inst, args):
    """Check devel installation."""
    # TODO should we not be checking for
    # devel_server here too?
    if shutil.which("git") is None:
        raise RuntimeError("git is missing")
    try:
        branch = (
            subprocess.check_output(
                ['git', 'branch', '--show-current']
            ).decode('utf8').strip())
    except subprocess.CalledProcessError:
        raise RuntimeError(
            'install.py must be called from '
            f'the engine repository, not from '
            f'{os.getcwd()}')
    print(f'Devel install on branch {branch}')
    if args.version:
        print(f'WARNING: ignoring version flag on branch {branch}')
        args.version = branch


# only called for user or server installations
def latest_commit(branch):
    """Get the latest commit SHA from GitHub API."""
    token = os.getenv('GITHUB_TOKEN')
    url = "https://api.github.com/repos/"
    url += f"GEM/oq-engine/commits/{branch}"
    req = Request(url)
    if token:
        req.add_header(
            'Authorization', f'token {token}')
    with urlopen(req) as f:
        return json.loads(f.read())["sha"]


def fix_version(commit, venv):
    """Fix baselib/__init__.py with the git version."""
    if sys.platform == "win32":
        path = "/lib/site-packages/"
        path += "openquake/baselib/__init__.py"
    else:
        path = "/lib/python*/site-packages/"
        path += "openquake/baselib/__init__.py"
    [fname] = glob.glob(venv + path)
    lines = []
    for line in open(fname):
        if line.startswith("__version__ = "):
            vers = line.split("=")[1].strip()[1:-1]
            lines.append(f'__version__ = "{vers}-git{commit}"\n')
        else:
            lines.append(line)
    with open(fname, "w") as f:
        f.write("".join(lines))


def _build_requirements_url(branch, inst):
    """Build requirements URL or local path."""
    if inst in (devel, devel_server):
        return CDIR
    return ('https://raw.githubusercontent.com/'
            f'gem/oq-engine/{branch}/')


def _install_engine(pycmd, version, inst,
                    from_fork, noupgrade):
    """Install engine requirements and the engine."""
    branch = get_requirements_branch(
        version, inst, from_fork)
    mac = "_" + platform.machine()
    if sys.platform != "darwin":
        mac = ""
    req_pre = _build_requirements_url(branch, inst)
    req = (f"{req_pre}/requirements-py"
           f"{PYVER[:2]}-{PLATFORM[sys.platform]}{mac}.txt")
    subprocess.check_call(
        [pycmd, "-m", "pip", "install",
         "--force-reinstall", "--trusted-host", "wheelhouse.openquake.org",
         "--trusted-host", "raw.githubusercontent.com", "-r", req])
    if inst in (devel, devel_server):
        subprocess.check_call([pycmd, "-m", "pip", "install", "-e", CDIR])
    elif version is None:
        subprocess.check_call(
            [pycmd, "-m", "pip", "install"] +
            ([] if noupgrade else ["--upgrade"]) + ["openquake.engine"])
    else:
        commit = latest_commit(version)
        print("Installing commit", commit)
        with tempfile.TemporaryDirectory() as tmp:
            custom_env = os.environ.copy()
            custom_env["TMPDIR"] = tmp
            custom_env["TEMP"] = tmp
            subprocess.check_call(
                [pycmd, "-m", "pip", "install"] +
                ([] if noupgrade else ["--upgrade"]) +
                [_git_branch_url(commit), "--no-clean"],
                env=custom_env)
        fix_version(commit, inst.VENV)


def _setup_config_and_oq(inst):
    """Create openquake.cfg and symlink oq."""
    sep = "bin" if sys.platform != "win32" else "Scripts"
    oqreal = os.path.join(inst.VENV, sep, "oq")
    if inst in (server, devel_server):
        if os.path.exists(inst.CFG):
            print(f"old file {inst.CFG}; not overwritten, "
                  f"consider updating with\n{inst.CONFIG}")
        else:
            with open(inst.CFG, "w") as cfg:
                cfg.write(inst.CONFIG)
            print(f"Created {inst.CFG}")
    if inst in (server, devel_server) \
            and not os.path.exists(inst.OQ):
        os.symlink(oqreal, inst.OQ)
    return oqreal


def _compile_numba_and_upgrade_db(oqreal, inst):
    """Compile numba modules and upgrade the database."""
    print("Compiling python/numba modules")
    subprocess.run([oqreal, "--version"])
    # compile numba and upgrade db
    cmd = [oqreal, "engine", "--upgrade-db"]
    if inst not in (user, devel):
        cmd = ['sudo', '-u', 'openquake'] + cmd
    subprocess.run(cmd)


def _create_systemd_services(inst):
    """Create systemd services for server/devel_server."""
    if inst not in (server, devel_server):
        return
    systemd_dir = "/run/systemd/system"
    if not os.path.exists(systemd_dir):
        return
    service_path = "/etc/systemd/system/"
    service_path += "openquake-webui.service"
    if not os.path.exists(service_path):
        with open(service_path, "w") as f:
            srv = SERVICE.format(
                service="webui",
                OQDATA=inst.OQDATA,
                afterservice="network.target",
                command="webui -s start")
            f.write(srv)
    subprocess.check_call(["systemctl", "enable",
                           "--now", "openquake-webui.service"])
    subprocess.check_call(["systemctl", "start", "openquake-webui.service"])


def _print_success(oqreal, inst):
    """Print success message and activation instructions."""
    if inst in (user, devel):
        if sys.platform == "win32":
            print(f"Please activate with "
                  f"{inst.VENV}\\Scripts\\activate.bat "
                  f"(CMD) or .ps1 (PowerShell)")
        else:
            print(f"Please activate with source "
                  f"{inst.VENV}/bin/activate")
    if inst in (user, server):
        path = os.path.join(
            inst.VENV, "demos", "hazard",
            "AreaSourceClassicalPSHA", "job.ini")
        print(f"installed successfully. Test with\n"
              f"{oqreal} engine --run {path}")


def install(inst, version, from_fork, novenv, noupgrade):
    """Install the engine in one of the three possible modes."""
    # create the user `openquake` in server mode
    if inst in (server, devel_server):
        try:
            pwd.getpwnam("openquake")
        except KeyError:
            subprocess.check_call(
                ["useradd", "-m", "-U", "openquake"])
            print("Created user openquake")
    # Create the oqdata directory if it doesn't exist
    if not os.path.exists(inst.OQDATA):
        os.makedirs(inst.OQDATA)
        if inst in (server, devel_server):
            subprocess.check_call(["chown", "openquake", inst.OQDATA])
    if not novenv:
        ensure(pyvenv=inst.VENV)
        print(f"Created {inst.VENV}")
    pycmd = _get_python_cmd(inst)
    _ensure_pip(pycmd, noupgrade)
    errors = standalone(inst, "install")
    _install_engine(pycmd, version, inst, from_fork, noupgrade)
    oqreal = _setup_config_and_oq(inst)
    _compile_numba_and_upgrade_db(oqreal, inst)
    errors += standalone(inst, "postinstall")
    _create_systemd_services(inst)
    _print_success(oqreal, inst)
    return errors


def remove(inst):
    """Remove the virtualenv and server services."""
    if inst in (server, devel_server):
        for service in ["webui"]:
            svc = f"openquake-{service}.service"
            sp = "/etc/systemd/system/" + svc
            if os.path.exists(sp):
                subprocess.check_call(
                    ["systemctl", "stop", svc])
                print("stopped " + svc)
                os.remove(sp)
                print("removed " + svc)
        subprocess.check_call(
            ["systemctl", "daemon-reload"])
    if os.path.exists(inst.VENV):
        shutil.rmtree(inst.VENV)
        print(f"{inst.VENV} removed")
    if inst in (server, devel_server) \
            and os.path.exists(server.OQ):
        os.remove(server.OQ)
        print(f"{server.OQ} removed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "inst",
        choices=["server", "user", "devel", "devel_server"],
        nargs="?",  help="the kind of installation you want")
    parser.add_argument("--venv", help="venv directory")
    parser.add_argument("--novenv", action="store_true",
                        help="keep the current python environment")
    parser.add_argument("--noupgrade", action="store_true",
                        help="not use '--upgrade' in pip install calls")
    parser.add_argument("--remove", action="store_true",
                        help="disinstall the engine")
    parser.add_argument("--version",
                        help="version to install (default stable)")
    # NOTE: This flag should be set when installing
    #       the engine from an action
    #       triggered by a fork
    parser.add_argument(
        "--from_fork", dest="from_fork",
        action="store_true", help=argparse.SUPPRESS)
    parser.set_defaults(from_fork=False)
    args = parser.parse_args()
    if args.inst:
        # set inst to the class named as the string
        # args.inst
        inst = globals()[args.inst]
        before_checks(inst, args, parser.format_usage())
        if args.remove:
            remove(inst)
        else:
            errors = install(
                inst, args.version,
                args.from_fork, args.novenv,
                args.noupgrade)
            if errors:
                # NB: even if one of the tools is
                # missing, the engine will work
                sys.exit('\n'.join(errors))
    else:
        sys.exit("Please specify the kind of installation")
