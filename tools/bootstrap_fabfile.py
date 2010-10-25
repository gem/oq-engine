import os, re, sys, random
from fabric.api import run, env, sudo, local, put, abort, prompt, cd
from fabric.state import output as fabric_output

CELLAR_PATH = "/usr/local/Cellar"
PYTHON_PATH = "%s/python/2.6.5" % CELLAR_PATH

def bootstrap():
    def _detect_os():
        if sys.platform == 'darwin':
            return _bootstrap_osx
        elif sys.platform == 'linux2':
            return _bootstrap_linux
        else:
            return _bootstrap_other
    bootstrap_fn = _detect_os()
    bootstrap_fn()


def _bootstrap_linux():
    print "Linux OS dev env bootstrapping is not yet implemented." 
    print "Maybe you want to do this instead?"

    def _detect_distro():
        pass

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
        print "You need to install Homebrew to bootstrap_osx"
        print 
        print 'ruby -e "$(curl -fsS http://gist.github.com/raw/323731/install_homebrew.rb)"'
        sys.exit()

    # Install python2.6
    _install_python()

    _homebrew_install("pip")

    # Install rabbitmq
    _homebrew_install("rabbitmq")
    _start_rabbitmq()
    _configure_rabbitmq_auth()

    # Install memcached
    _homebrew_install("memcached")
    with cd("/tmp"):
        libmcd_url = "http://download.tangent.org/libmemcached-0.38.tar.gz"
        libmcd_file = "libmemcached-0.38.tar.gz"
        if not ls(libmcd_file):
            _curl(libmcd_url, libmcd_file)
            run("tar xzf %s" % libmcd_file)
            with cd("libmemcached-0.38"):
                run("./configure `brew diy`")
                sudo("make && make install && brew ln libmemcached")

    # Install PostgreSQL
    _homebrew_install("postgresql")
    _homebrew_install("postgis")
    _configure_postgresql()
    _start_postgresql()
    _createdb_postgresql()

    # Install virtualenv
    _pip_install("virtualenv")

    # Install virtualenvwrapper via pip and homebrew
    # We want homebrew because it puts the stuff in a
    # nice path
    _pip_install("virtualenvwrapper")

    url = "http://gist.github.com/raw/635189/9f483e4969149a1fe1ed81f7ae33f19dfbc328bf/gistfile1.txt"
    with cd("/usr/local/Library/Formula"):
        if not ls("virtualenvwrapper.rb"): 
            sudo("curl %s > virtualenvwrapper.rb" % url)

    _homebrew_install("virtualenvwrapper")

    # Build the environment
    with cd("~"):
        if not ls(".virtualenvs"):
            run("mkdir -p .virtualenvs")
            run("%s mkvirtualenv opengem" % _virtualenv_source())

    _pip_install("lxml", virtualenv="opengem")
    _pip_install("pyyaml", virtualenv="opengem")
    _pip_install("sphinx", virtualenv="opengem")
    _pip_install("shapely", virtualenv="opengem")
    _pip_install("eventlet", virtualenv="opengem")
    _pip_install("python-gflags", virtualenv="opengem")
    _pip_install("guppy", virtualenv="opengem")
    _pip_install("celery", virtualenv="opengem")
    _pip_install("nose", virtualenv="opengem")
    _pip_install("django", virtualenv="opengem")
    _pip_install("ordereddict", virtualenv="opengem")
    _pip_install("pylibmc", version="0.9.2", virtualenv="opengem")
    _pip_install("pylint", virtualenv="opengem")

    # Install OpenSHA-lite
    opensha_url = "http://opengem.globalquakemodel.org/job/OpenSHA-Lite/lastSuccessfulBuild/artifact/dist/opensha-lite.jar"
    opensha_file = "opensha-lite.jar"
    print run("pwd")
    with cd("../lib"):
        _curl(opensha_url, opensha_file)

    #download and install geohash
    geohash_url = "http://python-geohash.googlecode.com/files/python-geohash-0.6.tar.gz"
    geohash_file = "python-geohash-0.6.tar.gz"
    with cd("/tmp"):
        if not ls(geohash_file):
            _curl(geohash_url, geohash_file)
            run("tar xzf %s" % geohash_file)
            with cd("python-geohash-0.6"):
                run("python setup.py install --prefix=~/.virtualenvs/opengem")

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
    _pip_install("scipy", virtualenv="opengem")

    # Install gdal
    _homebrew_install("gdal")
    _install_gdal_from_dmg()
    with cd("/tmp"):
        if not ls("/usr/local/lib/swq.h"):
            _curl("http://svn.osgeo.org/gdal/branches/1.7/gdal/ogr/swq.h", "swq.h")
            sudo("mv {,/usr/local/lib/}swq.h")

    _pip_install("gdal", virtualenv="opengem")

    # Install jpype from source
    _install_jpype_from_source()

    # Add virtualenv source to .profile
    if "virtualenvwrapper.sh" not in _warn_only_run("cat ~/.profile"):
        f = open("%s/.profile" % os.environ['HOME'], 'a')
        f.write(_virtualenv_source())
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
    run("installer -pkg /Volumes/%s/%s -target /" % (volume, package))
    run("hdiutil detach %s" % volume)

def _curl(url, filename):
    run("pwd")
    run("curl %s > %s" % (url, filename))

def _start_celery():
    if not run("ps aux | grep celeryd"):
        run("celeryd &")

def _start_rabbitmq():
    sudo("nohup /usr/local/sbin/rabbitmq-server &")

def _start_postgresql():
    if not run("ps aux | grep postgres"):
        run("postgres -D /tmp/pgsql &")

def _configure_rabbitmq_auth():
    env.warn_only = True
    sudo('/usr/local/sbin/rabbitmqctl add_user celeryuser celery')
    sudo('/usr/local/sbin/rabbitmqctl add_vhost celeryvhost')
    sudo('/usr/local/sbin/rabbitmqctl set_permissions -p celeryvhost celeryuser ".*" ".*" ".*"')
    env.warn_only = False

def _configure_postgresql():
    if not ls("/tmp/pgsql"):
        run("initdb /tmp/pgsql")

def _createdb_postgresql():
    if not run("psql -l | grep opengem"):
        run("createdb opengem")
    

def _install_gdal_from_dmg():
    with cd("/tmp"):
        gdal_url = "http://www.kyngchaos.com/files/software/frameworks/GDAL_Complete-1.7.dmg"
        gdal_file = "GDAL_Complete-1.7.dmg"
        if not ls(gdal_file):
            _curl(gdal_url, gdal_file)
            _attach_and_install(gdal_file, "GDAL\ Complete", "GDAL\ Complete.pkg")

def _install_jpype_from_source():
    jpype_url="http://softlayer.dl.sourceforge.net/project/jpype/JPype/0.5.4/JPype-0.5.4.1.zip"
    jpype_file = "JPype-0.5.4.1.zip"
    with cd("/tmp"):
        if not ls(jpype_file):
            _curl(jpype_url, jpype_file) 
            run("unzip %s" % jpype_file)
            with cd("JPype-0.5.4.1"):
                run("python setup.py install --prefix=~/.virtualenvs/opengem")

def _install_numpy_from_source():
    with cd("/tmp"):
        diffurl = ("http://gist.github.com/raw/636065/"
                   "b1302efeeea6bdd716cfdbb0ba351f2d4cc758f4/numpy_ppc.diff")

        if not ls("numpy"):
            run("svn co http://svn.scipy.org/svn/numpy/trunk numpy")
            with cd("numpy"):
                run("curl %s | patch -p0" % diffurl)
                run("python setup.py install --prefix=~/.virtualenvs/opengem")
            # Remove the svn directory
            run("rm -rf numpy")

def _warn_only_run(command):
    env.warn_only = True
    output = run(command)
    env.warn_only = False
    return output

def _homebrew_is_installed():
    return _warn_only_run("which brew")

def _homebrew_exists(package):
    output = _warn_only_run("brew info %s" % package)

    if re.search("not installed", output, re.IGNORECASE):
        return False

    return True

def _homebrew_install(package):
    if not _homebrew_exists(package):
        print env.warn_only
        return sudo("brew install %s" % package, pty=True)

def _homebrew_uninstall(package):
    output = run("brew list %s" % package)
    if output:
        return sudo("brew uninstall %s" % package)

def _virtualenv_source():
    # todo(chris) THIS IS SUPER UGLY. 
    return """
export VIRTUALENVWRAPPER_PYTHON=%s/bin/python
export PATH=$PATH:%s/bin/
source %s/virtualenvwrapper/2.1.1/bin/virtualenvwrapper.sh
    """ % (PYTHON_PATH, PYTHON_PATH, CELLAR_PATH)

def _pip_installed(python_package, virtualenv=None):
    python_site_dir="/usr/local/lib/python2.6/site-packages/"
    if virtualenv:
        python_site_dir="~/.virtualenvs/opengem/lib/python2.6/site-packages/"

    with cd(python_site_dir):
        print run("pwd")
        return ls("%s*" % python_package)

def _pip_install(python_package, virtualenv=None, version=None):
    if not _pip_installed(python_package, virtualenv):
        if version:
            install_package="pip install %s==%s" % (python_package, version)
        else:
            install_package = "pip install %s" % python_package
        if virtualenv: 
            install_package = "%s -E ~/.virtualenvs/%s" % (install_package, 
                                                           virtualenv)
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

            sudo('curl "http://gist.github.com/raw/635038/a3d24cbe"'
                 '> python2.6.rb')

            if ls("python.rb"):
                sudo("mv python.rb{,-bootstrap_osx}")
                sudo("cp python{2.6,}.rb")

    if _homebrew_install("python"):
        # Move them back
        sudo("mv python{,2.6}")
        sudo("mv python.rb{-bootstrap_osx,}")
