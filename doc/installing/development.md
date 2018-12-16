# Installing the OpenQuake Engine for development using Python 3.6

To develop with the OpenQuake Engine and Hazardlib an installation from sources must be performed.

The official supported distributions to develop the OpenQuake Engine and its libraries are

### Linux

- Ubuntu 18.04 LTS (Bionic)
- RedHat Enterprise Linux 7 / CentOS 7 / Scientific Linux 7
- Fedora 27/28/29

This guide may work also on other Linux releases/distributions.

### macOS

- macOS 10.11 (El Capitan)
- macOS 10.12 (Sierra)
- macOS 10.13 (High Sierra)
- macOS 10.14 (Mojave)

## Prerequisites

Knowledge of [Python](https://www.python.org/) (and its virtual environments), [git](https://git-scm.com/) and [software development](https://xkcd.com/844/) are required.

Some software prerequisites are needed to build the development environment. Python 3.6 or greater is required.

### Ubuntu

```bash
sudo apt install git python3.6 python3.6-venv python3-pip
```

### RedHat and clones

On RedHat and its clones (CentOS/SL) Python 3.6 isn't available in the standard repositories, but it can be installed via [RedHat Software Collections](https://access.redhat.com/documentation/en-US/Red_Hat_Developer_Toolset/1/html-single/Software_Collections_Guide/).

```bash
## RedHat
sudo yum install git scl-utils scl-utils-build

## CentOS/SL
sudo yum install git centos-release-scl

sudo yum install rh-python36
scl enable rh-python36 bash
```

### Fedora

```bash
sudo dnf install python36
```

### macOS
*This procedure refers to the official Python distribution from [python.org](https://python.org). If you are using a different python (from brew, macports, conda) you may need to adapt the following commands.*

#### Xcode

You must install the Command Line Tools Package for Xcode first. You can install the Command Line Tools package without having to install the entire Xcode software by running:

```bash
xcode-select --install
```

If Xcode is already installed on your machine, then there is no need to install the command-line tools.

#### Python

You need to download Python from [python.org](https://python.org): https://www.python.org/ftp/python/3.6.6/python-3.6.6-macosx10.9.pkg

#### Encoding

Make sure that the encoding set in the terminal is `en_US.UTF-8`. To force it, you should put the following lines in your `~/.profile`:

```bash
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

## Build the development environment

Let's create a working dir called openquake first

```bash
mkdir $HOME/openquake && cd $HOME/openquake
```

then build a development environment using python *virtualenv*

```bash
python3.6 -m venv oqenv
source oqenv/bin/activate
```

## Install the code

Inside the *virtualenv* (the prompt shows something like `(oqenv)user@myhost:~$`) upgrade `pip` and `setuptools` first

```bash
pip install -U pip setuptools
```

### Download the OpenQuake source code

```bash
mkdir src && cd src
git clone https://github.com/gem/oq-engine.git
```

### Install OpenQuake

It's strongly recommended to install Python dependencies using our Python wheels distribution: all the external dependencies (`geos`, `proj4`, `hdf5`, `blas`, and many other) are already included as pre-compiled binaries and are tested before every release.

```bash
# For Linux
pip install -r oq-engine/requirements-py36-linux64.txt
```

```bash
# For macOS
pip install -r oq-engine/requirements-py36-macos.txt
```

```bash
pip install -e oq-engine/[dev]
```
The `dev` extra feature will install some extra dependencies that will help in debugging the code. To install other extra features see [1](#note1). If your system does not support the provided binary dependencies you'll need to manually install them, using tools provided by your python distribution [2](#note2).

Now it is possible to run the OpenQuake Engine with `oq engine`. Any change made to the `oq-engine` code will be reflected in the environment.

Continue on [How to run the OpenQuake Engine](../running/unix.md)

### Sync the source code with remote

You can pull all the latest changes to the source code running

```bash
cd oq-engine
git pull
cd ..
```

## Loading and unloading the development environment

To exit from the OpenQuake development environment type `deactivate`. Before using again the OpenQuake software the environment must be reloaded running `source oqenv/bin/activate`(assuming that it has been installed under 'oqenv'). For more information about *virtualenv*, see http://docs.python-guide.org/en/latest/dev/virtualenvs/.

To load the virtual environment automatically at every login, add the following line at the bottom of your `~/.bashrc` (Linux) or `~/.profile` (macOS):

```bash
source $HOME/openquake/oqenv/bin/activate
```

You can also add a short-hand command to enable it:

```bash
alias oqenv="source $HOME/openquake/oqenv/bin/activate"
```

Put it again at the bottom of `~/.bashrc` or `~/.profile`; close and re-open the terminal. You can now load your environment just typing `oqenv`.

### Multiple installations

If any other installation of the Engine exists on the same machine, like a system-wide installation made with packages, you must change the DbServer port from the default one (1908) to any other unused port. Using a DbServer started from a different codebase (which may be out-of-sync) could lead to unexpected behaviours and errors. To change the DbServer port `oq-engine/openquake/engine/openquake.cfg` must be updated:

```
[dbserver]          |  [dbserver]
## cut ##           |  ## cut ##
port = 1908         >  port = 1985
authkey = changeme  |  authkey = changeme
## cut ##           |  ## cut ##
```

or the `OQ_DBSERVER_PORT` enviroment variable must be set:

```bash
export OQ_DBSERVER_PORT=1985
```

## Running the tests

To run the OpenQuake Engine tests see the **[testing](../testing.md)** page.

## Uninstall the OpenQuake Engine

To uninstall the OpenQuake development make sure that its environment is not loaded, typing `deactivate`, and then remove the folder where it has been installed: `rm -Rf openquake`.

***

### Notes ###

*<a name="note1">[1]</a>: extra features, like celery and pam support can be installed running:*

```bash
# oq-engine with celery support
pip install -e oq-engine/[dev,celery]
# oq-engine with pam support
pip install -e oq-engine/[dev,pam]
# oq-engine with support for both
pip install -e oq-engine/[dev,celery,pam]
```

*<a name="note2">[2]</a>: unsupported systems:*

If your system does not support the provided binary dependencies (python wheels)

```bash
pip install -e oq-engine/[dev]
```

will try to download the required dependencies from [pypi](http://pypi.python.org/). This may require some extra work to get all the external C dependencies resolved.
If you are using a non-standard python distribution (like _macports_ or _anaconda_) you should use tools provided by such distribution to get the required dependencies.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
