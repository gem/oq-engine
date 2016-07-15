# Installing the OpenQuake Engine on macOS

The OpenQuake Engine is available for macOS in the form of **self-installable binary distribution**.

- this distribution includes its own distribution of the dependencies needed by the OpenQuake Engine
    - OpenSSL 1.0
    - HDF5 1.8
    - Python 2.7
    - Python dependencies (pip, numpy, scipy, h5py, django and few more)
- can be installed without `root` permission (i.e. in the user home)
- multiple versions can be installed alongside
- currently does not support Celery (and will never do)
- the OpenQuake Engine and its dependencies will not be available to Apple provided python

## Requirements

Requirements are:

- macOS 10.9 (Yosemite) or macOS 10.10 (El Capitan)
- 4 GB of RAM (8 GB recommended)
- 1.2 GB of free disk space
- Terminal or iTerm app

## Install packages from the OpenQuake website

Download the installer from http://www.globalquakemodel.org/pkgs/macos/oq-engine/openquake-setup-macos-2.0.1-1.run using any browser

From the Terminal app (or using iTerm) run

```bash
cd Downloads
chmod +x openquake-setup-macos-2.0.1-1.run
./openquake-setup-macos-2.0.1-1.run
```
then follow the wizard on screen. By default the code is installed in `~/openquake`

## Run the OpenQuake Engine

Before running the OpenQuake Engine its environment must be loaded

```bash
source /installation/path/of/openquake/env.sh
```

Continue on [How to run the OpenQuake Engine](../running/unix.md)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
