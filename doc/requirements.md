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

### Binary dependencies

Software  | Version(s)
--------- | ----------
Python | 2.7, 3.5
RabbitMQ | 2.6 to 3.2
libgeos | >= 3.2.2
HDF5 | 1.8


### Python dependencies

See [setup.py](../setup.py) for a complete list of the Python dependencies.
