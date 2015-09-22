## How-to install LXC and OpenQuake LXC on RHEL/CentOS 6
As root user:

### 1) Add the EPEL repo to your RHEL/CentOS 6 server
```bash
$ rpm -ivh http://mirror.nl.leaseweb.net/epel/6/i386/epel-release-6-8.noarch.rpm
```
### 2) Install LXC 1.0.7 from epel and some other stuff needed
```bash
$ yum install lxc lxc-libs lxc-templates bridge-utils libcgroup
```
### 3) Enable the cgroups
```bash
$ service cgconfig start
$ service cgred start
$ chkconfig --level 345 cgconfig on
$ chkconfig --level 345 cgred on
```
### 4) Setup the network:
the easiest way is to create an internal network, so you do not need to expose the LXC to the bare-metal server network.

#### a) Create the bridge

```bash
$ brctl addbr lxcbr0
```

#### b) Make the bridge persistent on reboot

create ```/etc/sysconfig/network-scripts/ifcfg-lxcbr0``` and add
```
DEVICE="lxcbr0"
TYPE="Bridge"
BOOTPROTO="static"
IPADDR="10.0.3.1"
NETMASK="255.255.255.0"
```

#### c) Start the bridge interface
```bash
$ ifup lxcbr0
```

### 5) Configure the firewall

to allow outgoing traffic from the container: edit ```/etc/sysconfig/iptables``` and

#### a) Comment or remove

```
-A FORWARD -j REJECT --reject-with icmp-host-prohibited
```

#### b) Add at the end of file

```
*nat
:PREROUTING ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]
-A POSTROUTING -o eth0 -j MASQUERADE
COMMIT
```

#### c) Restart the firewall
```bash
$ service iptables restart
```

### 6) Enable IPv4 forwarding
edit ```/etc/sysctl.conf``` and change ```net.ipv4.ip_forward = 0``` to ```net.ipv4.ip_forward = 1```, then apply the new parameters with
```bash
$ sysctl –p
```

### 7) Download OpenQuake LXC
```bash
$ cd /tmp && wget http://www.globalquakemodel.org/lxc/Ubuntu_lxc_14.04_64_oq_1.5-0.tar.bz2
```

### 8) Extract the OpenQuake LXC
```bash
$ tar --numeric-owner -C /var/lib/lxc -xpsjf /tmp/Ubuntu_lxc_14.04_64_oq_1.5-0.tar.bz2
```

### 9) Check if the LXC is installed and ready
with the command lxc-ls you should see
```bash
$ lxc-ls
openquake-nightly-141020
```

### 10) Setup the OpenQuake LXC ip address
open ```/var/lib/lxc/openquake/rootfs/etc/network/interfaces``` and change ```iface eth0 inet dhcp``` to
```
iface eth0 inet static
address 10.0.3.2
netmask 255.255.255.0
gateway 10.0.3.1
dns-nameservers 8.8.8.8
```

### 11) Start the OpenQuake LXC
```bash
$ lxc-start –d –n openquake
```

### 12) Login into the running OpenQuake LXC
```bash
$ lxc-console –n openquake
(to detach press ctrl-a + q)
```

You can also login using SSH from the host server:
```bash
$ ssh openquake@10.0.3.2
User: openquake
Password: openquake
```

### Please note:
* This how-to is intended for a fresh, standard installation of RHEL/CentOS 6 (and is tested on 6.4). It may need some adjustments for customized installations.
* On 5. the firewall could be already customized by the sysadmin, please be careful when edit it. For more details please ask to your network and/or system administrator.
* On 5. section b. ```-A POSTROUTING -o eth0 -j MASQUERADE``` "eth0" is the name of the host server main interface. It can differ in your configuration (see the used interface with ifconfig).
* On 8. the ```--numeric-owner``` is mandatory.
* On 10. the ```8.8.8.8``` DNS is the one provided by Google. It’s better to use your internal DNS, so change that IP address with the one associated to your DNS server. For more details please ask to your network and/or system administrator.
* On certain installations the ```rsyslogd``` process inside the container can eat lots of CPU cycles. To fix it run, within the container, these commands (not required on containers prepared by us):
```bash
service rsyslog stop
sed -i -e 's/^\$ModLoad imklog/#\$ModLoad imklog/g' /etc/rsyslog.conf
service rsyslog start
```
