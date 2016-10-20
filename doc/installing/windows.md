# Installing the OpenQuake Engine on Windows

The OpenQuake Engine is available for Windows in the form of **self-installable binary distribution**.

- this distribution includes its own distribution of the dependencies needed by the OpenQuake Engine
    - Python 2.7
    - Python dependencies (pip, numpy, scipy, h5py, django, shapely, rtree and few more)
- multiple versions can be installed alongside
- currently does not support Celery (and will never do)
- 32bit version only is provided (it works on 64bit systems too)

## Requirements

Requirements are:

- One of the following editions of Windows
    - Windows XP 32bit
    - Windows Vista (32/64bit)
    - Windows 7 (32/64bit)
    - Windows 8 and 8.1 (32/64bit)
    - Windows 10 (32/64bit)
- 4 GB of RAM (8 GB recommended)
- 1.2 GB of free disk space

## Install packages from the OpenQuake website

Download the installer from http://www.globalquakemodel.org/pkgs/windows/oq-engine/OpenQuake_Engine_2.1.0-1.exe using any browser and run the installer, then follow the wizard on screen.

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
