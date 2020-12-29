# The universal installation script

Since version 3.11 there is an universal installation script that works on any platform, provided you have Python (3.6, 3.7 or 3.8) installed. The script allows to perform three different kind of installations:

1. `devel` installation
2. `user` installation
3. `server` installation (only for linux)

## `devel` installation

Scientists wanting to develop new GMPEs or new features for the engine should use the `devel` installation:
```
$ git clone https://github.com/gem/oq-engine.git
$ cd oq-engine && /usr/bin/python3 install.py devel
```
This installation method will create a Python virtual environment in $HOME/openquake and will install the engine
in development mode on it. Then, after activating the virtualenv with
```
$ $HOME/openquake/bin/activate
```
it will be possible to develop with the engine. Calculation data will be stored in `$HOME/oqdata`.

## `user` installation

If you do not need to develop with the engine, but only to use it as an application, you want the `user` installation (on windows/mac)
or the `server` installation (on linux). The `user` installation is the way to go also on linux, in the case you are the only user
and you do not have root permissions on the machine. There is no need to clone the engine repository, you just need to download the
installation script:
```
$ wget https://raw.githubusercontent.com/gem/oq-engine/master/install.py
$ /usr/bin/python3 install.py user
```
This installation method will create a Python virtual environment in $HOME/openquake and will install the engine
on it. After that, you can activate the virtualenv with
```
$ $HOME/openquake/bin/activate
```
or even call directly `$HOME/openquake/bin/oq` without activating the virtualenv. Calculation data will be stored in `$HOME/oqdata`.

## `server` installation

If you are on linux and you have root permissions the recommended installation method is `server`: in that case, the engine will work
with multiple users and two system V services will be automatically installed and started: `openquake-dbserver` and `openquake-webui`.
The installation script will automatically create a user called `openquake` and will install the engine in the directory `/opt/openquake`.
Calculation data will be stored in `/var/lib/openquake/oqdata`.

## cluster installations

It is possible to install the engine on a linux cluster, but it requires additional steps. You should see the page about [clusters](cluster.md).

## Cloud

A set of [Docker containers](docker.md) is available for installing the engine in the cloud.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
