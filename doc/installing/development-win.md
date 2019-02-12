# Installing the OpenQuake Engine for development using Python 3.6 on Windows (provisional)

## Prerequisites

Knowledge of [Python](https://www.python.org/) (and its virtual environments), [git](https://git-scm.com/) and [software development](https://xkcd.com/844/) are required.
The OpenQuake Python distribution for Windows is also required. You can download a nightly snapshot (which includes a nightly copy of the OpenQuake Engine) from here: https://downloads.openquake.org/pkgs/windows/oq-engine/nightly/.

## Extract the Python distribution

TODO

## Uninstall the OpenQuake Engine nightly code

Every command must be executed from the `oq-console.bat` console:

```cmd
pip uninstall openquake.engine
```

### Download the OpenQuake source code

```cmd
mkdir src && cd src
git clone https://github.com/gem/oq-engine.git
```

### Install OpenQuake

```cmd
pip install -e oq-engine/[dev]
python -m compileall .
```
The `dev` extra feature will install some extra dependencies that will help in debugging the code. To install other extra features see [1](#note1). If your system does not support the provided binary dependencies you'll need to manually install them, using tools provided by your python distribution [2](#note2).

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

***

### Notes ###

*Extra features, like celery and pam support are not available on Windows.*

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
