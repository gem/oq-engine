.. _installing-the-openquake-engine:

Installing the OpenQuake engine
===============================

The OpenQuake Engine runs on Linux, macOS and Windows; on laptops,
workstations, standalone servers and multi-node clusters. Due to its
large range of use cases it can be installed in several different
ways. The minimum hardware requirements are

- 16 GB of RAM
- 4 GB of free disk space

To run any serious calculation (i.e. a model in GEM mosaic) you need
at least 2 GB of RAM per thread for hazard calculations and even more
memory for risk calculations. For instance, on a recent i9 processor
with 32 threads you would need at least 64 GB of RAM.

If you want to use the latest feature of the engine you should install
the latest available version, noting the there is a new version every 3-4
months. If you want stability, you should install the Long Term
Support version that changes only every two years.

If you have a Windows machine and you are not interested
in developing with the engine, the recommended approach is to use
the Windows installer: :ref:`windows`.

If you have a Mac or Linux machine and you are not interested
in developing with the engine, the recommended approach is to use
the :doc:`universal installer <universal>` in ``user`` mode.

Users wanting to develop with the engine (for instance to implement
new GMPES) must clone the engine reepository and
use the :doc:`universal installer <universal>` in ``devel`` mode.

Changing the version
--------------------

To change the version of the engine, make sure to uninstall the current version, before installing a new version.
See the corresponding chapters following the link below.

- :ref:`Uninstalling the engine <universal>`
- :ref:`Installing a specific engine version <universal>`

Other installation methods
--------------------------

**Using ``pip``**

The OpenQuake Engine is also available on `PyPI <https://pypi.python.org/pypi/openquake.engine>`_ and can be installed
in any Python 3 environment via ``pip``::

	```
	$ pip install -r https://github.com/gem/oq-engine/raw/engine-3.24/requirements-py311-linux64.txt openquake.engine
	```

This works for Linux and Python 3.11. You can trivially adapt the command to other operating systems. For instance for Windows it would be::

	```
	$ pip install -r https://github.com/gem/oq-engine/raw/engine-3.24/requirements-py311-win64.txt openquake.engine
	```

and for Mac, it would be::

	```
	$ pip install -r https://github.com/gem/oq-engine/raw/engine-3.24/requirements-py311-macos.txt openquake.engine
	```

Cloud
-----

A set of :doc:`Docker containers <docker>` for installing the engine in the cloud.

Getting help
------------

If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list:
https://groups.google.com/g/openquake-users


.. toctree::
   :maxdepth: 1
   :caption: Installation:

   universal
   windows
   macos
   development
   cluster
   server
   slurm
   tools
   docker
