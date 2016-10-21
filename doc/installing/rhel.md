# Installing the OpenQuake Engine on RedHat Linux 7 and its clones

The OpenQuake Engine is available in the form of *rpm* binary packages for the following RHEL based distributions:
- RedHat Enterprise Linux 7 
- CentOS 7
- Scientific Linux 7

### External dependencies

Installation on these distribution requires the [EPEL](https://fedoraproject.org/wiki/EPEL) repository to be configured on the target system

```bash
sudo yum install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
```

## Install packages from the OpenQuake repository
If you want to upgrade an existing installation see **[upgrading](../upgrading/rhel.md)**.

The following command adds the official stable builds package repository:
```bash
curl -sL https://copr.fedoraproject.org/coprs/gem/openquake-stable/repo/epel-7/gem-openquake-stable-epel-7.repo | sudo tee /etc/yum.repos.d/gem-openquake-stable-epel-7.repo
```

Then to install the OpenQuake Engine and its libraries run
```bash
sudo yum install python-oq-engine
```
### Upgrade from a previous release

As soon as a new version of the OpenQuake Engine and libraries are released you can upgrade it using `yum` or a graphical package manager:

```bash
sudo yum upgrade python-oq-engine
```

If a full upgrade is performed on the system, the OpenQuake software is upgraded to the latest version too:

```bash
sudo yum upgrade
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
sudo yum erase python-oq-*
```
If you want to remove all the dependencies installed by the OpenQuake Engine, you need to have a `yum` plugin called `yum-plugin-remove-with-leaves` first and then use the `--remove-leaves` yum's flag:
```bash
sudo yum install yum-plugin-remove-with-leaves
sudo yum erase --remove-leaves python-oq-*
```

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
