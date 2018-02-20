## Technology Stack

### Main dependencies
 
* Python - Implementation language
* concurrent.futures - Standard package for concurrence in Python
* Django - Used by the API server and the WebUI
* HDF5 - Used for storing and managing data
* numpy and scipy - Fundamental packages for scientific computing with Python
* pyzmq - Used for internal inter-process communications

### Optional dependencies

* Rtree - a wrapper of libspatialindex that provides a number of advanced spatial indexing features 
* Celery - Distributed task queue library, using the `iterator_native()`
* RabbitMQ - Message broker for Celery tasks, logging channels, and other signalling

### Python dependencies

Python 2.7, Python 3.5 or Python 3.6.

See [setup.py](../setup.py) for a complete list of the Python dependencies.

### Binary dependencies

Software  | Version(s)
--------- | ----------
RabbitMQ | 2.6 to 3.2
libgeos | >= 3.2.2
HDF5 | 1.8

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
