OpenGEM System
==============

Dependencies
------------

For the most part the Python packages in here can be installed using `pip`
(python-pip on ubuntu) or your favorite package manager.

On OS X a good way to intall the pieces that are not Python (if you don't
already use MacPorts or Fink) is called homebrew: http://mxcl.github.com/homebrew/

* eventlet
* lxml
* PyYAML
* python-gflags
* SciPy
  * You will need gfortran, for os x that is at: http://r.research.att.com/gfortran-4.2.3.dmg 
  * After that `pip install scipy` should work.
  * If it doesn't and there is an error about ppc64... well it is more complex,
    see Troubleshooting
* Shapely
  * requires geos (c library, also called libgeos)
* Sphinx (for building documentation only)


Running Tests
-------------

To run the python tests use:

::

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

* GitHub (http://github.com/gem/opengem)
* Rietveld (http://gemreview.appspot.com)
* PivotalTracker (http://pivotaltracker.com)

Troubleshooting
---------------

SciPy can be a real pain to install on OS X. These steps should work if the
procedure mentioned above does not.

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

