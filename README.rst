=========
hazardlib
=========
hazardlib (the Openquake Hazard Library) is open-source software for performing
seismic hazard analysis.

What is hazardlib?
------------------
hazardlib includes modules for modeling seismic sources (point, area and fault),
earthquake ruptures, temporal (e.g. Poissonian) and magnitude occurrence
models (e.g. Gutenberg-Richter), magnitude/area scaling relationships,
ground motion and intensity prediction equations (i.e. GMPEs and IPEs).
Eventually it will offer a number of calculators for hazard curves,
stochastic event sets, ground motion fields and disaggregation histograms.

hazardlib aims at becoming an open and comprehensive tool for seismic hazard
analysis. The GEM Foundation (http://www.globalquakemodel.org/) supports
the development of the  library by adding the most recent methodologies
adopted by the seismological/seismic hazard communities. Comments,
suggestions and criticisms from the community are always very welcome.

Requirements
------------
hazardlib depends on numpy and scipy for fast numerical calculations and on
shapely for geometric primitives routines.

Development and support
-----------------------

hazardlib is being actively developed by GEM foundation as a part of
OpenQuake project (though it doesn’t mean hazardlib depends on OpenQuake).
The OpenQuake development infrastructure is used for developing hazardlib:
the public repository is available on github:
http://github.com/gem/oq-hazardlib. A mailing list is available as well:
http://groups.google.com/group/openquake-users. You can also ask for
support on IRC channel #openquake on freenode.

Installation
------------
To install type as usual::

 python setup.py install

Running Tests (in a development environment)
--------------------------------------------

1. Install dependencies::

    # Ubuntu 14.04 LTS:
    apt-get install python-numpy python-scipy python-shapely
    # Other platforms, or if you are using a virtualenv:
    pip install numpy scipy shapely

2. Install test dependencies::

    # Ubuntu 14.04 LTS:
    apt-get install python-nose python-coverage python-mock
    # Other platforms, or if you are using a virtualenv:
    pip install nose coverage mock

3. Run tests::

    nosetests --with-doctest --with-coverage --cover-package=openquake.hazardlib

License
-------
hazardlib is licensed under terms of GNU Affero General Public License 3.0, see
LICENSE for more details.
