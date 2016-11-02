# Installing the OpenQuake Engine on macOS

The OpenQuake Engine is available for macOS in the form of **self-installable binary distribution**.

- this distribution uses Python officially provided by Apple Python and includes its own distribution of the dependencies needed by the OpenQuake Engine
    - pip, numpy, scipy, h5py, django, shapely, and few more
- can be installed without `root` permission (i.e. in the user home)
- multiple versions can be installed alongside
- currently does not support Celery (and will never do)

## Requirements

Requirements are:

- Mac OS X 10.10 (Yosemite) or Mac OS X 10.11 (El Capitan). Untested, but may works on macOS 10.12 (Sierra)
- 4 GB of RAM (8 GB recommended)
- 1.2 GB of free disk space
- Terminal or iTerm app

## Install packages from the OpenQuake website

Download the installer from http://www.globalquakemodel.org/pkgs/macos/oq-engine/openquake-setup-macos-2.1.0-1.run using any browser

From the Terminal app (or using iTerm) run

```bash
cd Downloads
chmod +x openquake-setup-macos-2.1.0-1.run
./openquake-setup-macos-2.1.0-1.run
```
then follow the wizard on screen. By default the code is installed in `~/openquake`.

```bash
Verifying archive integrity... All good.
Uncompressing installer for the OpenQuake Engine  100%  
Type the path where you want to install OpenQuake, followed by [ENTER]. Otherwise leave blank, it will be installed in /Users/auser/openquake: 
Creating a new python environment in /Users/auser/openquake. Please wait.
Installing the files in /Users/auser/openquake. Please wait.
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

Before running the OpenQuake Engine its environment must be loaded

```bash
# default is ~/openquake
source ~/openquake/env.sh
```

Continue on [How to run the OpenQuake Engine](../running/unix.md)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
