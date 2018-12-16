=================
openquake.baselib
=================

`openquake.baselib` is a collection of utilities to run large numeric
simulations. It includes support for parallel computing (via multiprocessing,
celery, zmq or dask), performance monitoring and a serialization library
from Python objects to HDF5 files and viceversa.

Development and support
-----------------------

`openquake.baselib` is being actively developed by GEM foundation as a part of
OpenQuake project. The public repository is available on github:
http://github.com/gem/oq-engine. A mailing list is available as well:
http://groups.google.com/group/openquake-users.

Installation
------------

`openquake.baselib` is currently part of the OpenQuake engine and can be
installed simply with

```
$ pip install openquake.engine
```

or in several other ways, see
https://github.com/gem/oq-engine/blob/master/README.md#installation

License
-------
openquake.baselib is licensed under terms of GNU Affero General Public
License 3.0.

