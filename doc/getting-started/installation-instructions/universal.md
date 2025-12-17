(universal)=

# Universal installer

Since version 3.11 of the OpenQuake-engine, there is a universal installation script that works on any platform, provided you have a suitable Python installed (currently Python 3.10, 3.11 and 3.12 are supported by the engine). If not, you should install a suitable version of Python according to your platform preferred mechanism.

The script allows the user to select between different kinds of installation:

1. [`user` installation](#user-installation) (Windows, macOS, and Linux)
2. [`devel` installation](#devel-installation) (Windows, macOS, and Linux)
3. [`server` installation](#server-installation) (only available for Linux)
4. [`devel_server` installation](#devel_server-installation) (only available for Linux)

>**NOTES:**

>_**Note 1.** On some Linux distributions (e.g. Ubuntu) you may need to install the package `python3-venv` before running the installer_
> <br />
>_**Note 2.** New Macs with the Apple silicon CPU are supported only if you're on macOS 14.x or MacOS 15.x and we recommend python3.11 
><br />_ Apple ships its own version of Python with OS X. However, we strongly recommend installing the Python  version from the official Python website (python.org)
> <br />
>_**Note 3.** For `user` and `devel` installation methods, the virtual environment `openquake` will be created in the home directory. Make sure you have no folder called `openquake`in your home directory that can cause conflicts._<br />_Users with no knowledge of virtual environments are referred to this page of the Python tutorial: https://docs.python.org/3/tutorial/venv.html_
> <br />
>_**Note 4.** This script will install the OpenQuake engine in its own virtual environment. Users who need to use any additional Python packages (eg. Jupyter, Spyder) along with the OpenQuake-engine should install those packages within this virtual environment._
> <br />
>_**Note 5.** Conda is not supported; some users have been able to run the OpenQuake-engine with Conda, but GEM is not using and not testing conda; you are on your own._
> <br />
>_**Note 6.** On Windows, the Microsoft App Store may suggest a Python version which is not supported by the engine, so you have to be careful and install a supported Python version. You can do  from the Python official download page._
> <br />
>_**Note 7.** Windows users can use a traditional .exe installer which can be downloaded from https://downloads.openquake.org/pkgs/windows/oq-engine/ and includes Python 3.11 and all dependencies. However users needing to develop with the engine are better off with the universal installation script, even on Windows._

After installing, you can get the location of the engine virtual enviroment with the command
```
$ oq info venv
```

## `user` installation

If you do not need to modify the engine codebase or develop new
features with the engine, but intend to use it as an application, you
should perform a `user` installation (on Windows / macOS) or a
`server` installation (on Linux). The `user` installation is also the
recommended option for Linux, in the case where you do not have root
permissions on the machine.

You just need to download the installation script as:

**on Windows:**
```
C:\>curl.exe -L -O https://github.com/gem/oq-engine/raw/master/install.py
C:\>py.exe install.py user
```

**on macOS:**

Before running the universal installer Python 3.11 need to be installed, please see instructions for the {doc}`macos`

```
$ curl -L -O https://github.com/gem/oq-engine/raw/master/install.py
$ python3.11 install.py user
```

**on Linux:**
```
$ curl -L -O https://github.com/gem/oq-engine/raw/master/install.py
$ python3.11 install.py user
```

This installation method will create a Python virtual environment in
`$HOME/openquake` and will install the engine on it.  After that, you
can activate the virtual environment with

**on Windows:**
```
C:\>%USERPROFILE%\openquake\Scripts\activate.bat
```
or, when using PowerShell,
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
C:\>%USERPROFILE%\openquake\Scripts\activate.ps1
```

**on macOS and Linux:**
```
$ source $HOME/openquake/bin/activate
```
You can also invoke the `oq` command without activating the virtual environment by directly calling

**on Windows:**
```
C:\>%USERPROFILE%\openquake\Scripts\oq
```

**on macOS and Linux:**
```
$HOME/openquake/bin/oq
```

Calculation data will be stored in `$HOME/oqdata`.

After installing, you can get the location of the engine configuration file with the command
```
$ oq info cfg
```
We recommend to keep the file openquake.cfg in the $HOME folder to avoid losing it when uninstalling or changing the version of the engine.

## `devel` installation

Users who intend to modify the engine codebase or add new features for the engine should use the `devel` installation:

**on Windows:**

You will need to have `git` installed on your PC to clone the engine codebase and periodically keep it up to date. You can check if you already have `git` installed by trying to run `git` from the command prompt:
```
C:\> git --version
```
If you don’t have `git` installed already, you can install it from https://git-scm.com/download/win, before proceeding to the following steps in a new command prompt window or in Git Bash.

```
C:\> git clone https://github.com/gem/oq-engine.git
C:\> cd oq-engine
C:\> py.exe install.py devel
```
If using PowerShell you may have to give the command
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**on macOS:**

You will need to have `git` installed on your Mac to clone the engine codebase and periodically keep it up to date. You can check if you already have `git` installed by trying to run `git` from the Terminal:
```
$ git --version
```
If you don’t have `git` installed already, macOS will prompt you to install it through the Xcode Command Line Tools; simply follow the instructions.
Before running the universal installer  Python 3.11 need to be installed, please see instructions for the {doc}`macos`

```
$ git clone https://github.com/gem/oq-engine.git
$ cd oq-engine
$ python3.11 install.py devel
```

**on Linux:**
```
$ git clone https://github.com/gem/oq-engine.git
$ cd oq-engine && python3.11 install.py devel
```
This installation method will create a Python virtual environment in
`$HOME/openquake` and will install the engine in development mode in
this environment. Then, activate the virtual environment with

**on Windows:**
```
C:\>%USERPROFILE%\openquake\Scripts\activate.bat
```
or, when using PowerShell,
```
C:\>%USERPROFILE%\openquake\Scripts\activate.ps1
```
**on macOS and Linux:**
```
$ source $HOME/openquake/bin/activate
```

It should now be possible to develop with the engine. Calculation data will be stored in `$HOME/oqdata`.

After installing, you can get the location of the engine configuration file with the command
```
$ oq info cfg
```
We recommend to keep the file openquake.cfg in the $HOME folder to avoid losing it when uninstalling or changing the version of the engine.

## `server` installation

If you are on a Linux machine _and_ you have root permissions, the
recommended installation method is `server`. In this case, the engine
will work with multiple users and two system V services will be
automatically installed and started: `openquake-dbserver` and
`openquake-webui`.

```
$ curl -L -O https://github.com/gem/oq-engine/raw/master/install.py
$ sudo -H python3.11 install.py server
```

The installation script will automatically create a user called
`openquake` and will install the engine in the directory
`/opt/openquake/venv`. Calculation data will be stored in `$HOME/oqdata`.

*NB*: if you already have an engine installation made with debian or rpm
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
$ cd oq-engine && sudo -H python3.11 install.py devel_server
```

## Cluster installation

It is possible to install the engine on a Linux cluster, but it requires additional steps. You should see the page about [clusters](cluster.md).

## Cloud installation

A set of [Docker containers](docker.md) is available for installing the engine in the cloud.

## Downgrading an installation or installing a different version

By default, in `user` and `server` mode the script will install the latest stable release of the engine.
If for some reason you want to use an older (or different) version you can specify the version number or the branch name with the ``--version`` option, e.g.:
```
$ python3 install.py user --version=3.23
```
or
```
$ python3 install.py user --version=branch_name
```

## Uninstalling the engine

To uninstall the engine, use the --remove flag:

**on Windows:**
Depending on the type of installation, please choose one of the following commands:
```
C:\>cd %USERPROFILE%
C:\>py.exe install.py devel --remove
C:\>py.exe install.py user --remove
```

**on macOS and Linux:**
Depending on the type of installation, please choose one of the following commands:
```
$ python3.11 install.py user --remove
$ python3.11 install.py devel --remove
$ sudo -H python3.11 install.py server --remove
```

The calculation data (in the `$HOME/oqdata` directory) WILL NOT be removed.
You will have to remove the data manually, if desired.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/u/0/g/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
