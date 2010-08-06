OpenGEM System
==============

Dependencies
------------

For the most part the Python packages in here can be installed using `pip`
(python-pip on ubuntu) or your favorite package manager.

On OS X a good way to intall the pieces that are not Python (if you don't
already use MacPorts or Fink) is called homebrew: http://mxcl.github.com/homebrew/

* lxml
* SciPy
  * You will need gfortran, for os x that is at: http://r.research.att.com/gfortran-4.2.3.dmg 
  * After that `pip install scipy` should work.
* PyYAML
* python-gflags
* Eventlet
* Shapely
  * requires geos (c library, also called libgeos)
* Sphinx (for building documentation only)


Running Tests
-------------

To run the python tests use:

::

    python runtests.py



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


