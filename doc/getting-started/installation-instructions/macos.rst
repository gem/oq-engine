Installing the OpenQuake Engine on MacOS
========================================

Requirements
------------

Requirements are:

-  macOS Sonoma 14.5 or macOS Ventura 13.6.7
-  at least 16 GB of RAM
-  4 GB of free disk space
-  Python 3.11

We recommend using a Linux server for large calculations such as
national or regional-scale models.

Installation Procedure
----------------------

Before to use the universal installer you need to install Python3.

Downloading the Python version from the official Python website
(python.org) is the recommended) method for installing Python on a Mac.

Download the installer from
https://www.python.org/ftp/python/3.11.8/python-3.11.8-macos11.pkg

The installation process is described in the following screenshots :

Localize the downloaded file on your computer (probably Downloads)

.. image:: _images/macos/download_python.png


and double-click on the installer to start the installation.

.. image:: _images/macos/run_installer.png


IMPORTANT: Please note that the package includes its own private copy of
OpenSSL 3.0.

.. image:: _images/macos/openssl.png


IMPORTANT Remember to double-click on Install Certificates to install it
at the end of installation


.. image:: _images/macos/install_certifi_1.png


.. image:: _images/macos/install_certifi_2.png


.. image:: _images/macos/install_certifi_3.png

Close all windows after the Process is completed.

Once Python 3.11 is installed, please run the universal installer to
install OpenQuake Engine 
 :ref:`<universal>`.


Getting help
------------

If you need help or have questions/comments/feedback for us, please
subscribe to the `OpenQuake users mailing
list <https://groups.google.com/g/openquake-users>`__
