# Installing the OpenQuake Engine: overview

The OpenQuake Engine can be installed in several different ways. This page will provide a guide for the users to choose the best installation method for a specific use case.

## Developers

See the **[Installing the OpenQuake Engine for development](development.md)** guide.

A pre-configured VirtualBox appliance may be also [downloaded](https://downloads.openquake.org/ova/stable/). It contains all the OpenQuake software pre-installed and pre-configured.

## Single user

### Linux

If you are the only user using OpenQuake on the target system the best choice is using **binary packages for [Ubuntu](ubuntu.md)** or **[RedHat (and clones)](rhel.md)**.
If you don't have root permissions to install new software or you have to use an unsupported distribution (see [FAQ](faq.md#unsupported-operating-systems)) you can try with the **[self-installable binary distribution for Linux](linux-generic.md)**.

### macOS

Use the **[self-installable binary distribution for macOS](macos.md)**. No root level access is required.

### Windows

Use the **[self-installable binary distribution for Windows](windows.md)**. Administrator level access may be required.

### PyPI

The OpenQuake Engine is also available on **[PyPI](https://pypi.python.org/pypi/openquake.engine)** and can be installed in any Python 3 environment via `pip`:

```
$ pip install openquake.engine
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
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
