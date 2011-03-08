# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.



import os, sys, re, random
from fabric.api import env, run, sudo, local, cd
from fabric.state import output as fabric_output

CELLAR_PATH = "/usr/local/Cellar"
PYTHON_PATH = "%s/python/2.6.5" % CELLAR_PATH
SITE_PKG_PATH = "~/.virtualenvs/openquake/lib/python2.6/site-packages/"

VIRTUALENV_PACKAGES = ["lxml", "pyyaml", "sphinx", "shapely",
    "python-gflags", "guppy",
    "libLAS", "numpy", "scipy", "celery==2.0.3",
    "nose", "django", "redis"]

"""
This fab file assists with setting up a developer's environment.

There are two primary functions implemented currently:
    boostrap - installs required libs and sets up the openquake virtual
environment
    virtualenv - only sets up the openquake virtual environment (useful if a
developer already has dependencies installed)
"""


def bootstrap():
    """Prior to running this bootstrap, you may need to perform a few 
    prerequisite steps. See platform notes below.

    Mac OS X:
        * None yet determined

    Ubuntu (10.04):
        * sudo apt-get update
        * sudo apt-get install python-setuptools build-essential python-dev postgresql-8.4
        * sudo easy_install fabric
        * sudo easy_install pip
    """
    _assert_we_can_remote_login()
    
    def _detect_os():
        platforms = {'Darwin': _bootstrap_osx, 'Linux': _bootstrap_linux}
        return platforms.get(run('uname'), _bootstrap_other)

    bootstrap_fn = _detect_os()      # bootstrap_fn = _bootstrap_linux
    bootstrap_fn()                   # _bootstrap_linux()


def virtualenv():
    """This method installs virtualenv, virtualenvwrapper, and pre-built
virtual environment tar ball specific to the platform.
    """
    
    _assert_we_can_remote_login()
 
    def _detect_os():
        platforms = {'Darwin': _virtual_env_osx, 'Linux': _virtual_env_linux}
        return platforms.get(run('uname'), _virtual_env_other)

    venv_fn = _detect_os()
    venv_fn()


def _virtual_env_osx():
    _setup_venv("http://opengem.cloudfed.com/\
documents/10156/11140/virtualenvs_osx.tar.gz")


def _virtual_env_linux():
    def _detect_distro():
        if _distro_is_ubuntu():
            return _virtual_env_ubuntu
        else:
            return _virtual_env_other

    venv_fn = _detect_distro()
    venv_fn() 


def _setup_venv(venv_tar_url):
    """The process of downloading and extracting the virtual env tarball is the
same for Ubuntu and OSX (just a different tarball).
    """ 
    if not _pip_is_installed():
        print "You need to install pip to continue with virtualenv setup."
        print "Visit http://pip.openplans.org/ for more information."
        sys.exit()
    # check the user's home dir for an existing virtualenv config
    # if one already exists, abort.
    if os.path.exists(os.path.join(os.environ['HOME'], ".virtualenvs/")):
        print "Virtual environment configuration already",
        print "exists in: ~/.virtualenvs"
        sys.exit()
    _pip_install("virtualenv")
    _pip_install("virtualenvwrapper")
    
    # grab the virtualenv tar from Liferay:
    venv_file_name = "virtualenvs.tar.gz"
    print "Downloading virtualenv package from:\n %s" % venv_tar_url
    print "This may take a few minutes."
    
    # curl the virtualenv tar to the user's home dir
    run("curl -s --create-dirs %s -o ~/%s" % (venv_tar_url, venv_file_name))

    # local virtual env dir 
    local_venv_path = "~/.virtualenvs/"

    # extract the tar (creating a ~/.virtualenv dir)
    with cd('~'):
        run("tar -xzf %s" % venv_file_name)

    # chown and chgrp the virtual env files
    # to the current user and group, respectively
    run("chown -R `id -un` %s" % local_venv_path)
    run("chgrp -R `id -g` %s" % local_venv_path)
    sys.exit()


def _virtual_env_ubuntu():
    _setup_venv("http://opengem.cloudfed.com/\
documents/10156/11140/virtualenvs_ubuntu.tar.gz")
    

def _virtual_env_other():
    print "Platform not currently supported."
    sys.exit()

def _bootstrap_other():
    pass

def _distro_is_ubuntu():
    distro = run("lsb_release -is")
    return distro == "Ubuntu"


def _bootstrap_linux():
 
    def _detect_distro():
        if _distro_is_ubuntu():
            version = run("lsb_release -a | grep Release | sed -e 's/Release: *//'")

            if not float(version) >= 9.04:
                raise "Included python is too old. Upgrade your distro, dude."

            return _bootstrap_ubuntu
        #elif distro == "Fedora":
        #    return _bootstrap_fedora
        else:
            raise "I don't know this distro."

    def _bootstrap_ubuntu():
        
        # we need easy_install
        if not run('which easy_install'):
            print "easy_install is required, but could not be found."
            print "Visit http://pypi.python.org/pypi/setuptools for more info."
            sys.exit()
        apt_packages = ["default-jdk", "build-essential", "python-matplotlib",
                        "erlang-inets", "erlang-os-mon", "erlang-nox",
                        "python2.6-dev", "python-setuptools", "python-pip",
                        "gfortran", "postgresql", "postgis", "python2.6",
                        "libxml2-dev", "libxslt-dev", "libblas-dev",
                        "liblapack-dev", "pylint", "unzip", "apt-file"]
        gdal_packages = ["gdal-bin", "libgeos-dev", "libgdal1-dev", "python-gdal"]
        pip_packages = ["virtualenv", "virtualenvwrapper",]
        virtualenv_packages = ["lxml", "pyyaml", "sphinx", "shapely", 
                               "python-gflags", "guppy", 
                               "libLAS", "numpy", "scipy", "celery",
                               "nose", "django", "stdeb"] 

        _apt_install(" ".join(apt_packages))
        _pip_install(" ".join(pip_packages))

        # For Ubuntu 10.04, we need to install redis-server and rabbitmq-server
        # from src/deb packages to get the versions we want
        _ubuntu_install_rabbit()
        _ubuntu_install_redis()

        # Build the virtual environment
        with cd("~"):
            if not ls(".virtualenvs"):
                run("mkdir -p .virtualenvs")
                run("%s; mkvirtualenv openquake" % _ubuntu_virtualenv_source())
      
        if "PYTHONPATH" not in _warn_only_run("cat ~/.profile"): 
            run('echo export PYTHONPATH="%s:$PYTHONPATH" >> ~/.profile' % SITE_PKG_PATH)
	
        sudo("rm -rf ~/build/")

        _configure_postgresql(pgsql_path="/usr/lib/postgresql/8.4/bin/")
        _start_postgresql(initd="/etc/init.d/postgresql-8.4")
        _adduser_posgresql()
        _createdb_postgresql()

        run('source ~/.profile')
        venv_packages = VIRTUALENV_PACKAGES
        for venv_package in venv_packages:
            _pip_install(venv_package, virtualenv="openquake")

        # GDAL.
        _apt_install(" ".join(gdal_packages))
        # GDAL installs to /usr/lib/python2.6/
        # copy it to the virtualenv
        if ls("/usr/lib/python2.6/dist-packages/osgeo"):
            run("cp -R /usr/lib/python2.6/dist-packages/osgeo/ \
~/.virtualenvs/openquake/lib/python2.6/site-packages/")
        else:
            print "Couldn't find osgeo module; something is wrong with GDAL."
            sys.exit()
        #download and install geohash
        geohash_url = "http://python-geohash.googlecode.com/files/python-geohash-0.6.tar.gz"
        geohash_file = "python-geohash-0.6.tar.gz"
        with cd("/tmp"):
            if not ls(geohash_file):
                _curl(geohash_url, geohash_file)
                run("tar xzf %s" % geohash_file)
                with cd("python-geohash-0.6"):
                    run("python setup.py install --prefix=~/.virtualenvs/openquake")

        # Install jpype from source
        
        # First, try to find a jvm. Search the most likely places.
        jvm_locs = ["/usr/lib/jvm/java-6-sun", "/usr/lib/jvm/default-java/"]
        jvm = ''
        # look for an existing jvm dir
        for loc in jvm_locs:
            if ls(loc):
                # if the jvm dir exists, use it
                jvm = loc
		# set java home in .profile
		if "JAVA_HOME" not in _warn_only_run("cat ~/.profile"):
			run('echo export JAVA_HOME="%s:$JAVA_HOME" >> ~/.profile' % jvm)
                break
        _install_jpype_from_source(java_home=jvm)
        # Add virtualenv source to .profile
        if "virtualenvwrapper.sh" not in _warn_only_run("cat ~/.profile"):
            run("echo %s >> ~/.profile" % \
                _ubuntu_virtualenv_source().replace('\n', ''))

    def _bootstrap_fedora():
        pass

    bootstrap_fn = _detect_distro()
    bootstrap_fn()

def _ubuntu_install_rabbit():
    env.warn_only = True
    print "Installing rabbitmq-server..."
    rabbit_deb = 'rabbitmq-server_2.2.0-1_all.deb'
    rabbit_url = 'http://www.rabbitmq.com/releases/rabbitmq-server/v2.2.0/%s' \
% rabbit_deb
    _deb_install(rabbit_url, rabbit_deb)
    # now configure rabbit
    _ubuntu_config_rabbit()
    print "Finished installing rabbitmq-server."
    env.warn_only = False

def _ubuntu_config_rabbit(): 
    env.warn_only = True
    rabbit_cfg = ['rabbitmqctl add_user celeryuser celery',
        'rabbitmqctl add_vhost celeryvhost',
        'rabbitmqctl set_permissions -p celeryvhost celeryuser ".*" ".*" ".*"',
        '/etc/init.d/rabbitmq-server restart']
    for cfg in rabbit_cfg:
        sudo(cfg)
    env.warn_only = False

def _ubuntu_install_redis():
    env.warn_only = True
    print "Installing redis-server..."
    redis_deb = 'redis-server_2.0.1-2_amd64.deb'
    redis_url = 'http://ubuntu.linux-bg.org/ubuntu//pool/universe/r/redis/%s' \
% redis_deb
    _deb_install(redis_url, redis_deb)
    sudo('/etc/init.d/redis-server restart')
    env.warn_only = False
    print "Finished installing redis-server."

def _deb_install(url, file):
    with cd('~'):
        run('curl %s -o %s' % (url, file))
        sudo('dpkg -i %s' % file)
        # clean up
        run('rm %s' % file)
           
def _bootstrap_osx():
    """
    Bootstrap development environment in MacOSX. Requires HomeBrew.
    
    Installs:
        python2.6.x
        pip
    """
    
    # We really don't care about warnings.
    fabric_output.warnings = False

    if not _homebrew_is_installed():
        print "You need to install Homebrew to bootstrap osx"
        print 
        print "Suggestion:"
        print 'ruby -e "$(curl -fsS https://gist.github.com/raw/323731/install_homebrew.rb)"'
        sys.exit()

    if not run('which easy_install'):
        print "easy_install is required, but could not be found."
        print "Visit http://pypi.python.org/pypi/setuptools for more info."
        sys.exit() 
    
    # Install python2.6
    _install_python()

    _homebrew_install("pip")
    _homebrew_install("redis")

    # Install rabbitmq
    _homebrew_install("rabbitmq")
    _start_rabbitmq()
    _configure_rabbitmq_auth()

    # Install virtualenv
    _pip_install("virtualenv")

    # Install virtualenvwrapper via pip and homebrew
    # We want homebrew because it puts the stuff in a
    # nice path
    _pip_install("virtualenvwrapper")

    url = "https://gist.github.com/raw/635189/9f483e4969149a1fe1ed81f7ae33f19dfbc328bf/gistfile1.txt"

    with cd("/usr/local/Library/Formula"):
        if not ls("virtualenvwrapper.rb"): 
            sudo("curl %s > virtualenvwrapper.rb" % url)

    _homebrew_install("virtualenvwrapper")

    # Build the environment
    with cd("~"):
        if not ls(".virtualenvs"):
            run("mkdir -p .virtualenvs")
            run("mkvirtualenv openquake")

    easy_install_packages = ["matplotlib"]
    
    for pkg in easy_install_packages:
        _easy_install(pkg, to_venv=True)
    _pip_install(" ".join(VIRTUALENV_PACKAGES), virtualenv="openquake")


    #download and install geohash
    geohash_url = "http://python-geohash.googlecode.com/files/python-geohash-0.6.tar.gz"
    geohash_file = "python-geohash-0.6.tar.gz"
    with cd("/tmp"):
        if not ls(geohash_file):
            _curl(geohash_url, geohash_file)
            run("tar xzf %s" % geohash_file)
            with cd("python-geohash-0.6"):
                run("python setup.py install --prefix=~/.virtualenvs/openquake")

    # download and install gfortran
    gfortran_url = "http://r.research.att.com/gfortran-4.2.3.dmg"
    gfortran_dmg = "gfortran-4.1.2.dmg"
    with cd("/tmp"):
        if not _warn_only_run("which gfortran"):
            if not ls(gfortran_dmg):
                _curl(gfortran_url, gfortran_dmg)

            _attach_and_install(gfortran_dmg, "GNU\ Fortran\ 4.2.3", "gfortran.pkg")

    # We install numpy from source because we have to remove the ppc64 line.
    _install_numpy_from_source()
    _pip_install("scipy", virtualenv="openquake")

    # Install gdal
    _homebrew_install("gdal")
    _install_gdal_from_dmg()
    with cd("/tmp"):
        if not ls("/usr/local/lib/swq.h"):
            _curl("http://svn.osgeo.org/gdal/branches/1.7/gdal/ogr/swq.h", "swq.h")
            sudo("mv swq.h /usr/local/lib/swq.h")

    _pip_install("gdal", virtualenv="openquake")

    # Install jpype from source
    _install_jpype_from_source()

    # Add virtualenv source to .profile
    if "virtualenvwrapper.sh" not in _warn_only_run("cat ~/.profile"):
        f = open("%s/.profile" % os.environ['HOME'], 'a')
        f.write(_osx_virtualenv_source())
        f.close()


def teardown_osx():
    """
    Destroy the virtualenv
    """


#
# Helper methods
#

def _attach_and_install(dmg, volume, package):
    run("hdiutil attach %s" % dmg )
    sudo("installer -pkg /Volumes/%s/%s -target /" % (volume, package))
    run("hdiutil detach %s" % volume)

def _curl(url, filename):
    run("curl %s > %s" % (url, filename))

def _start_celery():
    if not run("ps aux | grep celeryd"):
        run("celeryd &")

def _start_rabbitmq():
    sudo("nohup /usr/local/sbin/rabbitmq-server &")


def _start_postgresql(initd=None):
    if not _warn_only_run("ps aux | grep [p]ostgres"):
        if not initd:
            run("postgres -D /tmp/pgsql &")
        else:
            sudo("%s start" % initd)

def _configure_rabbitmq_auth():
    env.warn_only = True
    sudo('/usr/local/sbin/rabbitmqctl add_user celeryuser celery')
    sudo('/usr/local/sbin/rabbitmqctl add_vhost celeryvhost')
    sudo('/usr/local/sbin/rabbitmqctl set_permissions -p celeryvhost celeryuser ".*" ".*" ".*"')
    env.warn_only = False


def _configure_postgresql(pgsql_path=""):
    if not ls("/tmp/pgsql"):
        run("%sinitdb -U `whoami` /tmp/pgsql" % pgsql_path)

def _adduser_posgresql():
    username=run("whoami")
    env.warn_only = True
    sudo("su - postgres -c \"createuser -s %s\"" % username)
    env.warn_only = False

def _createdb_postgresql():
    if not _warn_only_run("psql -l | grep openquake"):
        run("createdb openquake")
    

def _install_gdal_from_dmg():
    with cd("/tmp"):
        gdal_url = "http://www.kyngchaos.com/files/software/frameworks/GDAL_Complete-1.7.dmg"
        gdal_file = "GDAL_Complete-1.7.dmg"
        if not ls(gdal_file):
            _curl(gdal_url, gdal_file)
            _attach_and_install(gdal_file, "GDAL\ Complete", "GDAL\ Complete.pkg")

def _install_jpype_from_source(java_home=None):
    jpype_url="http://softlayer.dl.sourceforge.net/project/jpype/JPype/0.5.4/JPype-0.5.4.1.zip"
    jpype_file = "JPype-0.5.4.1.zip"

    if java_home:
        java_home = "JAVA_HOME=%s" % java_home
    else:
        java_home = ""

    with cd("/tmp"):
        if not ls(jpype_file):
            _curl(jpype_url, jpype_file) 
            run("unzip %s" % jpype_file)
            with cd("JPype-0.5.4.1"):
                run("%s python setup.py install --prefix=~/.virtualenvs/openquake" % java_home)

def _install_numpy_from_source():
    with cd("/tmp"):
        diffurl = ("https://gist.github.com/raw/636065/"

                   "b1302efeeea6bdd716cfdbb0ba351f2d4cc758f4/numpy_ppc.diff")

        if not ls("numpy"):
            run("svn co http://svn.scipy.org/svn/numpy/trunk numpy")
            with cd("numpy"):
                run("curl %s | patch -p0" % diffurl)
                run("python setup.py install --prefix=~/.virtualenvs/openquake")
            # Remove the svn directory
            run("rm -rf numpy")

def _warn_only_run(command):
    env.warn_only = True
    output = run(command)
    env.warn_only = False
    return output

def _homebrew_is_installed():
    return _warn_only_run("which brew")

def _pip_is_installed():
    return _warn_only_run("which pip")

def _homebrew_exists(package):
    output = _warn_only_run("brew info %s" % package)

    if re.search("not installed", output, re.IGNORECASE):
        return False

    return True

def _easy_install(package, to_venv=False):
    """Set to_venv=True to install this package to your virtual environment."""
    if to_venv:
        return sudo("PYTHONPATH=%s easy_install \
--install-dir=~/.virtualenvs/openquake/lib/python2.6/site-packages/ %s" \
% (SITE_PKG_PATH, package), pty=True)
    else:
        return sudo("easy install %s" % package, pty=True)

def _apt_install(package):
    return sudo("DEBIAN_FRONTEND=noninteractive apt-get -q -y install %s" % package, pty=True)

def _homebrew_install(package):
    if not _homebrew_exists(package):
        return sudo("brew install %s" % package, pty=True)

def _homebrew_uninstall(package):
    output = run("brew list %s" % package)
    if output:
        return sudo("brew uninstall %s" % package)


def _ubuntu_virtualenv_source():
    return "\nsource /usr/local/bin/virtualenvwrapper.sh"

def _osx_virtualenv_source():
    # todo(chris) THIS IS SUPER UGLY. 
    return """
export VIRTUALENVWRAPPER_PYTHON=%s/bin/python
export PATH=$PATH:%s/bin/
source %s/virtualenvwrapper/2.1.1/bin/virtualenvwrapper.sh
    """ % (PYTHON_PATH, PYTHON_PATH, CELLAR_PATH)

def _pip_installed(python_package, virtualenv=None):
    python_site_dir="/usr/local/lib/python2.6/site-packages/"
    if virtualenv:
        python_site_dir="~/.virtualenvs/openquake/lib/python2.6/site-packages/"

    with cd(python_site_dir):
        env.warn_only = True
        res = ls("%s*" % python_package)
        env.warn_only = False
        return res


def _pip_install(python_package, virtualenv=None, version=None):
    if not _pip_installed(python_package, virtualenv):
        if version:
            install_package="pip install %s==%s" % (python_package, version)
        else:
            install_package = "pip install %s" % python_package
        if virtualenv: 
            install_package = "%s -E ~/.virtualenvs/%s" % (install_package, 
                                                           virtualenv)

        if not virtualenv:
            return sudo(install_package)
        else:
            return run(install_package)

def ls(file):
    return _warn_only_run("ls %s" % file)

def _install_python():
    with cd("/usr/local/Library/Formula"):
        if not ls("python2.6.rb"): 
            # Install Python
            print """
                While we're installing python via brew, we'll be modifying your python
                Formula so we can install python2.6. We'll move it back after. This means
                that to uninstall python2.6 with brew, you'll need to manually move it 
                back.
            """


            sudo('curl "https://gist.github.com/raw/635038/a3d24cbe"'
                 '> python2.6.rb')

            if ls("python.rb"):
                sudo("mv python.rb{,-bootstrap_osx}")
                sudo("cp python{2.6,}.rb")

    _homebrew_install("python")

def _assert_we_can_remote_login():
    """Remote login is required for running bootstrap/virtualenv setup  on 
    localhost. This function verifies that remote login is enabled.
    If it is not, the script will print an error message and exit.

    If fabric's env.hosts == ['localhost'], no check is performed.""" 
   
    if env.hosts != ['localhost']:
        return
    
    with os.popen("uname") as fp:
        platform = fp.read()
    platform = platform.strip('\n')
 
    REMOTE_LOGIN_NOT_ENABLED = "It looks like remote login is not enabled on \
the local machine."
    
    def _osx():
        with os.popen("sudo systemsetup -getremotelogin") as fp:
            result = fp.read()
    
        if result != 'Remote Login: On\n':
            print
            print REMOTE_LOGIN_NOT_ENABLED
            print
            print "You need to enable it to continue."
            print "To do so, select Apple -> System \
Preferences -> Sharing and make sure 'Remote Login' is checked."
            sys.exit()

    def _linux():
        with os.popen("ps aux | grep [s]shd") as fp:
            result = fp.read()

        if result == '':
            print
            print REMOTE_LOGIN_NOT_ENABLED
            print
            print "Please start sshd and try again."
            sys.exit()

    if platform == 'Darwin':
        _osx()
    elif platform == 'Linux':
        _linux()
    else:
        print
        print "Unknown platform '%s'" % platform
        print
        print "This is probably a bug."
        sys.exit()
