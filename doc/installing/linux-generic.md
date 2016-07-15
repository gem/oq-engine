# Installing the OpenQuake Engine on a generic Linux distribution

The OpenQuake Engine is also available in the form of **self-installable binary distribution**.

### Differences with packages for Ubuntu and RedHat

This distribution has some differences with the packages we provide for Ubuntu and RedHat:

- includes its own distribution of the dependencies needed by the OpenQuake Engine
    - OpenSSL 1.0
    - HDF5 1.8
    - Python 2.7
    - Python dependencies (pip, numpy, scipy, h5py, django and few more)
- can be installed without `root` permission (i.e. in the user home)
- multiple versions can be installed alongside
- currently does not support Celery (support for Celery is planned)
- the OpenQuake Engine and its dependencies will not be available to system's python

## Requirements

Requirements are:

- GNU/Linux with bash
- libc version at least 2.15
- 4 GB of RAM (8 GB recommended)
- 1.2 GB of free disk space

## Install packages from the OpenQuake repository

Download the installer from http://www.globalquakemodel.org/pkgs/linux/oq-engine/openquake-setup-linux64-2.0.1-1.run using any browser

From a terminal run

```bash
cd Downloads
chmod +x openquake-setup-linux64-2.0.1-1.run
./openquake-setup-linux64-2.0.1-1.run
```
then follow the wizard on screen. By default the code is installed in `~/openquake`


## Run the OpenQuake Engine

Before running the OpenQuake Engine its environment must be loaded

```bash
source /installation/path/of/openquake/env.sh
```

Continue on [How to run the OpenQuake Engine](../running/unix.md)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
