### Unsupported operating systems

Binary packages *may* work on Ubuntu derivates and Debian if the dependencies are satsfied; these configurations are known to work:
- **Ubuntu 14.04** (Trusty) packages work on **Mint Linux 17** and on **Debian 8.0** (Jessie)
- **Ubuntu 16.04** (Trusty) packages work on **Mint Linux 18** and on **Debian unstable**

These configurations however are not tested by our [countinuos integration system](https://ci.openquake.org) and we cannot guarantee on the quality of the results. Use at your own risk.

***

### Celery support

In the OpenQuake Engine 2.0 Celery isn't needed (and not recommended) on a single machine setup; the OpenQuake Engine is able to use all the available CPU cores even without Celery.
Celery must be enabled on a cluster / multi node setup. To enable it please refer to the multiple nodes installation guidelines for [Ubuntu](FIXME)
or [RedHat/CentOS/SL](FIXME).

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
