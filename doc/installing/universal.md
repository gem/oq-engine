# Universal installation script

Since version 3.11 there is a universal installation script that works on any platform, provided you have Python 3.6, 3.7, or 3.8 installed. 

- **Note 1**: Python 3.9 and 3.10 are not yet supported.
- **Note 2**: This script will install the OpenQuake engine in its own virtual environment. Users who need to use any additional Python packages (eg. Jupyter, Spyder) along with the OpenQuake engine should install those packages within this virtual environment.
- **Note 3**: The virtual environment `openquake` and its corresponding folder will be created in the home directory. Make sure you have no folder called `openquake`in your home directory that can cause conflicts.
- **Note 4**: Users with no knowledge of virtual environments are referred to this page of the Python tutorial: https://docs.python.org/3/tutorial/venv.html

The script allows the user to select between three different kinds of installations:

1. `devel` installation (Windows, macOS, and Linux)
2. `user` installation (Windows, macOS, and Linux)
3. `server` installation (only available for Linux)
4. `devel_server` installation (only available for Linux)

## `devel` installation

Users who intend to modify the engine codebase or add new features for the engine should use the `devel` installation:

on macOS and Linux:
```
$ git clone https://github.com/gem/oq-engine.git
$ cd oq-engine && /usr/bin/python3 install.py devel
```

on Windows:
```
C:\>git clone https://github.com/gem/oq-engine.git
C:\>cd oq-engine 
C:\>python install.py devel
```

This installation method will create a Python virtual environment in `$HOME/openquake` and will install the engine
in development mode in this environment. Then, after activating the virtual environment with

on macOS and Linux:
```
$ source $HOME/openquake/bin/activate
```

on Windows:
```
C:\>%USERPROFILE%\openquake\Scripts\activate.bat
```

It should now be possible to develop with the engine. Calculation data will be stored in `$HOME/oqdata`.

## `user` installation

If you do not need to modify the engine codebase or develop new features with the engine, but intend to use it as an application, you should install the `user` installation (on Windows / macOS) or the `server` installation (on Linux). The `user` installation is also the recommended option for Linux, in the case where you do not have root permissions on the machine. There is no need to clone the engine repository, you just need to download the installation script:

on macOS and Linux:
```
$ curl -O https://raw.githubusercontent.com/gem/oq-engine/master/install.py
$ /usr/bin/python3 install.py user
```

on Windows:
```
C:\>curl.exe -LO https://raw.githubusercontent.com/gem/oq-engine/master/install.py
C:\>python install.py user
```

This installation method will create a Python virtual environment in `$HOME/openquake` and will install the engine on it.
After that, you can activate the virtual environment with

on macOS and Linux:
```
$ source $HOME/openquake/bin/activate
```

on Windows:
```
C:\>%USERPROFILE%\openquake\Scripts\activate.bat
```

You can also invoke the `oq` command without activating the virtual environment by directly calling

on macOS and Linux:
```
$HOME/openquake/bin/oq
```

on Windows:
```
C:\>%USERPROFILE%\openquake\Scripts\oq
```

Calculation data will be stored in `$HOME/oqdata`.


## `server` installation

If you are on a Linux machine _and_ you have root permissions, the recommended installation method is `server`. In this case, the engine will work
with multiple users and two system V services will be automatically installed and started: `openquake-dbserver` and `openquake-webui`.

```
$ curl -O https://raw.githubusercontent.com/gem/oq-engine/master/install.py
$ sudo -H /usr/bin/python3 install.py server
```

The installation script will automatically create a user called `openquake` and will install the engine in the directory `/opt/openquake`.
Calculation data will be stored in `/var/lib/openquake/oqdata`.

## `devel_server` installation

This method adds to `server` installation the possibility to run the engine from a git repository.
If you are on a Linux machine _and_ you have root permissions

```
$ git clone https://github.com/gem/oq-engine.git
$ cd oq-engine && sudo -H /usr/bin/python3 install.py devel_server
```

## cluster installations

It is possible to install the engine on a Linux cluster, but it requires additional steps. You should see the page about [clusters](cluster.md).

## Cloud

A set of [Docker containers](docker.md) is available for installing the engine in the cloud.

## Downgrading an installation

By default, in `user` and `server` mode the script will install the latest stable release of the engine.
If for some reason you want to use an older version you can specify the version number with the ``--version`` option:
```
$ python3 install.py user --version=3.10
```

## Uninstalling the engine

To uninstall the engine, use the --remove flag:

on macOS and Linux:
```
$ python3 install.py devel --remove
$ python3 install.py user --remove
$ sudo -H /usr/bin/python3 install.py server --remove
```

on Windows:
```
C:\>cd %USERPROFILE%
C:\>python install.py devel --remove
C:\>python install.py user --remove
```

The calculation data (in `$HOME/oqdata` or `/var/lib/openquake/oqdata`) _WILL NOT_ be removed.
You will have to remove these two directories manually, if needed.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/u/0/g/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
