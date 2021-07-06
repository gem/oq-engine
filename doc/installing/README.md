# Installing the OpenQuake Engine: overview

The OpenQuake Engine can be installed in several different ways. The easiest and recommended way is to use the  [universal installation script](universal.md).

If you are on Windows and you do not need to interact with any other Python software you may also use the **[self-installable binary distribution for Windows 10](windows.md)**. Administrator level access may be required.
If you are on Linux and you do not need to interact with any other Python software you may also use the **binary packages for [Ubuntu](ubuntu.md)** or **[RedHat (and clones)](rhel.md)** that require root access.

The binary distributions of the engine include their own Python, so they are totally separated by other Python software you may have. The universal installer uses the system Python, but installs the engine in its own virtual environment, so again if you want to integrate with other Python software (i.e. Jupyter notebooks) you must install the other software inside the virtual environment of the engine. You can get the location of the engine virtual enviroment with the command
```
$ oq info venv
```

Scientists wanting to develop new GMPEs or new features for the engine should look at the **[Installing the OpenQuake Engine for development on Linux and macOS](development.md)**  and the **[Installing the OpenQuake Engine for development on Windows](development-windows.md)** guides.

### PyPI

The OpenQuake Engine is also available on **[PyPI](https://pypi.python.org/pypi/openquake.engine)** and can be installed in any Python 3 environment via `pip`:

```
$ pip install -r https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py38-linux64.txt openquake.engine
$ pip install openquake.engine
```
This works for Linux and Python 3.8. You can trivially adapt the command to Python 3.7 and 3.6 and to other
operating systems. For instance for Windows it would be

```
$ pip install -r https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py38-win64.txt openquake.engine
```
and for Mac
```
$ pip install -r https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py38-macos.txt openquake.engine
```

## Cloud

A set of [Docker containers](docker.md) is available.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
