OpenGEM System
==============

Dependencies
------------

For the most part the Python packages in here can be installed using `pip`
(python-pip on ubuntu) or your favorite package manager.


 * libxslt-dev
 * gfortran
 * python-numpy
 * python-scipy
 * libmemcache-dev
 

On OS X a good way to install the pieces that are not Python (if you don't
already use MacPorts or Fink) is called homebrew: http://mxcl.github.com/homebrew/

* gdal
 * Brew install gdal itself, then
 * sudo pip install gdal (FAILS, so):
 * Use the package from http://www.kyngchaos.com/software:frameworks
* osgeo (pip install)
* eventlet
* jpype
* lxml
* PyYAML
* python-gflags
* RabbitMQ (Installed using brew install rabbitmq)
* SciPy
  * You will need gfortran, for os x that is at: http://r.research.att.com/gfortran-4.2.3.dmg 
  * After that `pip install scipy` should work.
  * If it doesn't and there is an error about ppc64... well it is more complex,
    see Troubleshooting
* Shapely
  * requires geos (c library, also called libgeos)
* Sphinx (for building documentation only)
* Guppy (http://guppy-pe.sourceforge.net)
* Redis 2.x or greater (http://code.google.com/p/redis/downloads/list)

You'll need to mess with PYTHONPATH (in your .bash_profile file), or add a .pth file, both for gdal and for openquake itself.

To get RabbitMQ set up, execute the following:

sudo rabbitmq-server &
sudo rabbitmqctl add_user celeryuser celery
sudo rabbitmqctl add_vhost celeryvhost
sudo rabbitmqctl set_permissions -p celeryvhost celeryuser ".*" ".*" ".*"

(Feel free to customize these settings and update celeryconfig.py)

Running Tests
-------------

To run the python tests use:

::
    celeryd &
    python runtests.py

To run the java tests use:

::

    ant


Running Demos
-------------

To run the command-line demo:

::

    ./demo.sh --debug



Tools / Services
----------------

* git
* git-cl (http://neugierig.org/software/git/?r=git-cl)

::
    
    git clone git://neugierig.org/git-cl.git
    ln -s /path/to/git-cl/git-cl /usr/bin/git-cl
    ln -s /path/to/git-cl/upload.py /usr/bin/upload.py

* GitHub (http://github.com/gem/openquake)
* Rietveld (http://gemreview.appspot.com) - requires a google account
* PivotalTracker (http://pivotaltracker.com)

Troubleshooting
---------------

SciPy can be a real pain to install on OS X. These steps should work if the
procedure mentioned above does not.

Make sure you have installed numpy >= 1.4, if you have installed GDAL you 
might have an older version of numpy that may be loaded by Python before your
new installation on numpy. To resolve this, change the python module loading 
order by editing /Python/2.6/site-packages/gdal.pth
from:
import sys; sys.path.insert(0,'/Library/Frameworks/GDAL.framework/Versions/1.7/
Python/site-packages')
to:
import sys; sys.path.append('/Library/Frameworks/GDAL.framework/Versions/1.7/
Python/site-packages')

::

    svn co http://svn.scipy.org/svn/numpy/trunk numpy 
    svn co http://svn.scipy.org/svn/scipy/trunk scipy
    
    cd numpy

    # edit gnu.py and find the word "ppc64" and remove it from the array
    vim numpy/distutils/fcompiler/gnu.py

    python setup.py build
    sudo python setup.py install
    
    cd ../scipy

    python setup.py build
    sudo python setup.py install
