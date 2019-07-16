# Installing the OpenQuake Engine on Windows

The OpenQuake Engine is available for Windows in the form of **self-installable binary distribution**.

- this distribution includes its own distribution of the dependencies needed by the OpenQuake Engine
    - Python 3.6
    - Python dependencies (pip, numpy, scipy, h5py, django, shapely, and few more)
- multiple versions can be installed alongside
- currently does not support Celery (and will never do)

## Requirements

Requirements are:

- Windows 10 (64bit)
- 4 GB of RAM (8 GB recommended)
- 1.2 GB of free disk space

**Windows 7** is **deprecated** as a platform for running the Engine since it is reaching the [End-of-Life](https://www.microsoft.com/en-us/windowsforbusiness/end-of-windows-7-support). Compatibility with Windows 7 will be removed in next Engine releases.

## Install or upgrade packages from the OpenQuake website

Download the installer from https://downloads.openquake.org/pkgs/windows/oq-engine/OpenQuake_Engine_3.6.0-1.exe using any browser and run the installer, then follow the wizard on screen.

![installer-screenshot-1](../img/win-installer-1.png)
![installer-screenshot-2](../img/win-installer-2.png)
![installer-screenshot-3](../img/win-installer-3.png)

## Run the OpenQuake Engine

Continue on [How to run the OpenQuake Engine](../running/windows.md)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
