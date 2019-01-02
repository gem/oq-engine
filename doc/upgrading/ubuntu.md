# Upgrading the OpenQuake Engine on Ubuntu Linux

To upgrade the OpenQuake Engine and its libraries run

```bash
sudo apt update
sudo apt install python3-oq-engine
```

If a full upgrade is performed on the system, the OpenQuake software is upgraded to the latest version too:

```bash
sudo apt update
sudo apt upgrade
```

### Coming from nightly builds
If you were previously using a nightly release first remove the old packages and the repository:

```bash
sudo apt remove --purge python-oq.* python3-oq.*
sudo add-apt-repository -r -y ppa:openquake-automatic-team/latest-master
sudo add-apt-repository -y ppa:openquake/ppa
sudo apt update
```

### Coming from OpenQuake Engine 1.x

If you are upgrading from OpenQuake Engine release 1.x, before you can proceed you have to run this command:
```bash
sudo apt remove --purge python-oq.*
sudo rm -Rf /usr/openquake
```

The following dependencies are not used anymore by the OpenQuake Engine 2:
- redis-server (used only by the OQ Engine 1.0)
- postgresql-server and postgis
- other minor dependencies

They can be removed, if not used by any other software installed on your machine, by running

```bash
sudo apt autoremove
```

If you want to remove also the data hosted by PostgreSQL, by default located in `/var/lib/postgresql`, you can add the `--purge` flag to the `autoremove` command

```bash
sudo apt autoremove --purge
```

BE AWARE that this command will delete all the data hosted by PostgreSQL (including all the databases not created by the OpenQuake Engine) and cannot be undone. If unsure, please make a backup first.


## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
