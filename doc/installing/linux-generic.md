# Installing the OpenQuake Engine on a generic Linux distribution

The OpenQuake Engine is also available in the form of **self-installable binary distribution**.
This way of installing OpenQuake is strongly suggested for old versions of Linux which
do not ship with Python 3.6 (like RHEL/CentOS/SL 6), or for users that do not have
administrator privileges (they cannot run `sudo` or `su`).

### Differences with packages for Ubuntu and RedHat

This distribution has some differences with the packages we provide for Ubuntu and RedHat:

- includes its own distribution of the dependencies needed by the OpenQuake Engine
    - OpenSSL 1.0
    - Python 3.6
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

Download the installer from https://downloads.openquake.org/pkgs/linux/oq-engine/openquake-setup-linux64-3.2.0-1.run using any browser

From a terminal run

```bash
cd Downloads
chmod +x openquake-setup-linux64-3.2.0-1.run
./openquake-setup-linux64-3.2.0-1.run
```
then follow the wizard on screen. By default the code is installed in `~/openquake`.

```bash
Verifying archive integrity... All good.
Uncompressing installer for the OpenQuake Engine  100%
Type the path where you want to install OpenQuake, followed by [ENTER]. Otherwise leave blank, it will be installed in /home/auser:
Copying the files in /home/auser/openquake. Please wait.
Finalizing the installation. Please wait.
Do you want to install the OpenQuake Tools (IPT, TaxtWeb, Taxonomy Glossary)? [y/n]: y
Do you want to make the 'oq' command available by default? [y/n]: y
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

If _make the 'oq' command available by default_ as been set to 'Y' (default) during the installation
the 'oq' command will be available by default after the terminal has been restarted.

To manually load the OpenQuake Engine environment, or if you answered 'no' to the question during installation, you must run

```bash
# default is ~/openquake
source ~/openquake/env.sh
```

before the OpenQuake Engine can be properly used.

To run the OpenQuake via command line use

```bash
oq engine --run </path/to/job.ini>
```

to start the [WebUI](../running/server.md) use instead

```bash
oq webui start
```
The WebUI will be started and a new browser window will be opened.

More information are available on [How to run the OpenQuake Engine](../running/unix.md) and [The OpenQuake Engine server and WebUI](../running/server.md).

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
