The OpenQuake-engine csv outputs
================================

As of now (engine-3.13) the OpenQuake-engine csv outputs have the following
structure:

1. First of all, there is a metadata section, where all lines start with
   the character `#` and contain comma separated name=value pairs. The
   metadata section can be empty.
2. Secondly, there is a header section, a comma separated list of field names,
   that contain strictly ASCII characters in the range a-zA-Z0-9 without spaces.
   Underscores and hyphens are accepted. The header section cannot be empty.
3. Finally, there is a data section which is a regular csv with the number of
   columns equal to the number of fields in the header. The data section
   can be empty.

The metadata section is the most experimental and subject to change.
The header section can also change if new fields are added. It is
unlikely that a field gets removed, but this has happened in the past.
Users should NEVER rely on the order of the columns. The header is there
so that the columns can referenced by name.

Users wanting to read the engine outputs can implement their own readers
or they can use the engine reader:

```python
>>> from openquake.baselib.hdf5 import read_csv
>>> aw = read_csv('/path/to/output.csv')
```

The engine reader returns an `ArrayWrapper` instance which is an array-like
object; the underlying numpy array can be accessed from the `aw.array`
attribute. The metadata variables appear as attributes of the `aw` object.
For instance given a hazard map like the following one
```
$ cat hazard_map-rlz-000_28524.csv
# generated_by='OpenQuake engine 3.13.0-gitaaed04b512', start_date='2022-01-11T11:21:25', checksum=184624282, kind='rlz-000', investigation_time=1.0
lon,lat,PGA-0.002105,SA(0.2)-0.002105,SA(1.0)-0.002105
-123.23738,49.27479,4.189332E-02,9.559597E-02,3.100745E-02
-123.23282,49.26162,4.167645E-02,9.511285E-02,3.087749E-02
-123.20480,49.26786,4.209680E-02,9.600781E-02,3.097641E-02
```

it can be read in ipython as follows:

```python
In [1]: from openquake.baselib.hdf5 import read_csv
In [3]: aw = read_csv('hazard_map-rlz-000_28524.csv')

In [4]: aw.generated_by
Out[4]: 'OpenQuake engine 3.13.0-gitaaed04b512'

In [5]: aw.kind
Out[5]: 'rlz-000'

In [6]: aw.investigation_time
Out[6]: 1.0
In [7]: aw.array
Out[7]: 
array([(-123.23738, 49.27479, 0.04189332, 0.09559597, 0.03100745),
       (-123.23282, 49.26162, 0.04167645, 0.09511285, 0.03087749),
       (-123.2048 , 49.26786, 0.0420968 , 0.09600781, 0.03097641)],
      dtype=[('lon', '<f8'), ('lat', '<f8'), ('PGA-0.002105', '<f8'), ('SA(0.2)-0.002105', '<f8'), ('SA(1.0)-0.002105', '<f8')])
```

The `checksum` attribute is an identifier for the calculation input: if
you have a user sending you an output and claiming that that output
comes from a certain input, you can verify that claim by comparing the
checksum with the input checksum (see the `oq checksum` command).
