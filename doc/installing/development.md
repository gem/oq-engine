# Installing the OpenQuake Engine for development

To develop with the OpenQuake Engine and Hazardlib an installation from sources must be performed.
The official supported distributions to develop the OpenQuake Engine and its libraries are
- Ubuntu 14.04 LTS (Trusty) 
- Ubuntu 16.04 LTS (Xenial)
- RedHat Enterprise Linux 7 
- CentOS 7
- Scientific Linux 7

This guide may work also on other Linux releases/distributions and with some adaptations on macOS.

## Prerequisites

Some prerequisites are needed to build the development environment

### Ubuntu

```bash
sudo apt-get install build-essential git libhdf5-dev libgeos-dev python-virtualenv python-pip
```

### RedHat

```bash
sudo yum groupinstall "Development tools"
sudo yum install git hdf5-devel geos-devel python-virtualenv python-pip
```

## Build the development environment

A development environment will be built using a python *virtualenv*

```bash
virtualenv openquake
source openquake/bin/activate
```

## Install the OpenQuake dependencies

Inside the *virtualenv* (the propmt shows something like `(openquake)user@myhost:~$`) upgrade `pip` first

```bash
pip install -U pip
```

download the OpenQuake source code

```bash
mkdir src && cd src
git clone https://github.com/gem/oq-engine.git
git clone https://github.com/gem/oq-hazardlib.git
```

install the OpenQuake requirements

```bash
pip install -r oq-engine/requirements-dev.txt
```

install OpenQuake itself

```bash
pip install -e oq-hazardlib/
pip install -e oq-engine/
```

Now it is possible to run the OpenQuake Engine with `oq engine`. Any change made to the `oq-engine` or `oq-hazardlib` code will be reflected in the environment.

Continue on [How to run the OpenQuake Engine](../running/unix.md)

## Loading and unloading the development environment

To exit from the OpenQuake development enviroment type `deactivate`. Before using again the OpenQuake software the environment must be loaded back running `source openquake/bin/activate`(assuming that it has been installed under 'openquake').


## Uninstall the OpenQuake Engine

To uninstall the OpenQuake development make sure that its enviroment is not loaded typing `deactivate` and the remove teh folder where it has been installed: `rm -Rf openquake`.

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the developer mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-dev
  * Contact us on IRC: irc.freenode.net, channel #openquake
