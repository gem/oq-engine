## Interacting with the datastore

After a calculation has been executed, the results are stored into an HDF5
file called the datastore. You can get the location of the file with
the command `oq show contents`. For instance, if the calculation ID is 42,
you will get something like the following:

```bash
$ oq show contents 42
...
<contents of the datastore>
...
/home/michele/oqdata/calc_42.hdf5 : 262.36 KB
```

The last line contains the location of the datastore and its size.
The datastore can be read from IPython like this:

```python
In [1]: from openquake.baselib.datastore import read
In [2]: dstore = read('/home/michele/oqdata/calc_42.hdf5')
In [3]: dstore
Out[4]: <DataStore 42, open>
```

The datastore object is dictionary-like and it is a thin wrapper
around a `h5py.File` object. You can read it as you would do
with a `h5py.File`, but it has some additional features.
There is no much documentation available yet, but you can
always read the source code and the [automatically generated
documentation](https://docs.openquake.org/oq-engine/master/openquake.baselib.html#module-openquake.baselib.datastore).

If your confortable with Python and with [h5py](
http://docs.h5py.org/en/latest/quick.html#quick) reading the
datastore is by fast the simplest, more convenient and most
efficient way to postprocess and visualize the results of
a calculation. However you should be warned that
**the datastore internals are reserved and subject to change!**

There is an extraction API that is more stable, you should use
it as much as possible. For instance if you want to extract
the realizations output you should do

```python
In [5]: from openquake.calculators.extract import extract
In [6]: extract(dstore, 'realizations')
```

and not `dstore['realizations']` that used to work in the past. The `extract`
function is mantained, so even if the structure of the datastore
changes (for instance recently we removed the `realizations` dataset) it
continues to work.

Having said so, I do no guarantee that the `extract` function will
keep working in the same way forever. The stable API is the
[WebAPI](web-api.md).

Accessing directly the datastore is meant for internal users (i.e. GEM
staff) and for power users that are willing to accept some instability
in order to get the cutting edge features of the engine. It is also
the only way for people needing to perform advanced postprocessing of the
results.
