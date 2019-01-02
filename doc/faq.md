# FAQ

### Help! There is an error in my calculation!

You are in the wrong place. These are the FAQ for IT issues, concerning
how to install the engine. If you have already installed it and have
issues running calculations you should go [here for hazard calculations](
faq-hazard.md) and [here for risk calculations](faq-risk.md).

******

### Python 2.7 compatibility 

Support for Python 2.7 has been dropped. The last version of the Engine compatible with Python 2.7 is **[OpenQuake Engine version 2.9 (Jeffreys)](https://github.com/gem/oq-engine/tree/engine-2.9#openquake-engine)**.

******

### Different installation methods

The OpenQuake Engine has at least three installation methods. To choose the one that best fits your needs take a look at the **[installation overview](installing/overview.md)**.

******

### Supported operating systems

Binary packages are provided for the following 64bit operating systems:
- [Windows](installing/windows.md)
- [macOS](installing/macos.md)
- Linux [Ubuntu](installing/ubuntu.md) and [RedHat/CentOS/Scientific Linux/Fedora](installing/rhel.md) via _deb_ and _rpm_
- Any other generic Linux distribution via a [self-installable binary distribution](installing/linux-generic.md)
- [Docker](installing/docker.md) hosts

A 64bit operating system **is required**. Please refer to each OS specific page for details about requirements.

******

### Unsupported operating systems

Binary packages *may* work on Ubuntu derivatives and Debian if the dependencies are satisfied; these configurations are known to work:
- Ubuntu 16.04 (Xenial) packages work on **Mint Linux 18** and on **Debian 9.0** (Stretch)
- Ubuntu 18.04 (Bionic) packages work on **Mint Linux 19** and on **Debian 10.0** (Buster)

These configurations however are not tested by our [continuous integration system](https://ci.openquake.org) and we cannot guarantee on the quality of the results. Use at your own risk.

Another installation option for unsupported Linux systems is provided by the **[self-installable binary distribution for generic Linux](installing/linux-generic.md)**.

******

### 32bit support

The OpenQuake Engine **requires a 64bit operating system**; 32bit systems are not officially supported and untested. Starting with version 2.3 of the Engine binary installers and packages aren't provided for 32bit operating systems anymore.

******

### Celery support

Starting with OpenQuake Engine 2.0 Celery isn't needed (and not recommended) on a single machine setup; the OpenQuake Engine is able to use all the available CPU cores even without Celery.
Celery must be enabled on a cluster / multi-node setup. To enable it please refer to the [multiple nodes installation guidelines](installing/cluster.md).

******

### MPI support

MPI is not supported by the OpenQuake Engine. Task distribution across network interconnected nodes is made via *Celery* and *RabbitMQ* as broker. No filesystem sharing is needed between the nodes and data transfer is made on plain TCP/IP connection. For a cluster setup see the [hardware suggestions](hardware-suggestions.md) and [cluster](installing/cluster.md) pages.

MPI support may be added in the future if sponsored by someone. If you would like to help support development of OpenQuake, please contact us at [partnership@globalquakemodel.org](mailto:partnership@globalquakemodel.org).

******

### Python scripts that import openquake

On **Ubuntu** and **RHEL** if a third party python script (or a Jupyter notebook) needs to import openquake as a library (as an example: `from openquake.commonlib import readinput`) you must use a virtual environment and install al local copy of the Engine:

```
$ python3 -m venv </path/to/myvenv>
$ . /path/to/myvenv/bin/activate
$ pip3 install openquake.engine
```

******

### Errors upgrading from an old version on Ubuntu

When upgrading from an OpenQuake version **older than 2.9 to a newer one** you may encounter an error on **Ubuntu**. Using `apt` to perform the upgrade you may get an error like this:

```bash
Unpacking oq-python3.5 (3.5.3-1ubuntu0~gem03~xenial01) ...
dpkg: error processing archive /var/cache/apt/archives/oq-python3.5_3.5.3-1ubuntu0~gem03~xenial01_amd64.deb (--unpack):
 trying to overwrite '/opt/openquake/bin/easy_install', which is also in package python-oq-libs 1.3.0~dev1496296871+a6bdffb
```

This issue can be resolved uninstalling OpenQuake first and then making a fresh installation of the latest version:

```bash
$ sudo apt remove python-oq-.*
$ sudo rm -Rf /opt/openquake
$ sudo apt install python3-oq-engine
```

******

### OpenQuake Hazardlib errors

```bash
pkg_resources.DistributionNotFound: The 'openquake.hazardlib==0.XY' distribution was not found and is required by openquake.engine
```
Since OpenQuake Engine 2.5, the OpenQuake Hazardlib package has been merged with the OpenQuake Engine one.

If you are using git and you have the `PYTHONPATH` set you should update `oq-engine` and then remove `oq-hazardlib` from your filesystem and from the `PYTHONPATH`, to avoid any possible confusion.

If `oq-hazardlib` has been installed via `pip` you must uninstall both `openquake.engine` and `openquake.hazardlib` first, and then reinstall `openquake.engine`.

```bash
$ pip uninstall openquake.hazardlib openquake.engine
$ pip install openquake.engine
# -OR- development installation
$ pip install -e /path/to/oq-engine/
```

If you are using Ubuntu or RedHat packages no extra operations are needed, the package manager will remove the old `python-oq-hazardlib` package and replace it with a fresh copy of `python3-oq-engine`.

On Ubuntu make sure to run `apt dist-upgrade` instead on `apt upgrade` to make a proper upgrade of the OpenQuake packages.

******

### 'The openquake master lost its controlling terminal' error

When the OpenQuake Engine is driven via the `oq` command over an SSH connection an associated terminal must exist throughout the `oq` calculation lifecycle.
The `openquake.engine.engine.MasterKilled: The openquake master lost its controlling terminal` error usually means that the SSH connection
has dropped or the controlling terminal has been closed having a running computation attached to it.

To avoid this error please use `nohup`, `screen`, `tmux` or `byobu` when using `oq` via SSH.
More information is available on [Running the OpenQuake Engine](running/unix.md).

******

### DbServer ports

The default port for the DbServer (configured via the `openquake.cfg` configuration file) is `1908` or `1907`.

******

### error: OSError: Unable to open file (on a multi-node cluster)

A more detailed stack trace:

```python
OSError:
  File "/opt/openquake/lib/python3.6/site-packages/openquake/baselib/parallel.py", line 312, in new
    val = func(*args)
  File "/opt/openquake/lib/python3.6/site-packages/openquake/baselib/parallel.py", line 376, in gfunc
    yield func(*args)
  File "/opt/openquake/lib/python3.6/site-packages/openquake/calculators/classical.py", line 301, in build_hazard_stats
    pgetter.init()  # if not already initialized
  File "/opt/openquake/lib/python3.6/site-packages/openquake/calculators/getters.py", line 69, in init
    self.dstore = hdf5.File(self.dstore, 'r')
  File "/opt/openquake/lib64/python3.6/site-packages/h5py/_hl/files.py", line 312, in __init__
    fid = make_fid(name, mode, userblock_size, fapl, swmr=swmr)
  File "/opt/openquake/lib64/python3.6/site-packages/h5py/_hl/files.py", line 142, in make_fid
    fid = h5f.open(name, flags, fapl=fapl)
  File "h5py/_objects.pyx", line 54, in h5py._objects.with_phil.wrapper
  File "h5py/_objects.pyx", line 55, in h5py._objects.with_phil.wrapper
  File "h5py/h5f.pyx", line 78, in h5py.h5f.open
OSError: Unable to open file (unable to open file: name = '/home/openquake/oqdata/cache_1.hdf5', errno = 2, error message = 'No such file or directory', flags = 0, o_flags = 0)
```

This happens when the [shared dir](installing/cluster.md#shared_filesystem) is not configured properly and workers cannot access data from the master node.
Please note that starting with OpenQuake Engine 3.3 the shared directory **is required** on multi-node deployments.

You can get more information about setting up the shared directory on the [cluster installation page](installing/cluster.md#shared_filesystem).

******

### error: [Errno 111] Connection refused

A more detailed stack trace:

```python
Traceback (most recent call last):
  File "/opt/openquake/lib/python3.6/site-packages/kombu/utils/functional.py", line 333, in retry_over_time
    return fun(*args, **kwargs)
  File "/opt/openquake/lib/python3.6/site-packages/kombu/connection.py", line 261, in connect
    return self.connection
  File "/opt/openquake/lib/python3.6/site-packages/kombu/connection.py", line 802, in connection
    self._connection = self._establish_connection()
  File "/opt/openquake/lib/python3.6/site-packages/kombu/connection.py", line 757, in _establish_connection
    conn = self.transport.establish_connection()
  File "/opt/openquake/lib/python3.6/site-packages/kombu/transport/pyamqp.py", line 130, in establish_connection
    conn.connect()
  File "/opt/openquake/lib/python3.6/site-packages/amqp/connection.py", line 282, in connect
    self.transport.connect()
  File "/opt/openquake/lib/python3.6/site-packages/amqp/transport.py", line 109, in connect
    self._connect(self.host, self.port, self.connect_timeout)
  File "/opt/openquake/lib/python3.6/site-packages/amqp/transport.py", line 150, in _connect
    self.sock.connect(sa)
ConnectionRefusedError: [Errno 111] Connection refused
```

This happens when the **Celery support is enabled but RabbitMQ server is not running**. You can start it running
```bash
$ sudo service rabbitmq-server start
``` 

It may also mean that an incompatible version of Celery is used. Please check it with `/opt/openquake/bin/pip3 freeze`.

******

### error: [Errno 104] Connection reset by peer _or_ (403) ACCESS_REFUSED

More detailed stack traces:


```python
Traceback (most recent call last):
  [...]
  File "/opt/openquake/lib/python3.6/dist-packages/amqp/connection.py", line 180, in __init__
    (10, 30),  # tune
  File "/opt/openquake/lib/python3.6/dist-packages/amqp/abstract_channel.py", line 67, in wait
    self.channel_id, allowed_methods, timeout)
  File "/opt/openquake/lib/python3.6/dist-packages/amqp/connection.py", line 241, in _wait_method
    channel, method_sig, args, content = read_timeout(timeout)
  File "/opt/openquake/lib/python3.6/dist-packages/amqp/connection.py", line 330, in read_timeout
    return self.method_reader.read_method()
  File "/opt/openquake/lib/python3.6/dist-packages/amqp/method_framing.py", line 189, in read_method
    raise m
error: [Errno 104] Connection reset by peer
```

```python
Traceback (most recent call last):
  [...]
  File "/opt/openquake/lib/python3.6/site-packages/amqp/connection.py", line 288, in connect
    self.drain_events(timeout=self.connect_timeout)
  File "/opt/openquake/lib/python3.6/site-packages/amqp/connection.py", line 471, in drain_events
    while not self.blocking_read(timeout):
  File "/opt/openquake/lib/python3.6/site-packages/amqp/connection.py", line 477, in blocking_read
    return self.on_inbound_frame(frame)
  File "/opt/openquake/lib/python3.6/site-packages/amqp/method_framing.py", line 55, in on_frame
    callback(channel, method_sig, buf, None)
  File "/opt/openquake/lib/python3.6/site-packages/amqp/connection.py", line 481, in on_inbound_method
    method_sig, payload, content,
  File "/opt/openquake/lib/python3.6/site-packages/amqp/abstract_channel.py", line 128, in dispatch_method
    listener(*args)
  File "/opt/openquake/lib/python3.6/site-packages/amqp/connection.py", line 603, in _on_close
    (class_id, method_id), ConnectionError)
amqp.exceptions.AccessRefused: (0, 0): (403) ACCESS_REFUSED - Login was refused using authentication mechanism AMQPLAIN. For details see the broker logfile.
```

These errors mean that RabbiMQ _user_ and _vhost_ have not been created or set correctly. Please refer to [cluster documentation](installing/cluster.md#rabbitmq) to fix it.

******

### Swap partitions

Having a swap partition active on resources fully dedicated to the OpenQuake Engine is discouraged. More info [here](installing/cluster.md#swap-partitions).

******

### System running out of disk space

The OpenQuake Engine may require lot of disk space for the raw results data (`hdf5` files stored in `/home/<user>/oqdata`) and the temporary files used to either generated outputs or load input files via the `API`. On certain cloud configurations the amount of space allocated to the root fs (`/`) is fairly limited and extra 'data' volumes needs to be attached. To make the Engine use these volumes for `oqdata` and the _temporary_ storage you must change the `openquake.cfg` configuration; assuming `/mnt/ext_volume` as the mount point of the extra 'data' volume, it must be changed as follow:

- `shared_dir` must be set to `/mnt/ext_volume`
- A `tmp` dir must be created in `/mnt/ext_volume`
- `custom_tmp` must be set to `/mnt/ext_volume/tmp` (the directory must exist)

******

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
