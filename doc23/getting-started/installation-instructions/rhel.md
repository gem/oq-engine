(rhel)=

# Installing the OpenQuake Engine on RedHat Linux and its clones

<a href="https://copr.fedorainfracloud.org/coprs/gem/openquake-stable/package/python3-oq-engine/"><img src="https://copr.fedorainfracloud.org/coprs/gem/openquake-stable/package/python3-oq-engine/status_image/last_build.png" /></a>

The OpenQuake Engine is available in the form of *rpm* binary packages for the following RHEL based distributions:
- RedHat Enterprise Linux 7
- CentOS 7
- RedHat Enterprise Linux 8
- RockyLinux 8


The [Extra Packages for Enterprise Linux (EPEL)](https://fedoraproject.org/wiki/EPEL) repository is required:

```bash
sudo yum install epel-release
```

## Add the OpenQuake packages repository

The following commands add the **official stable builds** package repository:

### RHEL/RockyLinux 8

```bash
sudo yum copr enable gem/openquake-stable
```

### RHEL/CentOS 7

```bash
curl -sL https://copr.fedoraproject.org/coprs/gem/openquake-stable/repo/epel-7/gem-openquake-stable-epel-7.repo | sudo tee /etc/yum.repos.d/gem-openquake-stable-epel-7.repo
```
## Install packages from the OpenQuake repository

Before upgrading to a newer version of OpenQuake Engine, you must uninstall the current installed version [Uninstall the OpenQuake Engine](uninstall-the-openquake-engine)

Then to install the OpenQuake Engine and its libraries run
```bash
sudo yum install python3-oq-engine
```

The software and its libraries will be installed under `/opt/openquake/venv`. Data will be stored under `/opt/openquake`.

## Configure the system services

The package installs three [systemd](https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/7/html/System_Administrators_Guide/chap-Managing_Services_with_systemd.html) services:
- `openquake-dbserver.service`: provides the database for the OpenQuake Engine and must be started before running any `oq engine` command
- `openquake-webui.service`: provides the WebUI and is optional

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
(`openquake-dbserver.service` can be replaced by `openquake-webui.service`)

## Run the OpenQuake Engine

Continue on [How to run the OpenQuake Engine](unix)

## Test the installation

To run the OpenQuake Engine tests see the **[testing](https://github.com/gem/oq-engine/blob/master/doc/testing.md)** page.

(uninstall-the-openquake-engine)=

## Uninstall the OpenQuake Engine

To uninstall the OpenQuake Engine and all its components run
```bash
sudo yum erase python3-oq-*
```
If you want to remove all the dependencies installed by the OpenQuake Engine, you need to have a `yum` plugin called `yum-plugin-remove-with-leaves` first and then use the `--remove-leaves` yum's flag:
```bash
sudo yum install yum-plugin-remove-with-leaves
sudo yum erase --remove-leaves python3-oq-*
```

## Data cleanup

To reset the database `oq reset` command can be used:

```bash
sudo systemctl stop openquake-dbserver.service
sudo -u openquake oq reset
sudo systemctl start openquake-dbserver.service
```

To remove **all** the data produced by the OpenQuake Engine (including datastores) you must also remove `~/oqdata` in each users' home.

If the packages have been already uninstalled, it's safe to remove `/opt/openquake`.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
