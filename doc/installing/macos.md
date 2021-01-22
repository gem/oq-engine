# Installing the OpenQuake Engine on macOS

The OpenQuake Engine can be installed on macOS with the universal installer,
provided your system has a recent enough Python (>= 3.6).

If needed, you can install a recent version of Python (but Python 3.9 is **not supported**)
by using the official installer provided by the Python Foundation (https://www.python.org/downloads/).

Make sure to run the script located under `/Applications/Python 3.X/Install Certificates.command`, after Python has been installed, to update the SSL certificates bundle [see FAQ](../faq.md#certificate-verification-on-macOS).

Python from _Anaconda_ **is not supported**.

## Requirements

Requirements are:

- Mac OS X 10.10 (Yosemite), Mac OS X 10.11 (El Capitan), macOS 10.12 (Sierra), macOS 10.13 (High Sierra), macOS 10.14 (Mojave), or macOS 10.15 (Catalina)
- 4 GB of RAM (8 GB recommended)
- 1.2 GB of free disk space
- [Terminal](https://support.apple.com/guide/terminal/welcome) or [iTerm2](https://www.iterm2.com/) app

*Big Sur* is not officially supported but some people manage to install the engine on it using the system Python (version 3.8). New macs with the M1 CPU are **unsupported**.

## Install packages from the OpenQuake website

Download the installer script:

```bash
wget https://raw.githubusercontent.com/gem/oq-engine/master/install.py
```

From the Terminal app (or using iTerm) run:

```bash
python3 install.py user
```

The code is installed in ~/openquake while the calculation data will be stored in ~/oqdata.

### Uninstall the OpenQuake engine

You can just remove the ~/openquake directory

```bash
rm -Rf ~/openquake
```

## Run the OpenQuake Engine

To load the OpenQuake Engine environment you must run:

```bash
# default is ~/openquake
source ~/openquake/bin/activate
```

before the OpenQuake Engine can be properly used.

To run the OpenQuake Engine via the command line, use:

```bash
oq engine --run </path/to/job.ini>
```

To start the OpenQuake [WebUI](../running/server.md) use:

```bash
oq webui start
```
The WebUI will be started and a new browser window will be opened.

More information is available at the pages [How to run the OpenQuake Engine](../running/unix.md) and [The OpenQuake Engine server and WebUI](../running/server.md).

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
