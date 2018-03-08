# FAQ

### Different installation methods

The OpenQuake Engine has at least three installation methods. To choose the one that best fits your needs take a look at the **[installation overview](installing/overview.md)**.

***

### Supported operating systems

Binary packages are provided for the following 64bit operating systems:
- [Windows](installing/windows.md)
- [macOS](installing/macos.md)
- Linux [Ubuntu](installing/ubuntu.md) and [RedHat/CentOS/Scientific Linux/Fedora](installing/rhel.md) via _deb_ and _rpm_
- Any other generic Linux distribution via a [self-installable binary distribution](installing/linux-generic.md)
- [Docker](installing/docker.md) hosts

A 64bit operating system **is required**. Please refer to each OS specific page for details about requirements.

***

### Unsupported operating systems

Binary packages *may* work on Ubuntu derivatives and Debian if the dependencies are satisfied; these configurations are known to work:
- **Ubuntu 14.04** (Trusty) packages work on **Mint Linux 17** and on **Debian 8.0** (Jessie)
- **Ubuntu 16.04** (Xenial) packages work on **Mint Linux 18** and on **Debian 9.0** (Stretch)

These configurations however are not tested by our [continuous integration system](https://ci.openquake.org) and we cannot guarantee on the quality of the results. Use at your own risk.

Another installation option for unsupported Linux systems is provided by the **[self-installable binary distribution for generic Linux](installing/linux-generic.md)**.

***

### 32bit support

The OpenQuake Engine **requires a 64bit operating system**; 32bit systems are not officially supported and untested. Staring with version 2.3 of the Engine binary installers and packages aren't provided for 32bit operating systems anymore.

***

### Celery support

Starting with OpenQuake Engine 2.0 Celery isn't needed (and not recommended) on a single machine setup; the OpenQuake Engine is able to use all the available CPU cores even without Celery.
Celery must be enabled on a cluster / multi node setup. To enable it please refer to the [multiple nodes installation guidelines](installing/cluster.md).

***

### MPI support

MPI is not supported by the OpenQuake Engine. Task distribution across network interconnected nodes is made via *Celery* and *RabbitMQ* as broker. No filesystem sharing is needed between the nodes and data transfer is made on plain TCP/IP connection. For a cluster setup see the [hardware suggestions](hardware-suggestions.md) and [cluster](installing/cluster.md) pages.

MPI support may be added in the future if sponsored by someone. If you would like to help support development of OpenQuake, please contact us at [partnership@globalquakemodel.org](mailto:partnership@globalquakemodel.org).

***

### Python scripts that import openquake

On **Ubuntu** and **RHEL** if a third party python script (or a Jupyter notebook) needs to import openquake as a library (as an example: `from openquake.commonlib import readinput`) you must use a virtual environment and install al local copy of the Engine:

```
$ python3 -m venv </path/to/myvenv>
$ . /path/to/myvenv/bin/activate
$ pip3 install openquake.engine
```

***

### OpenQuake Hazardlib errors
```bash
pkg_resources.DistributionNotFound: The 'openquake.hazardlib==0.XY' distribution was not found and is required by openquake.engine
```
Since OpenQuake Engine 2.5, the OpenQuake Hazardlib package has been merged with the OpenQuake Engine one.

If you are using git and you have the `PYTHONPATH` set you should update `oq-engine` and then remove `oq-hazardlib` from your filesystem and from the `PYTHONPATH`, to avoid any possible confusion.

If `oq-hazardlib` has been installed via `pip` you must uninstall both `openquake.engine` and `openquake.hazardlib` first, and then reinstall `oq-engine`.

```bash
$ pip uninstall openquake.hazardlib openquake.engine
$ pip install openquake.engine
# -OR- development installation
$ pip install -e /path/to/oq-engine/
```

If you are using Ubuntu or RedHat packages no extra operations are needed, the package manager will remove the old `python-oq-hazardlib` package and replace it with a fresh copy of `python3-oq-engine`.

On Ubuntu make sure to run `apt dist-upgrade` instead on `apt upgrade` to make a proper upgrade of the OpenQuake packages.

***

### error: [Errno 111] Connection refused

A more detailed stack trace:

```Python
File "/usr/local/lib/python2.6/dist-packages/carrot/connection.py", line 135, in connection
    self._connection = self._establish_connection()
File "/usr/local/lib/python2.6/dist-packages/carrot/connection.py", line 148, in _establish_connection
    return self.create_backend().establish_connection()
File "/usr/local/lib/python2.6/dist-packages/carrot/backends/pyamqplib.py", line 208, in establish_connection
    connect_timeout=conninfo.connect_timeout)
File "/usr/local/lib/python2.6/dist-packages/amqplib/client_0_8/connection.py", line 125, in __init__
    self.transport = create_transport(host, connect_timeout, ssl)
File "/usr/local/lib/python2.6/dist-packages/amqplib/client_0_8/transport.py", line 220, in create_transport
    return TCPTransport(host, connect_timeout)
File "/usr/local/lib/python2.6/dist-packages/amqplib/client_0_8/transport.py", line 58, in __init__
    self.sock.connect((host, port))
File "", line 1, in connect
error: [Errno 111] Connection refused
```

This happens when the **Celery support is enabled but RabbitMQ server is not running**. You can start it running
```bash
$ sudo service rabbitmq-server start
``` 

***

### error: [Errno 104] Connection reset by peer

A more detailed stack trace:

```python
Traceback (most recent call last):
  File "/usr/lib/python2.7/dist-packages/celery/worker/__init__.py", line 206, in start
    self.blueprint.start(self)
  File "/usr/lib/python2.7/dist-packages/celery/bootsteps.py", line 119, in start
    self.on_start()
  File "/usr/lib/python2.7/dist-packages/celery/apps/worker.py", line 165, in on_start
    self.purge_messages()
  File "/usr/lib/python2.7/dist-packages/celery/apps/worker.py", line 189, in purge_messages
    count = self.app.control.purge()
  File "/usr/lib/python2.7/dist-packages/celery/app/control.py", line 145, in purge
    return self.app.amqp.TaskConsumer(conn).purge()
  File "/usr/lib/python2.7/dist-packages/celery/app/amqp.py", line 375, in __init__
    **kw
  File "/usr/lib/python2.7/dist-packages/kombu/messaging.py", line 364, in __init__
    self.revive(self.channel)
  File "/usr/lib/python2.7/dist-packages/kombu/messaging.py", line 369, in revive
    channel = self.channel = maybe_channel(channel)
  File "/usr/lib/python2.7/dist-packages/kombu/connection.py", line 1054, in maybe_channel
    return channel.default_channel
  File "/usr/lib/python2.7/dist-packages/kombu/connection.py", line 756, in default_channel
    self.connection
  File "/usr/lib/python2.7/dist-packages/kombu/connection.py", line 741, in connection
    self._connection = self._establish_connection()
  File "/usr/lib/python2.7/dist-packages/kombu/connection.py", line 696, in _establish_connection
    conn = self.transport.establish_connection()
  File "/usr/lib/python2.7/dist-packages/kombu/transport/pyamqp.py", line 116, in establish_connection
    conn = self.Connection(**opts)
  File "/usr/lib/python2.7/dist-packages/amqp/connection.py", line 180, in __init__
    (10, 30),  # tune
  File "/usr/lib/python2.7/dist-packages/amqp/abstract_channel.py", line 67, in wait
    self.channel_id, allowed_methods, timeout)
  File "/usr/lib/python2.7/dist-packages/amqp/connection.py", line 241, in _wait_method
    channel, method_sig, args, content = read_timeout(timeout)
  File "/usr/lib/python2.7/dist-packages/amqp/connection.py", line 330, in read_timeout
    return self.method_reader.read_method()
  File "/usr/lib/python2.7/dist-packages/amqp/method_framing.py", line 189, in read_method
    raise m
error: [Errno 104] Connection reset by peer
```

This means that RabbiMQ _user_ and _vhost_ have not been created or set correctly. Please refer to [cluster documentation](installing/cluster.md#rabbitmq) to fix it.

***

### Swap partitions

Having a swap partition active on resources fully dedicated to the OpenQuake Engine is discouraged. More info [here](installing/cluster.md#swap-partitions).

***

### System running out of disk space

The OpenQuake Engine may require lot of disk space for the raw results data (`hdf5` files stored in `/home/<user>/oqdata`) and the temporary files used to either generated outputs or load input files via the `API`. On certain cloud configurations the amount of space allocated to the root fs (`/`) is fairly limited and extra 'data' volumes needs to be attached. To make the Engine use these volumes for `oqdata` and the _temporary_ storage you must change the `openquake.cfg` configuration; assuming `/mnt/ext_volume` as the mount point of the extra 'data' volume, it must be changed as follow:

- `shared_dir` must be set to `/mnt/ext_volume`
- A `tmp` dir must be created in `/mnt/ext_volume`
- `custom_tmp` must be set to `/mnt/ext_volume/tmp` (the directory must exist)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
