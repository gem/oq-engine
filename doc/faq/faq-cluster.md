# FAQ related to cluster deployments

For general questions see [FAQ](faq.md)

### Recover after a Out Of Memory (OOM) condition

When an _Out Of Memory (OOM)_ condition occours on the master node the `oq` process is terminated by the operating system _OOM killer_ via a `SIGKILL` signal.

Due to the forcefully termination of `oq`, _celery_ tasks are not revoked on the worker nodes and processes may be left running, using resources (both CPU and RAM), until the task execution reaches an end.

To free up resources for a new run and to cleanup the cluster status **you must restart _celery_ in the workers nodes** via `systemctl restart openquake-celery` before starting any new job execution; this will stop any other running computation which is anyway highly probable to be already broken due to the OOM condition on the master node.

******

### error: OSError: Unable to open file

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

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
