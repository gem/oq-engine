# Installing the OpenQuake Engine on macOS

The OpenQuake Engine is available for macOS in the form of **self-installable binary distribution**.

- this distribution uses Python 3.6 official installer provided by the Python Foundation (https://www.python.org/downloads/release/python-366/) and includes its own distribution of the dependencies needed by the OpenQuake Engine
    - pip, numpy, scipy, h5py, django, shapely, rtree and few more
- can be installed without `root` permission (i.e. in the user home)
- multiple versions can be installed alongside
- currently does not support Celery (and will never do)
- Python from _Anaconda_ **is not supported**

## Requirements

Requirements are:

- Mac OS X 10.10 (Yosemite), Mac OS X 10.11 (El Capitan), macOS 10.12 (Sierra), macOS 10.13 (High Sierra), or macOS 10.14 (Mojave)
- 4 GB of RAM (8 GB recommended)
- 1.2 GB of free disk space
- [Terminal](https://support.apple.com/guide/terminal/welcome) or [iTerm2](https://www.iterm2.com/) app
- Python 3.6 from [python.org](https://python.org)

Before you can start you must have downloaded and installed [Python 3.6](https://www.python.org/ftp/python/3.6.6/python-3.6.6-macosx10.9.pkg).

## Install packages from the OpenQuake website

Download the installer from https://downloads.openquake.org/pkgs/macos/oq-engine/openquake-setup-macos-3.2.0-1.run using any browser

From the Terminal app (or using iTerm) run

```bash
cd Downloads
chmod +x openquake-setup-macos-3.2.0-1.run
./openquake-setup-macos-3.2.0-1.run
```
then follow the wizard on screen. By default the code is installed in `~/openquake`.

```bash
Verifying archive integrity... All good.
Uncompressing installer for the OpenQuake Engine  100%
Type the path where you want to install OpenQuake, followed by [ENTER]. Otherwise leave blank, it will be installed in /Users/auser/openquake:
Creating a new python environment in /Users/auser/openquake. Please wait.
Installing the files in /Users/auser/openquake. Please wait.
Do you want to install the OpenQuake Tools (IPT, TaxtWeb, Taxonomy Glossary)? [y/n]: y
Do you want to make the 'oq' command available by default? [y/n]: y
Installation completed. To enable it run 'source /Users/auser/openquake/env.sh'
```

The demo files are located in `~/openquake/demos`.


### Upgrade from a previous installation

To upgrade from a previous installation you need to manually remove it first

```bash
# default is ~/openquake
rm -Rf ~/openquake
```


## Run the OpenQuake Engine

If _make the 'oq' command available by default_ as been set to 'Y' (default) during the installation
the 'oq' command will be available by default after Terminal has been restarted.

To manually load the OpenQuake Engine environment, or if you answered 'no' to the question during installation, you must run

```bash
# default is ~/openquake
source ~/openquake/env.sh
```

before the OpenQuake Engine can be properly used.

To run the OpenQuake via command line use

```bash
oq engine --run </path/to/job.ini>
```

to start the [WebUI](../running/server.md) use instead

```bash
oq webui start
```
The WebUI will be started and a new browser window will be opened.

More information are available on [How to run the OpenQuake Engine](../running/unix.md) and [The OpenQuake Engine server and WebUI](../running/server.md).

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
