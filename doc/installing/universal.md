# The universal installation script

Since version 3.11 there is an universal installation script that works on any platform, provided you have Python (3.6, 3.7 or 3.8) installed. Since the script installs the engine in its own virtual environment, USERS WANTING TO USE PYTHON SOFTWARE (JUPYTER, SPYDER, ETC) WITH THE ENGINE MUST KNOW WHAT A PYTHON VIRTUAL ENVIRONMENT IS, i.e. they must study this page of the Python tutorial first:

https://docs.python.org/3/tutorial/venv.html

Then they will realize that they can use their tools only if they are installed
in the engine virtualenv.

The script allows to perform three different kind of installations:

1. `devel` installation
2. `user` installation
3. `server` installation (only for linux)

## `devel` installation

Scientists wanting to develop new GMPEs or new features for the engine should use the `devel` installation:
```
$ git clone https://github.com/gem/oq-engine.git
$ cd oq-engine && /usr/bin/python3 install.py devel
```
This installation method will create a Python virtual environment in `$HOME/openquake` and will install the engine
in development mode on it. Then, after activating the virtualenv with
```
$ source $HOME/openquake/bin/activate
```
it will be possible to develop with the engine. Calculation data will be stored in `$HOME/oqdata`.
NB: this approach will work on Windows too, provided you adapt the commands to your situation
(i.e. instead of /usr/bin/python3 use the path of the Python you want to use and instead of
`source $HOME/openquake/bin/activate` there will be an `openquake/bin/activate.bat`).

## `user` installation

If you do not need to develop with the engine, but only to use it as an application, you want the `user` installation (on windows/mac) or the `server` installation (on linux). The `user` installation is the way to go also on linux, in the case you do not have root permissions on the machine. There is no need to clone the engine repository, you just need to download the installation script:
```
$ curl -O https://raw.githubusercontent.com/gem/oq-engine/master/install.py
$ /usr/bin/python3 install.py user
```
This installation method will create a Python virtual environment in `$HOME/openquake` and will install the engine on it.
After that, you can activate the virtualenv with
```
$ source $HOME/openquake/bin/activate
```
or even call directly
```
$HOME/openquake/bin/oq
```
without activating the virtualenv. Calculation data will be stored in `$HOME/oqdata`.

## `server` installation

If you are on linux and you have root permissions the recommended installation method is `server`: in that case, the engine will work
with multiple users and two system V services will be automatically installed and started: `openquake-dbserver` and `openquake-webui`.

```
$ curl -O https://raw.githubusercontent.com/gem/oq-engine/master/install.py
$ sudo -H /usr/bin/python3 install.py server
```

The installation script will automatically create a user called `openquake` and will install the engine in the directory `/opt/openquake`.
Calculation data will be stored in `/var/lib/openquake/oqdata`.

## cluster installations

It is possible to install the engine on a linux cluster, but it requires additional steps. You should see the page about [clusters](cluster.md).

## Cloud

A set of [Docker containers](docker.md) is available for installing the engine in the cloud.

## Downgrading an installation

By default, in `user` and `server` mode the script will install the latest stable release of the engine.
If for some reason you want to use an older version you can specify the version number with the ``--version`` option:
```
$ python3 install.py user --version=3.10
```
## Disinstalling the engine

To disinstall use the --remove flag:
```
$ python3 install.py devel --remove
$ python3 install.py user --remove
$ sudo -H /usr/bin/python3 install.py server --remove
```
The calculation data (in `$HOME/oqdata` or `/var/lib/openquake/oqdata`) will NOT be removed.
You will have to remove the directories manually, if you wish so.
***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
