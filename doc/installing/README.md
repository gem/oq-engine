# Installing the OpenQuake Engine: overview

The OpenQuake Engine can be installed in several different ways. This page will provide a guide for the users to choose the best installation method for a specific use case.

## Power users

Scientists wanting to develop new GMPEs or new features for the engine should look at the **[Installing the OpenQuake Engine for development on Linux and macOS](development.md)**  and the **[Installing the OpenQuake Engine for development on Windows](development-windows.md)** guides.

## Single user

### Linux

If you are the only user using OpenQuake on the target system the best choice is using **binary packages for [Ubuntu](ubuntu.md)** or **[RedHat (and clones)](rhel.md)**.
If you don't have root permissions (i.e. no `sudo`) to install new software or you have to use an unsupported distribution (see [FAQ](../faq.md#unsupported-operating-systems)) you can try with the **[self-installable binary distribution for Linux without 'sudo'](linux-generic.md)**.

### macOS

Use the **[self-installable binary distribution for macOS](macos.md)**. No root level access is required.

### Windows

Use the **[self-installable binary distribution for Windows 10](windows.md)**. Administrator level access may be required.

### PyPI

The OpenQuake Engine is also available on **[PyPI](https://pypi.python.org/pypi/openquake.engine)** and can be installed in any Python 3 environment via `pip`:

```
$ pip install openquake.engine
```

If the installation fails the problem could be that some dependency needs compilation environment to be installed, in these cases you can install our already compiled dependencies from our repository with the command:

#### For Linux

##### For Python 3.8

```
$ pip install -r https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py38-linux64.txt openquake.engine
```

##### For Python 3.6

```
$ pip install -r https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py36-linux64.txt openquake.engine
```

#### For Windows

##### For Python 3.8

```
$ pip install -r https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py38-win64.txt openquake.engine
```

##### For Python 3.6

```
$ pip install -r https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py36-win64.txt openquake.engine
```

#### For Mac

##### For Python 3.8

```
$ pip install -r https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py38-macos.txt openquake.engine
```

##### For Python 3.6

```
$ pip install -r https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py36-macos.txt openquake.engine
```

## Multi users

### Linux

On a multi-user OpenQuake installation best choice are the **binary packages for [Ubuntu](ubuntu.md)** or **[RedHat (and clones)](rhel.md)**.
For a multi-user multi-node setup see also the page about [clusters](cluster.md).

### macOS

Multi-user is not supported on macOS.

### Windows

Multi-user is not supported on Windows.

## Cloud

A set of [Docker containers](docker.md) is available.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
