(ubuntu)=

# Installing the OpenQuake Engine on Ubuntu Linux

The OpenQuake Engine stable tree is available in the form of *deb* binary packages for the following Ubuntu releases:
- **Ubuntu 20.04** LTS (Focal)
- **Ubuntu 18.04** LTS (Bionic)

Packages *may* work on Debian,  but this setup is not supported by GEM. See the **[FAQ](unsupported-operating-systems)**.

The software and its libraries will be installed under `/opt/openquake`. Data will be stored under `/var/lib/openquake`.

## Configure the system services {#configure-system-services}

The package installs three system service managed through [systemd](https://www.freedesktop.org/software/systemd/man/systemctl.html):
- `openquake-dbserver`: provides the database for the OpenQuake Engine and must be started before running any `oq engine` command
- `openquake-webui`: provides the WebUI and is optional
`openquake-dbserver` and `openquake-webui` are started by default at boot.

To manually start, stop or restart a service run
```bash
sudo systemctl <start|stop|restart> openquake-dbserver openquake-webui
```

To check the status of a service run
```bash
sudo systemctl status openquake-dbserver openquake-webui
```

## Run the OpenQuake Engine

Continue on [How to run the OpenQuake Engine](unix)

## Test the installation

To run the OpenQuake Engine tests see the **[testing](https://github.com/gem/oq-engine/blob/master/doc/contributing/testing.md)** page.

## Uninstall the OpenQuake Engine

To uninstall the OpenQuake Engine and all its components run
```bash
sudo apt remove python-oq-* python3-oq-*
```
If you want to remove all the dependencies installed by the OpenQuake Engine you may then use the apt `autoremove` function and run

```bash
sudo apt autoremove
```

## Data cleanup

To reset the database `oq reset` command can be used:

```bash
sudo systemctl stop openquake-dbserver
sudo -u openquake oq reset
sudo systemctl start openquake-dbserver
```

To remove **all** the data produced by the OpenQuake Engine (including datastores) you must also remove `~/oqdata` in each users' home. The `reset-db` bash script is provided, as a reference, in `/usr/share/openquake/engine/utils`.

If the packages have been already uninstalled, it's safe to remove `/var/lib/openquake`.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
