# Universal installation script

Since version 3.11 of the OpenQuake-engine, there is a universal installation script that works on any platform, provided you have a suitable Python installed.
The script allows the user to select between different kinds of installations:

1. [`user` installation](#user-installation) (Windows, macOS, and Linux)
2. [`devel` installation](#devel-installation) (Windows, macOS, and Linux)
3. [`server` installation](#server-installation) (only available for Linux)
4. [`devel_server` installation](#devel_server-installation) (only available for Linux)


**Python installation**

The OpenQuake engines supports Python 3.8, Python 3.9 or Python 3.10 (later versions are not supported yet).

You can install Python via [python.org](https://www.python.org/downloads/). 

  > **Warning**:
  > _Conda is not supported. Some users have been able to run the OpenQuake-engine with Conda, but GEM is not using and not testing conda; you are on your own._

> **Note:** This script will install the OpenQuake engine in its own _virtual environment_. Users who need to use any additional Python packages (eg. Jupyter, Spyder) along with the OpenQuake-engine should install those packages within this virtual environment. Users with no knowledge of virtual environments are referred to this page of the Python tutorial: https://docs.python.org/3/tutorial/venv.html


## `user` installation

If you do not need to modify the engine codebase or develop new features with the engine, but intend to use it as an application, you should perform a `user` installation (on Windows / macOS) or a `server` installation (on Linux). The `user` installation is also the recommended option for Linux, in the case where you do not have root permissions on the machine. 

By default, the script will install the latest stable release of the engine. It is possible to [specify another version](#installing-a-specific-engine-version).

### on Windows

  1. Make sure to have Python installed.
  2. Download the installation script from the terminal:
  ```
  C:\>curl.exe -LO https://raw.githubusercontent.com/gem/oq-engine/master/install.py
  C:\>python.exe install.py user
  ```
  3. This installation method will create a Python virtual environment in `$HOME/openquake` and will install the engine on it.
  > **Warning**:
  > _Make sure you have no folder called `openquake` in your home directory that can cause conflicts._

  4. Activate the OpenQuake virtual environment with
  ```
  C:\>%USERPROFILE%\openquake\Scripts\activate.bat
  ```

  5. [Running the OpenQuake Engine](https://github.com/gem/oq-engine#running-the-openquake-engine)

  6. Calculation data will be stored in `$HOME/oqdata`.


### on macOS:

  1. Make sure to have Python installed.<br />
  > - Make sure to run the script located under /Applications/Python 3.X/Install Certificates.command, after Python has been installed, to update the SSL certificates bundle see [see FAQ](../faq.md#certificate-verification-on-macOS).<br />
  > - Apple ships its own version of Python. However, we strongly recommend installing the official Python distribution. Alternatively, use Python from one of the package managers (Homebrew, MacPorts, Fink).<br />
  > - New Macs with the _M1 CPU_ are supported only if you are on macOS 12.x and for **python3.9**.

  2. Download the installation script:
  ```
  $ curl -O https://raw.githubusercontent.com/gem/oq-engine/master/install.py
  $ python3.9 install.py user
  ```
  > _*Note 1*: Users can decided the preferred Python version (e.g., `$python3.10 install.py user`)_<br />
  > _*Note 2*: Users with the M1 CPU must use Python 3.9_

  3. This installation method will create a Python virtual environment in `$HOME/openquake` and will install the engine on it.
  > **Warning**:
  > _Make sure you have no folder called `openquake` in your home directory that can cause conflicts._

  4. Activate the OpenQuake virtual environment with
  ```
  $ source $HOME/openquake/bin/activate
  ```

  5. [Running the OpenQuake Engine](https://github.com/gem/oq-engine#running-the-openquake-engine)

  6. Calculation data will be stored in `$HOME/oqdata`.


### on Linux:
  1. Make sure to have Python installed.<br />
  > _On some Linux distributions (i.e. Ubuntu) you may need to install the package `python3-venv` before running the installer._

  2. Download the installation script:
  ```
  $ curl -O https://raw.githubusercontent.com/gem/oq-engine/master/install.py
  $ /usr/bin/python3 install.py user
  ```

  3. This installation method will create a Python virtual environment in `$HOME/openquake` and will install the engine on it.
  > **Warning**:
  > _Make sure you have no folder called `openquake` in your home directory that can cause conflicts._

  4. Activate the OpenQuake virtual environment with
  ```
  $ source $HOME/openquake/bin/activate
  ```

  5. [Running the OpenQuake Engine](https://github.com/gem/oq-engine#running-the-openquake-engine)

  6. Calculation data will be stored in `$HOME/oqdata`.


## `devel` installation

Users who intend to modify the engine codebase or add new features for the engine should use the `devel` (developer) installation:

You will need to have `git` installed on your PC to clone the engine codebase and periodically keep it up to date. If you don’t have `git` installed already, you can install it from https://git-scm.com/downloads.
You can check if you already have `git` installed by trying to run `git` from the command prompt:
  - on Windows: `C:\> git --version`
  - on macOS: `$ git --version`


### on Windows:

  1. Clone the OpenQuake Engine repository. <br />
  In a new command prompt window or in Git Bash.
  ```
  C:\> git clone https://github.com/gem/oq-engine.git
  C:\> cd oq-engine 
  C:\> python.exe install.py devel
  ```
  2. This installation method will create a Python virtual environment in `$HOME/openquake` and will install the engine on it.
  > **Warning**:
  > _Make sure you have no folder called `openquake` in your home directory that can cause conflicts._

  3. Activate the OpenQuake virtual environment with
  ```
  C:\>%USERPROFILE%\openquake\Scripts\activate.bat
  ```

  4. [Running the OpenQuake Engine](https://github.com/gem/oq-engine#running-the-openquake-engine)

  5. Calculation data will be stored in `$HOME/oqdata`.


### on macOS:

> _Before installing the engine, make sure to run the script located under /Applications/Python 3.X/Install Certificates.command,to update the SSL certificates bundle see [see FAQ](../faq.md#certificate-verification-on-macOS)._

  1. Clone the OpenQuake Engine repository. <br />
  ```
  $ git clone https://github.com/gem/oq-engine.git
  $ cd oq-engine
  $ python3.9 install.py devel
  ```
    > _*Note 1*: Users can decided the preferred Python version (e.g., `$python3.10 install.py user`)_<br />
    > _*Note 2*: Users with the M1 CPU must use Python 3.9_

  2. This installation method will create a Python virtual environment in `$HOME/openquake` and will install the engine on it.
  > **Warning**:
  > _Make sure you have no folder called `openquake` in your home directory that can cause conflicts._

  3. Activate the OpenQuake virtual environment with
  ```
  $ source $HOME/openquake/bin/activate
  ```

  4. [Running the OpenQuake Engine](https://github.com/gem/oq-engine#running-the-openquake-engine)

  5. Calculation data will be stored in `$HOME/oqdata`.


### on Linux:

  1. Clone the OpenQuake Engine repository. <br />
  ```
  $ git clone https://github.com/gem/oq-engine.git
  $ cd oq-engine && /usr/bin/python3 install.py devel
  ```

  2. This installation method will create a Python virtual environment in `$HOME/openquake` and will install the engine on it.
  > **Warning**:
  > _Make sure you have no folder called `openquake` in your home directory that can cause conflicts._

  3. Activate the OpenQuake virtual environment with
  ```
  $ source $HOME/openquake/bin/activate
  ```

  4. [Running the OpenQuake Engine](https://github.com/gem/oq-engine#running-the-openquake-engine)

  5. Calculation data will be stored in `$HOME/oqdata`.


## `server` installation

If you are on a Linux machine _and you have root permissions_, the
recommended installation method is `server`. In this case, the engine
will work with multiple users and two system V services will be
automatically installed and started: `openquake-dbserver` and
`openquake-webui`.

```
$ curl -O https://raw.githubusercontent.com/gem/oq-engine/master/install.py
$ sudo -H /usr/bin/python3 install.py server
```

The installation script will automatically create a user called
`openquake` and will install the engine in the directory
`/opt/openquake`.  Calculation data will be stored in
`/var/lib/openquake/oqdata`.

> **Warning**:
> If you already have an engine installation made with debian or rpm
packages, before installing the new version you must uninstall the old
version, make sure that the dbserver and webui services are actually
stopped and then also remove the directory `/opt/openquake` and the
configuration file `/etc/openquake/openquake.cfg`. If you want to
preserve some configuration (like the [zworkers] section which is needed
on a cluster) you should keep a copy of `/etc/openquake/openquake.cfg`
and move it inside `/opt/openquake` once the new installation is finished.


## `devel_server` installation

This method adds to `server` installation the possibility to run the engine from a git repository.
If you are on a Linux machine _and_ you have root permissions

```
$ git clone https://github.com/gem/oq-engine.git
$ cd oq-engine && sudo -H /usr/bin/python3 install.py devel_server
```

## Cluster installation

It is possible to install the engine on a Linux cluster, but it requires additional steps. You should see the page about [clusters](cluster.md).


## Cloud installation

A set of [Docker containers](docker.md) is available for installing the engine in the cloud.


## Installing a specific engine version

By default, in `user` and `server` mode the script will install the latest stable release of the engine.
If for some reason you want to use an older version you can specify the version number with the ``--version`` option:
```
$ python3 install.py user --version=3.10
```

## Uninstalling the engine

To uninstall the engine, use the --remove flag:

**on Windows:**
  Depending on the type of installation, please choose one of the following commands:
  ```
  C:\>cd %USERPROFILE%
  C:\>python install.py devel --remove
  C:\>python install.py user --remove
  ```

**on macOS and Linux:**
  Depending on the type of installation, please choose one of the following commands:
  ```
  $ python3 install.py user --remove
  $ python3 install.py devel --remove
  $ sudo -H python3 install.py server --remove
  ```

The calculation data (in the `$HOME/oqdata` directory) **WILL NOT** be removed.
You will have to remove the data manually, if desired.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/u/0/g/openquake-users.
