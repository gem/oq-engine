# Installing the OpenQuake Hazardlib for development

To develop with the OpenQuake Hazardlib an installation from sources must be performed.

*The source installation will conflict with the package installation, so you
must remove the openquake package if it was already installed.*

The official supported distributions to develop the OpenQuake libraries are
- Ubuntu 14.04 LTS (Trusty) 
- Ubuntu 16.04 LTS (Xenial)
- RedHat Enterprise Linux 7 
- CentOS 7
- Scientific Linux 7

This guide may work also on other Linux releases/distributions.

Guidelines are provided for *macOS* too.

## Prerequisites

Knowledge of [Python](https://www.python.org/) (and its virtual environments), [git](https://git-scm.com/) and [software development](https://xkcd.com/844/) are required.

Some software prerequisites are needed to build the development environment. Python 2.7 is used in this guide, but Python 3.5 can be also used with few adaptations to the following commands.

### Ubuntu

```bash
sudo apt-get install build-essential git libhdf5-dev libgeos-dev python-virtualenv python-pip
```

### RedHat

```bash
sudo yum groupinstall "Development tools"
sudo yum install git hdf5-devel geos-devel python-virtualenv python-pip
```

### macOS
*This procedure refers to the stock Python shipped by Apple on macOS. If you are using a different python (from brew, macports, conda) you may need to adapt the following commands.*

You must install [Xcode](https://itunes.apple.com/app/xcode/id497799835?mt=12) first.
`pip` needs to be manually installed too:

```bash
curl https://bootstrap.pypa.io/get-pip.py | sudo python
```

and finally *virtualenv*

```bash
sudo pip install virtualenv
```

## Build the development environment

A development environment will be built using a python *virtualenv*

```bash
virtualenv openquake
source openquake/bin/activate
```

## Install the code

Inside the *virtualenv* (the prompt shows something like `(openquake)user@myhost:~$`) upgrade `pip` first

```bash
pip install -U pip
```

### Download the OpenQuake Hazardlib source code

```bash
mkdir src && cd src
git clone https://github.com/gem/oq-hazardlib.git
```

### Install Hazardlib <sup>[1](#note1)</sup> <sup>[2](#note2)</sup>

```bash
pip install -e oq-hazardlib/
```

### Sync the source code with remote

You can pull all the latest changes to the source code running

```bash
cd oq-hazardlib
git pull
cd ..
```

## Loading and unloading the development environment

To exit from the OpenQuake development environment type `deactivate`. Before using again the OpenQuake software the environment must be loaded back running `source openquake/bin/activate`(assuming that it has been installed under 'openquake'). For more information about *virtualenv* and its you see http://docs.python-guide.org/en/latest/dev/virtualenvs/

## Running the tests

To run the OpenQuake Hazardlib tests see the **[testing](../testing.md)** page.

## Uninstall the OpenQuake Hazardlib

To uninstall the OpenQuake development make sure that its environment is not loaded typing `deactivate` and the remove the folder where it has been installed: `rm -Rf openquake`.

***

### Notes ###

*<a name="note1">[1]</a>: if you want to use binary dependencies (python wheels: they do not require any compiler, development library...) before installing `oq-engine` and `oq-hazardlib` run:*

```bash
# For Linux
pip install -r oq-hazardlib/requirements-py27-linux64.txt
```

```bash
# For macOS
pip install -r oq-hazardlib/requirements-py27-macos.txt
```

*<a name="note2">[2]</a>: extra features, like rtree support can be installed running:*

```bash
# oq-hazardlib with Rtree support
pip install -e oq-hazardlib/[Rtree]
```
***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
