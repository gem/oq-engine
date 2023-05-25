# FAQ

### Help! There is an error in my calculation!

You are in the wrong place. These are the FAQ for IT issues, concerning
how to install the engine. If you have already installed it and have
issues running calculations you should go [here for hazard calculations](
faq-hazard.md) and [here for risk calculations](faq-risk.md).

******

### Help! What is the recommended hardware to run engine calculations?

It depends on your use case and your level of expertise. Most of our users
are scientists with little IT experience and/or little support from their IT
departments. For them we recommend to buy a very powerful server and not
a cluster, which is complex to manage. A server with 256 GB of RAM
and 64 real cores is currently powerful enough to run all of the calculations
in the GEM global hazard and risk mosaic. If you have larger calculations
and IT expertise, for a cluster setup see the [hardware suggestions](hardware-suggestions.md) and [cluster](installing/cluster.md) pages.

### Help! I have a multi-node cluster and I'm in trouble

If you are running the OpenQuake Engine on a multi-node cluster you should also
have a look at [FAQ related to cluster deployments](faq-cluster.md).

### Help! Should I disable hyperthreading?

Disabling hyperthreading is recommended since it will save
memory. Suppose for instance that you have a laptop with a powerful i9
processor and 16 GB of RAM. It seems a lot. In reality it is not.  The
operating system will consume some memory, the browser will consume a
lot of memory, you may have other applications open and you may end up
with less than 10 GB of available memory. If hyperthreading is enabled
the engine will see 10x2 = 20 cores; running parallel computations may
easily consume 0.5 GB per core, i.e. 10 GB, so you will run out of
memory. With hyperthreading disabled you will still have 5 GB of
available RAM.

Note: on a linux machine you can try disable hyperthreading
temporarily with the command `sudo echo off > /sys/devices/system/cpu/smt/control`: however, this setting will not survive a reboot. Also, on some
systems this command will not work. If you cannot disable hyperthreading
just make sure that if you have enough memory: we recommend 4 GB per
real core or 2 GB per thread.

### Help! My windows server with 32/64 or more cores hangs!

Some users reported this issue. It is due to a limitation of Python
multiprocessing module on Windows. In all cases we have seen, the
problem was solved by disabling hyperthreading. Otherwise you can
reduce the number of used cores by setting the parameter `num_cores`
in the file openquake.cfg as explained below.

### Help! I want to limit the number of cores used by the engine

This is another way to save memory. If you are on a single machine,
the way to do it is to edit the file openquake.cfg and add the lines
(if for instance you want to use 8 cores)
```
[distribution]
num_cores = 8
```
If you are on a cluster you must edit the section [zworkers] and the parameter
`host_cores`, replacing the `-1` with the number of cores to be used on
each machine.

### Help! I am running out of memory!

If you are on a laptop, the first thing to do is close all memory consuming
applications. Remember that running the enigne from the command-line is the
most memory-efficient way to run calculations (browesers can use significant 
memory from your laptop).
You can also limit the number of parallel threads as explained
before (i.e. disable hyperthreading, reduce num_cores) or disable
parallelism altogether by giving the command

```
$ oq engine --run job.ini --no-distribute
```

or by setting `concurrent_tasks = 0` in the job.ini file.
If you still run out of memory, then you must reduce your calculation or
upgrade your system.

### Help! Is it possible to configure multiple installations of the engine to run independently on the same computer?

Yes, it is possible, as long as their virtual environments are stored in
different directories and the ports used by their dbservers are different.

When you install the engine using the `install.py` script,
you may specify the `--venv` parameter to choose in which directory the engine
virtual environment must to be stored. On an existing installation of the engine,
you can run the command

```
$ oq info venv
```

to retrieve the path of its virtual environment.

Another parameter accepted by the `install.py` script is `--dbport`, that
specifies the port number used by the engine dbserver. By default, the port is
set to 1907 for server installations or 1908 for user installations. The port
can be customized through the attribute `port` of section `[dbserver]` in the
configuration file `openquake.cfg`, placed inside the virtual environment
directory, e.g.:

```
[dbserver]
    port = 1907
```

#### Can two installations of the engine share the same `oqdata` directory?

The `oqdata` directory, that stores calculation data, can safely be shared between
two different instances of the engine working on a same computer. Each datastore
is independent from all others and has a unique identifier. It is possible to
determine the version of the engine that produced each datastore (for instance
`calc_X.hdf5`) using the command

```
$ oq show_attrs / X
```

where `/` indicates the root attributes of the datastore (`checksum`, `date`
`engine_version` and `input_size`) and X (an integer number) is the calculation
id. In case the calculation id is not specified, the attributes will be retrieved
for the latest calculation.

******

### Different installation methods

The OpenQuake Engine has several installation methods. To choose the one that best fits your needs take a look at the **[installation overview](installing/README.md)**.

******

### Supported operating systems

Binary packages are provided for the following 64bit operating systems:
- [Windows 10](installing/windows.md)
- [macOS 11.6+](installing/universal.md)
- Linux [Ubuntu 18.04+](installing/ubuntu.md) and [RedHat/CentOS 7/RockyLinux 8 ](installing/rhel.md) via _deb_ and _rpm_
- Any other generic Linux distribution via the [universal installer](installing/universal.md)
- [Docker](installing/docker.md) hosts

A 64bit operating system **is required**. Please refer to each OS specific page for details about requirements.

******

### Unsupported operating systems

- Windows 8 may or may not work and we will not provide support for it
Binary packages *may* work on Ubuntu derivatives and Debian if the dependencies are satisfied; these configurations are known to work:
- Ubuntu 18.04 (Bionic) packages work on **Debian 10.0** (Buster)
- Ubuntu 20.04 (Focal) packages work on **Debian 11.0** (Bullseye)

These configurations however are not tested and we cannot guarantee on the quality of the results. Use at your own risk.

******

### 32bit support

The OpenQuake Engine **requires a 64bit operating system**. Starting with version 2.3 of the Engine binary installers and packages aren't provided for 32bit operating systems anymore.

******

### MPI support

MPI is not supported by the OpenQuake Engine. Task distribution across network interconnected nodes is done via *zmq*. The worker nodes must have read access to a shared file system writeable from the master node. Data transfer is made on TCP/IP connection.

MPI support may be added in the future if sponsored by someone. If you would like to help support development of OpenQuake, please contact us at [partnership@globalquakemodel.org](mailto:partnership@globalquakemodel.org).

******

### Python 2.7 compatibility 

Support for Python 2.7 has been dropped. The last version of the Engine compatible with Python 2.7 is **[OpenQuake Engine version 2.9 (Jeffreys)](https://github.com/gem/oq-engine/tree/engine-2.9#openquake-engine)**.

******

### Python scripts that import openquake

On **Ubuntu** and **RHEL** if a third party python script (or a Jupyter notebook) needs to import openquake as a library (as an example: `from openquake.commonlib import readinput`) you must use a virtual environment and install a local copy of the Engine:

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

The default port for the DbServer (configured via the `openquake.cfg`
configuration file) is `1908` (for a development installation) or `1907`
(for a package installation).

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

### Certificate verification on macOS

```python
Traceback (most recent call last):
  File "/Users/openquake/py36/bin/oq", line 11, in <module>
    load_entry_point('openquake.engine', 'console_scripts', 'oq')()
  File "/Users/openquake/openquake/oq-engine/openquake/commands/__main__.py", line 53, in oq
    parser.callfunc()
  File "/Users/openquake/openquake/oq-engine/openquake/baselib/sap.py", line 181, in callfunc
    return self.func(**vars(namespace))
  File "/Users/openquake/openquake/oq-engine/openquake/baselib/sap.py", line 251, in main
    return func(**kw)
  File "/Users/openquake/openquake/oq-engine/openquake/commands/engine.py", line 210, in engine
    exports, hazard_calculation_id=hc_id)
  File "/Users/openquake/openquake/oq-engine/openquake/commands/engine.py", line 70, in run_job
    eng.run_calc(job_id, oqparam, exports, **kw)
  File "/Users/openquake/openquake/oq-engine/openquake/engine/engine.py", line 341, in run_calc
    close=False, **kw)
  File "/Users/openquake/openquake/oq-engine/openquake/calculators/base.py", line 192, in run
    self.pre_execute()
  File "/Users/openquake/openquake/oq-engine/openquake/calculators/scenario_damage.py", line 85, in pre_execute
    super().pre_execute()
  File "/Users/openquake/openquake/oq-engine/openquake/calculators/base.py", line 465, in pre_execute
    self.read_inputs()
  File "/Users/openquake/openquake/oq-engine/openquake/calculators/base.py", line 398, in read_inputs
    self._read_risk_data()
  File "/Users/openquake/openquake/oq-engine/openquake/calculators/base.py", line 655, in _read_risk_data
    haz_sitecol, assetcol)
  File "/Users/openquake/openquake/oq-engine/openquake/calculators/base.py", line 821, in read_shakemap
    oq.discard_assets)
  File "/Users/openquake/openquake/oq-engine/openquake/hazardlib/shakemap.py", line 100, in get_sitecol_shakemap
    array = download_array(array_or_id)
  File "/Users/openquake/openquake/oq-engine/openquake/hazardlib/shakemap.py", line 74, in download_array
    contents = json.loads(urlopen(url).read())[
  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/urllib/request.py", line 223, in urlopen
    return opener.open(url, data, timeout)
  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/urllib/request.py", line 526, in open
    response = self._open(req, data)
  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/urllib/request.py", line 544, in _open
    '_open', req)
  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/urllib/request.py", line 504, in _call_chain
    result = func(*args)
  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/urllib/request.py", line 1361, in https_open
    context=self._context, check_hostname=self._check_hostname)
  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/urllib/request.py", line 1320, in do_open
    raise URLError(err)
urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:852)>
```

Please have a look at `/Applications/Python 3.8/ReadMe.rtf` for possible solutions. If unsure run from a terminal the following command:

```bash
sudo /Applications/Python\ 3.8/install_certificates.command  # NB: use the appropriate Python version!
```

******


## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
