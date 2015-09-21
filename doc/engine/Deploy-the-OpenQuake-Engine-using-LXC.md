### About LXC
>LXC (LinuX Containers) is an operating system–level virtualization method for running multiple isolated Linux systems (containers) on a single control host.

>The Linux kernel comprises cgroups for resource isolation (CPU, memory, block I/O, network, etc.) that does not require starting any virtual machines. Cgroups also provides namespace isolation to completely isolate applications' view of the operating environment, including process trees, network, user ids and mounted file systems.

>LXC combines cgroups and namespace support to provide an isolated environment for applications. Docker can also use LXC as one of its execution drivers, enabling image management and providing deployment services.

From http://en.wikipedia.org/wiki/LXC

**GEM** provides a ready-to-use LXC container with Ubuntu 14.04 and the OpenQuake engine. The LXC is available with OpenQuake installed using Ubuntu packages (for users). If you need to work with GIT sources (for developers and advanced users) see [Deploy-the-OpenQuake-Engine-Nightly-using-LXC.md](Deploy-the-OpenQuake-Engine-Nightly-using-LXC.md).

### Host prerequisites
* Ubuntu >= 12.04 64bit
* Fedora >= 21 64bit
* RHEL/CentOS 7 (using the [EPEL](http://mirror.switch.ch/ftp/mirror/epel/7/x86_64/repoview/epel-release.html) repo)
* [RHEL/CentOS 6](Installing-LXC-on-CentOS.md)
* Should works with other distributions supporting LXC (Debian, ArchLinux, OpenSUSE, Gentoo...)
* sudo
* wget

For RedHat based distros (RHEL, CentOS, Fedora) use ```yum``` instead of ```apt-get```

### Install LXC
```bash
$ sudo apt-get install lxc
```
Download the OpenQuake LXC archive (current released version is [http://www.globalquakemodel.org/lxc/Ubuntu_lxc_14.04_64_oq_1.5-0.tar.bz2])
```bash
$ cd ~ && wget http://www.globalquakemodel.org/lxc/Ubuntu_lxc_14.04_64_oq_1.5-0.tar.bz2
```
### Extract the OpenQuake LXC archive
```bash
$ sudo tar --numeric-owner -C /var/lib/lxc -xpsjf ~/Ubuntu_lxc_14.04_64_oq_1.5-0.tar.bz2
```

### Start the OpenQuake LXC container
```bash
$ sudo lxc-start -n openquake -d
```

### Login into the OpenQuake LXC container
```bash
$ sudo lxc-console -n openquake
```
* user: openquake / password: openquake
* To detach from the container console press ctrl+a then q

### Stop the OpenQuake LXC container
```bash
$ sudo lxc-stop -n openquake
```

### Move or copy files
To move or copy files from the host (your PC) to the OpenQuake LXC container just access it from the host path ```/var/lib/lxc/openquake/rootfs```.
Example:
```bash
$ sudo cp /home/hostuser/job.ini /var/lib/lxc/openquake/rootfs/home/openquake
```

### Update the LXC container and the OpenQuake Engine
```bash
$ sudo apt-get update && sudo apt-get upgrade
```
Be careful: the upgrade will destroy all the data saved in the OpenQuake DB!

### Useful links
* https://help.ubuntu.com/14.04/serverguide/lxc.html
