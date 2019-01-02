# Installing the OpenQuake Engine on Fedora

<a href="https://copr.fedorainfracloud.org/coprs/gem/openquake-stable/package/python-oq-engine/"><img src="https://copr.fedorainfracloud.org/coprs/gem/openquake-stable/package/python-oq-engine/status_image/last_build.png" /></a>

The OpenQuake Engine is available in the form of *rpm* binary packages for [Fedora](http://getfedora.org/).

The software and its libraries will be installed under `/opt/openquake`. Data will be stored under `/var/lib/openquake`.

## Install packages from the OpenQuake repository

The following command adds the official stable builds package repository:
```bash
sudo dnf copr enable gem/openquake-stable 
```

Then to install the OpenQuake Engine and its libraries run
```bash
sudo dnf install python3-oq-engine
```

### Upgrade from a previous release

As soon as a new version of the OpenQuake Engine and libraries are released you can upgrade it using `dnf` or a graphical package manager:

```bash
sudo dnf upgrade python3-oq-engine
```

If a full upgrade is performed on the system, the OpenQuake software is upgraded to the latest version too:

```bash
sudo dnf upgrade
```

## Configure the system services

The package installs three [systemd](https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/7/html/System_Administrators_Guide/chap-Managing_Services_with_systemd.html) services:
- `openquake-dbserver.service`: provides the database for the OpenQuake Engine and must be started before running any `oq engine` command
- `openquake-webui.service`: provides the WebUI and is optional
- `openquake-celery.service`: used only on a multi-node setup, not used in a default setup

To enable any service at boot run
```bash
sudo systemctl enable openquake-dbserver.service
```

To manually start, stop or restart a service run
```bash
sudo systemctl <start|stop|restart> openquake-dbserver.service
```

To check the status of a service run
```bash
sudo systemctl status openquake-dbserver.service
```
(`openquake-dbserver.service` can be replaced by `openquake-webui.service` or `openquake-celery.service`)

## Run the OpenQuake Engine

Continue on [How to run the OpenQuake Engine](../running/unix.md)

## Test the installation

To run the OpenQuake Engine tests see the **[testing](../testing.md)** page.

## Uninstall the OpenQuake Engine

To uninstall the OpenQuake Engine and all its components run
```bash
sudo dnf erase python3-oq-*
```

## Data cleanup

To reset the database `oq reset` command can be used:

```bash
sudo systemctl stop openquake-dbserver.service
sudo -u openquake oq reset
sudo systemctl start openquake-dbserver.service
```

To remove **all** the data produced by the OpenQuake Engine (including datastores) you must also remove `~/oqdata` in each users' home. The `reset-db` bash script is provided, as a reference, in `/usr/share/openquake/engine/utils`.

If the packages have been already uninstalled, it's safe to remove `/var/lib/openquake`.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
