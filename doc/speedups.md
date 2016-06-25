# Installing geodetic speedups from git repository

### Pre-requisites
We Assume that you have already:
*  cloned the hazardlib git repository
*  installed a C compiler and linker

### Building the extension
cd into the top-level directory of the hazardlib git repository

```bash
python setup.py build_ext
```

### Install symlinks (Unix-like systems only...)

```bash
cd openquake/hazardlib/geo
ln -s ../../../build/lib.*/openquake/hazardlib/geo/*.so .
```

### Run tests

```bash
nosetests -v -a '!slow'
```
If you do not see a warning message of the form "RuntimeWarning: geodetic speedups are not available", then you have installed the C extensions correctly.
