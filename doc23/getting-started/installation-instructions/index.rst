.. _installing-the-openquake-engine:

Installing the OpenQuake engine
===============================

The OpenQuake Engine runs on Linux, macOS and Windows; on laptops, workstations, standalone servers and multi-node 
clusters. Due to its large range of use cases it can be installed in several different ways.

	Warning: If you already have an engine installation, before installing the new version you must uninstall the old one.

Instructive YouTube video for the installation procedure:

.. youtube:: J46boursIRc
   :align: center

.. _hardware-requirements:

Hardware requirements
---------------------

The minimum required to install the engine and run the demos is

- 8 GB of RAM (16 GB on macOS Ventura)
- 4 GB of free disk space

To run any serious calculation (i.e. a model in GEM mosaic) you need at least 2 GB of RAM per thread for hazard 
calculations and even more memory for risk calculations. For instance, on a recent i9 processor with 32 threads you 
would need at least 64 GB of RAM.

Check more advanced `hardware suggestions here <https://github.com/gem/oq-engine/blob/master/doc/hardware-suggestions.md>`_.

Installing the Long Term Support (LTS) version
----------------------------------------------

**On Windows**

Download OpenQuake Engine for Windows: https://downloads.openquake.org/pkgs/windows/oq-engine/OpenQuake_Engine_3.16.6-1.exe . 
Then follow the wizard on screen.

	Warning: Administrator level access may be required.

**On MacOS or Linux**

See instructions for the :ref:`universal installer <universal_installer>` script, 
and consider the specific LTS to be installed.

Installing the latest version
-----------------------------

See instructions for the :ref:`universal installer <universal_installer>` script. 
This script works for Linux, macOS and Windows, on laptops, workstations, standalone servers and multi-node clusters.

Changing the OpenQuake Engine version
-------------------------------------

To change the version of the engine, make sure to uninstall the current version, before installing a new version.

- :ref:`Uninstalling the engine <uninstalling_the_engine>`
- `Installing a specific engine version <https://github.com/gem/oq-engine/blob/master/doc/installing/universal.md##installing-a-specific-engine-version>`_

Other installation methods
--------------------------

**Using ``pip``**

The OpenQuake Engine is also available on `PyPI <https://pypi.python.org/pypi/openquake.engine>`_ and can be installed 
in any Python 3 environment via ``pip``::

	```
	$ pip install -r https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py38-linux64.txt openquake.engine
	```

This works for Linux and Python 3.8. You can trivially adapt the command to Python 3.9 and 3.10, and to other operating 
systems. For instance for Windows and Python 3.8, it would be::

	```
	$ pip install -r https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py38-win64.txt openquake.engine
	```

and for Mac and Python 3.8, it would be::

	```
	$ pip install -r https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py38-macos.txt openquake.engine
	```

Cloud
-----

A set of :ref:`Docker containers <docker>` for installing the engine in the cloud.

Getting help
------------

If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: 
https://groups.google.com/g/openquake-users


.. toctree::
   :maxdepth: 1

   universal
   windows
   ubuntu
   ubuntu-nightly
   development
   cluster
   rhel
   server
   tools
   docker