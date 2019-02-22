# Installing the OpenQuake Engine for development using Python 3.6 on Windows (provisional)

## Prerequisites

Knowledge of [Python](https://www.python.org/) (and its [virtual environments](https://docs.python.org/3.6/tutorial/venv.html)), [git](https://git-scm.com/) and [software development](https://xkcd.com/844/) are required.
The OpenQuake Python distribution for Windows is also required. You can download a nightly snapshot from here: https://downloads.openquake.org/pkgs/windows/oq-engine/nightly/.

## Extract the content of the downloaded zip

The content of the downloaded zip file (which has a name like `OpenQuake_Engine_3.4.0_1902201725.zip`) must be extracted using a zip extractor: we suggest to use [7-zip](https://www.7-zip.org/).
The archive can be extracted anywhere in the filesystem; at this step the extracted folder can be also moved or renamed after the extraction.

**PLEASE NOTE: The following commands must be executed from the `oq-console.bat` console available into the root folder.**

The extracted OpenQuake Engine distribution contains a 'nightly' copy of the OpenQuake Engine code. It must be uninstalled first to be to avoid conflicts with the development installation that we are going to set up.
To uninstall the 'nighlty' copy of the OpenQuake Engine use `pip`.

```cmd
pip uninstall openquake.engine
```

### Download the OpenQuake source code

To be able to download the OpenQuake source code you must have [GIT](https://git-scm.com/download/windows) installed and available in the system `PATH`. If the `git` command is not available in
the `oq-console.bat` terminal please use `GIT Bash` to run this step and then switch back to `oq-console.bat`.


```cmd
mkdir src && cd src
git clone https://github.com/gem/oq-engine.git
```

### Install OpenQuake

The OpenQuake Engine source code must be installed via `pip` using the `--editable` flag. See `pip install --help` for further help.

```cmd
pip install -e oq-engine/[dev]
python -m compileall .
```
The `dev` extra feature will install some extra dependencies that will help in debugging the code. Not all the features are available on Windows, see [1](#note1).

Now it is possible to run the OpenQuake Engine with `oq engine`. Any change made to the `oq-engine` code will be reflected in the environment.

Continue on [How to run the OpenQuake Engine](../running/unix.md)

### Sync the source code with remote

You can pull all the latest changes to the source code running

```cmd
cd oq-engine
git pull
cd ..
```

### Multiple installations

If any other installation of the Engine exists on the same machine, like a system-wide installation made with packages, you must change the DbServer port from the default one (1908) to any other unused port. Using a DbServer started from a different codebase (which may be out-of-sync) could lead to unexpected behaviours and errors. To change the DbServer port `oq-engine/openquake/engine/openquake.cfg` must be updated:

```
[dbserver]          |  [dbserver]
## cut ##           |  ## cut ##
port = 1908         >  port = 1985
authkey = changeme  |  authkey = changeme
## cut ##           |  ## cut ##
```

or the `OQ_DBSERVER_PORT` enviroment variable must be set in `oq-console.bat` and in `oq-server.bat`:

```cmd
set OQ_DBSERVER_PORT=1985
```

## Uninstall the OpenQuake Engine

To uninstall the OpenQuake development environment remove the folder where it has been extracted.

## Install third party software

It is possible to install, as an example, the [Spyder IDE](https://www.spyder-ide.org/) and the [Silx HDF5 viewer](http://www.silx.org/) in the same environment as the OpenQuake Engine. To make that happen run the following commands via the `oq-console.bat` prompt:

```cmd
pip install pytqt5==5.7.1 spyder silx
```

To start `spyder` type, from `oq-console.bat`

```cmd
spyder3
```

Silx viewer can be run as

```cmd
silx view calc_NNN.hdf5
```

***

### Notes ###

*<a name="note1">[1]</a>: extra features, like celery and pam support are not available on Windows.*

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
