# Installing the OpenQuake Engine on a generic Linux distribution

The OpenQuake Engine is also available in the form of **self-installable binary distribution**.

### Differences with packages for Ubuntu and RedHat

This distribution has some differences with the packages we provide for Ubuntu and RedHat:

- includes its own distribution of the dependencies needed by the OpenQuake Engine
    - OpenSSL 1.0
    - HDF5 1.8
    - Python 2.7
    - Python dependencies (pip, numpy, scipy, h5py, django, shapely, rtree and few more)
- can be installed without `root` permission (i.e. in the user home)
- multiple versions can be installed alongside
- currently does not support Celery (support for Celery is planned) and clusters setup
- the OpenQuake Engine and its dependencies will not be available to system's python

## Requirements

Requirements are:

- GNU/Linux with bash
- libc version at least 2.14 (i.e. a distro not older than CentOS 6)
- 4 GB of RAM (8 GB recommended)
- 1.2 GB of free disk space

## Install packages from the OpenQuake website

Download the installer from http://www.globalquakemodel.org/pkgs/linux/oq-engine/openquake-setup-linux64-2.1.0-1.run using any browser

From a terminal run

```bash
cd Downloads
chmod +x openquake-setup-linux64-2.1.0-1.run
./openquake-setup-linux64-2.1.0-1.run
```
then follow the wizard on screen. By default the code is installed in `~/openquake`.

```bash
Verifying archive integrity... All good.
Uncompressing installer for the OpenQuake Engine  100%
Type the path where you want to install OpenQuake, followed by [ENTER]. Otherwise leave blank, it will be installed in /home/auser:
Copying the files in /home/auser/openquake. Please wait.
Finalizing the installation. Please wait.
Installation completed. To enable it run 'source /home/auser/openquake/env.sh'
```

The demo files are located in `~/openquake/share/openquake/engine/demos`.


### Upgrade from a previous installation

To upgrade from a previous installation you need to manually remove it first

```bash
# default is ~/openquake
rm -Rf ~/openquake
```


## Run the OpenQuake Engine

Before running the OpenQuake Engine its environment must be loaded

```bash
# default is ~/openquake
source ~/openquake/env.sh
```

Continue on [How to run the OpenQuake Engine](../running/unix.md)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
