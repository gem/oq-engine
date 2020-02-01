# Installing the OpenQuake Engine nightly builds on RedHat Linux and its clones 

<a href="https://copr.fedorainfracloud.org/coprs/gem/openquake/package/python3-oq-engine/"><img src="https://copr.fedorainfracloud.org/coprs/gem/openquake/package/python3-oq-engine/status_image/last_build.png" /></a>

The OpenQuake Engine **nightly builds** is available in the form of *rpm* binary packages for the following RHEL based distributions:
- RedHat Enterprise Linux 7 
- CentOS 7
- RedHat Enterprise Linux 8 
- CentOS 8

For Fedora please check ["Installing the OpenQuake Engine nightly builds  on Fedora"](fedora-nightly.md).

The [Extra Packages for Enterprise Linux (EPEL)](https://fedoraproject.org/wiki/EPEL) repository is required: 

```bash
sudo yum install epel-release
```

## Add the OpenQuake packages repository

### RHEL/CentOS 8

The following command adds the nighlty builds package repository:
```bash
sudo yum copr enable gem/openquake
```

### RHEL/CentOS 7

The following command adds the nighlty builds package repository:
```bash
curl -sL https://copr.fedoraproject.org/coprs/gem/openquake/repo/epel-7/gem-openquake-epel-7.repo | sudo tee /etc/yum.repos.d/gem-openquake-epel-7.repo
```

## Install packages from the OpenQuake nighlty repository

Then to install the OpenQuake Engine and its libraries first remove stable packages and then install nightly build packages

```bash
sudo yum erase python3-oq-engine
sudo yum install python3-oq-engine
```

The software and its libraries will be installed under `/opt/openquake`. Data will be stored under `/var/lib/openquake`.

Now you can follow the [standard installing procedures](./rhel.md#configure-the-system-services)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
