# Installing the OpenQuake Engine nightly builds on Fedora

<a href="https://copr.fedorainfracloud.org/coprs/gem/openquake/package/python3-oq-engine/"><img src="https://copr.fedorainfracloud.org/coprs/gem/openquake/package/python3-oq-engine/status_image/last_build.png" /></a>

The OpenQuake Engine is available in the form of *rpm* binary packages for [Fedora](http://getfedora.org/).

For RHEL/CentOS please check ["Installing the OpenQuake Engine on RHEL/CentOS"](fedora-nightly.md).

## Install packages from the OpenQuake repository

The following command adds the nightly builds package repository:
```bash
sudo dnf copr enable gem/openquake
```

Then to install the OpenQuake Engine and its libraries first remove stable packages and then install nightly build packages

```bash
sudo dnf erase python3-oq-engine
sudo dnf install python3-oq-engine
```

The software and its libraries will be installed under `/opt/openquake`. Data will be stored under `/var/lib/openquake`.

Now you can follow the [standard installing procedures](./fedora.md#configure-the-system-services)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
