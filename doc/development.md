# Installing the OpenQuake Hazardlib for development

To develop with the OpenQuake Hazardlib an installation from sources must be performed.
The official supported distributions to develop the OpenQuake libraries are
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

Inside the *virtualenv* (the prompt shows something like `(openquake)user@myhost:~$`) upgrade `pip` first

```bash
pip install -U pip
```

download the OpenQuake Hazardlib source code

```bash
mkdir src && cd src
git clone https://github.com/gem/oq-hazardlib.git
```

install the OpenQuake requirements

```bash
pip install -r oq-hazardlib/requirements-dev.txt
```

install OpenQuake itself

```bash
pip install -e oq-hazardlib/
```

## Loading and unloading the development environment

To exit from the OpenQuake development environment type `deactivate`. Before using again the OpenQuake software the environment must be loaded back running `source openquake/bin/activate`(assuming that it has been installed under 'openquake'). For more information about *virtualenv* and its you see http://docs.python-guide.org/en/latest/dev/virtualenvs/

## Running the tests

To run the OpenQuake Hazardlib tests see the **[testing](../testing.md)** page.

## Uninstall the OpenQuake Hazardlib

To uninstall the OpenQuake development make sure that its environment is not loaded typing `deactivate` and the remove the folder where it has been installed: `rm -Rf openquake`.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
