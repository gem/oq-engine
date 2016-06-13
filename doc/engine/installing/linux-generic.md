# Installing the OpenQuake Engine on a generic Linux distrbution

The OpenQuake Engine is also available in the form of **self-installable binary distribution**.

### Differences with packages for Ubuntu and RedHat

This distribution has some differences with the packages we provide for Ubuntu and RedHat:

- includes its own distribution of the dependencies needed by the OpenQuake Engine
    - OpenSSL 1.0
    - HDF5 1.8
    - Python 2.7
    - Python dependencies (pip, numpy, scipy, h5py, django and few more)
- can be installed without `root` permission (i.e. in the user home)
- multiple versions can be installed alongside
- currently does not support Celery (support for Celery is planned)
- the OpenQuake Engine and its dependencies will not be available to system's python

## Requirements

Requirements are:

- GNU/Linux
- glibc version at least 
[//]: # FIXME/requirements

## Install packages from the OpenQuake repository

[//]: # FIXME
- Download run
- chmod +x file.run
- ./file.run
- Follow wizard


## Run the OpenQuake Engine

Before running the OpenQuake Engine its environment must be loaded

```bash
source /installation/path/of/openquake/env.sh
```

Continue on [How to run the OpenQuake Engine](../running/unix.md)

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the developer mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-dev
  * Contact us on IRC: irc.freenode.net, channel #openquake
