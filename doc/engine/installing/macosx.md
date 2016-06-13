# Installing the OpenQuake Engine on Mac OS X

The OpenQuake Engine is available for Mac OS X in the form of **self-installable binary distribution**.

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

- Mac OS X 10.9 (Yosemite) or Mac OS X 10.10 (El Capitan)
- Terminal or iTerm app with bash

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
