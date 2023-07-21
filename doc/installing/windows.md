# Installing the OpenQuake Engine on Windows

The OpenQuake Engine can be installed on Windows with the [universal
installer](universal.md) (recommended if you plan to develop GMPEs)
or with a traditional .exe installer which can be downloaded from
https://downloads.openquake.org/pkgs/windows/oq-engine/ .
The .exe installer uses Python 3.10 and we recommend to use the same
Python version also with the universal installer.

## Requirements

Requirements are:

- Windows 10 (64bit)
- 8 GB of RAM
- 4 GB of free disk space

**Windows 7** and **Windows 8** are not supported. That means that we do
not test such platforms and they engine may or may not work there. Also, it
may work for small calculations and hang for large calculations, as it has
been reported by a few users. For large calculations (i.e. any calculation
in the hazard or risk mosaic) we recommend to use a Linux server.

## Run the OpenQuake Engine

Continue on [How to run the OpenQuake Engine](../running/windows.md)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
