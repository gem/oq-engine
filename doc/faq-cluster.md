# FAQ related to cluster deployments

### What it is the proper way to install the engine on a supercomputer cluster?

Normally a supercomputer cluster cannot be fully assigned to the OpenQuake engine, so you cannot
perform the [regular cluster installation](installing/cluster.md). We suggest to do the following instead:

- install the engine in server mode on the machine that will host the database and
  set `shared_dir=/opt/openquake` in the openquake.cfg file; such machine can have low specs; optionally,
  you can run the WebUI there, so that the users can easily download the results
- expose /opt/openquake to all the machines in the cluster by using a read-write shared filesystem
- then run the calculations on the other cluster nodes; the outputs will be saved in /opt/openquake/oqdata and
  the code will be read from /opt/openquake/venv; this will work if all the nodes have a vanilla python
  installation consistent with the one on the database machine.

### Recover after a Out Of Memory (OOM) condition

When an _Out Of Memory (OOM)_ condition occours on the master node the `oq` process is terminated by the operating system _OOM killer_ via a `SIGKILL` signal.

Due to the forcefully termination of `oq`, processes may be left running, using resources (both CPU and RAM), until the task execution reaches an end.

To free up resources for a new run **you must kill all openquake processes on the workers nodes**; this will stop any other running computation which is anyway highly probable to be already broken due to the OOM condition on the master node.

### error: OSError: Unable to open file

A more detailed stack trace:

```python
OSError:
  File "/opt/openquake/lib/python3.8/site-packages/openquake/baselib/parallel.py", line 312, in new
    val = func(*args)
  File "/opt/openquake/lib/python3.8/site-packages/openquake/baselib/parallel.py", line 376, in gfunc
    yield func(*args)
  File "/opt/openquake/lib/python3.8/site-packages/openquake/calculators/classical.py", line 301, in build_hazard_stats
    pgetter.init()  # if not already initialized
  File "/opt/openquake/lib/python3.8/site-packages/openquake/calculators/getters.py", line 69, in init
    self.dstore = hdf5.File(self.dstore, 'r')
  File "/opt/openquake/lib64/python3.8/site-packages/h5py/_hl/files.py", line 312, in __init__
    fid = make_fid(name, mode, userblock_size, fapl, swmr=swmr)
  File "/opt/openquake/lib64/python3.8/site-packages/h5py/_hl/files.py", line 142, in make_fid
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

## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
