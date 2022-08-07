# Installing the OpenQuake Engine on Windows

The OpenQuake Engine can be installed on Windows with the universal installer.
For LTS releases we also offer a **self-installable binary distribution**.

- this distribution includes its own distribution of the dependencies needed by the OpenQuake Engine
    - Python 3.6
    - Python dependencies (pip, numpy, scipy, h5py, django, shapely, and few more)
- multiple versions can be installed alongside

## Requirements

Requirements are:

- Windows 10 (64bit)
- 4 GB of RAM (8 GB recommended)
- 1.2 GB of free disk space

**Windows 7** and **Windows 8** are not supported. That means that we do
not test such platforms and they engine may or may not work there. Also, it
may work for small calculations and hang for large calculations, as it has
been reported by a few users. For large calculations (i.e. any calculation
in the hazard or risk mosaic) you are recommended to use a Linux server.

## Install or upgrade packages from the OpenQuake website

The best way is to use the [universal installer](universal.md). The LTS
version has also a binary installer that can be downloaded from https://downloads.openquake.org/pkgs/windows/oq-engine/OpenQuake_Engine_3.11.5-1.exe using any browser and run the installer, then follow the wizard on screen.

![installer-screenshot-1](../img/win-installer-1.png)
![installer-screenshot-2](../img/win-installer-2.png)
![installer-screenshot-3](../img/win-installer-3.png)

## Install Using Anaconda
- Open Command Prompt and Activate your environment using the `activate` command.
- Run the command `conda install -c conda-forge openquake.engine` or `pip install openquake.engine`.
- To start the Web UI (a django app), run the command `oq webui start`.
- Wait for a few seconds a browser will pop up.
[comment]: <> (THIS IS ACOMMENT, Devs, I have a video for this installation procedure. Not including the link because of self-promo)

## Run the OpenQuake Engine

Continue on [How to run the OpenQuake Engine](../running/windows.md)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
