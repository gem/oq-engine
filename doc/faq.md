# FAQ

### Different installation methods

The OpenQuake Engine has at least three installation methods. To choose the one that best fits your needs take a look at the **[installation overview](installing/overview.md)**.

***

### Unsupported operating systems

Binary packages *may* work on Ubuntu derivatives and Debian if the dependencies are satisfied; these configurations are known to work:
- **Ubuntu 14.04** (Trusty) packages work on **Mint Linux 17** and on **Debian 8.0** (Jessie)
- **Ubuntu 16.04** (Trusty) packages work on **Mint Linux 18** and on **Debian unstable**

These configurations however are not tested by our [continuous integration system](https://ci.openquake.org) and we cannot guarantee on the quality of the results. Use at your own risk.

Another installation option for unsupported Linux systems is provided by the **[self-installable binary distribution for generic Linux](installing/linux-generic.md)**.

***

### Celery support

In the OpenQuake Engine 2.1 Celery isn't needed (and not recommended) on a single machine setup; the OpenQuake Engine is able to use all the available CPU cores even without Celery.
Celery must be enabled on a cluster / multi node setup. To enable it please refer to the [multiple nodes installation guidelines](installing/cluster.md).

***

### MPI support

MPI is not supported by the OpenQuake Engine. Task distribution across network interconnected nodes is made via *Celery* and *RabbitMQ* as broker. No filesystem sharing is needed between the nodes and data transfer is made on plain TCP/IP connection. For a cluster setup see the [hardware suggestions](hardware-suggestions.md) and [cluster](installing/cluster.md) pages.

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
