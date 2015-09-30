# Running OpenQuake Engine Lite on Windows
This page describes the steps necessary to run the development version of the OpenQuake Engine Lite (**oq-lite**), **oq-hazardlib** and **oq-risklib** on Windows. Installation on Windows is still experimental and provided 'as it is' with no warranty.

The supported way is using MiniGW and [Python(X,Y)](https://python-xy.github.io/) 2.7.9 on Windows 7 to 10. Python(X,Y) 2.7.10 is currently unsupported since it's unable to compile the hazardlib speedups. 

## Install primary dependencies
First of all you need to have GIT installed. It can be downloaded from the [official GIT website](https://git-scm.com/download).

### Python(X,Y)
Download Python(X,Y) 2.7.9 from the University of Kent mirror and install it: http://www.mirrorservice.org/sites/pythonxy.com/Python(x,y)-2.7.9.0.exe
During the setup make sure you have selected also **Cython** and **GDAL** packages.

### Shapely
Shapely isn't provided by the main Python(X,Y) installer and needs to be downloaded and installed separately from http://sourceforge.net/projects/python-xy/files/plugins/shapely-1.5.9-7_py27.exe/download.

### Hazardlib speedups
To be able to compile the hazardlib speedup (and then to install the Hazardlib) you'll need a **GCC** compiler. GCC is provided by the Python(X,Y) MinGW package. Download and install it from here http://sourceforge.net/projects/python-xy/files/plugins/mingw-4.8.1-3.exe/download.


## Clone the OpenQuake repos and install them

Clone the OpenQuake Hzardlib and Risklib repositories. In this example they will be cloned in a 'GEM' folder in the user home directory.
```bash
$ mkdir $HOME/GEM && cd $HOME/GEM
$ git clone --depth=1 https://github.com/gem/oq-hazardlib.git
$ git clone --depth=1 https://github.com/gem/oq-risklib.git
```
this example uses the Bash console provided by MinGW and the GIT windows packages. `cmd` can also be used (some commands may differ). The `--depth` flag will make a 'shallow clone', reducing the size of the downloaded files.

### Install Hazardlib

```bash
$ cd oq-hazardlib
$ python setup.py build --compiler=mingw32
$ python setup.py install
```
### Install Risklib and oq-lite 

```bash
$ cd oq-risklib
$ python setup.py install
```

### Set the PYTHONPATH and the PATH

The PYTHONPATH must be set; also the system PATH must be fix to include the oq-lite entry point
```bash
$ echo 'export PYTHONPATH="$HOME/GEM/oq-hazardlib:$HOME/GEM/oq-risklib:$PYTHONPATH"' >> $HOME/.profile
$ echo 'export PATH="$HOME/GEM/oq-risklib/bin:$PATH"' >> $HOME/.profile
$ source $HOME/.profile
```

### Notes

Using Hazardlib and Risklib (and oq-lite) from sources is not supported yet. It can be possible if you don't expect to use `oq-lite` and you don't need the speedups.
When using the libraries from sources you need to set the PYTHONPATH in the Windows Environment settings (under advanced options, it may require administration rights).


## Run a demo

This is an example of the output from the `AreaSourceClassicalPSHA` demo:

```bash
$ oq-lite run $HOME/GEM/oq-risklib/demos/AreaSourceClassicalPSHA/job.ini

INFO:root:Reading the site collection
INFO:root:Reading the composite source model
INFO:root:Processing 1 fast sources...
INFO:root:Total weight of the sources=[ 41.]
INFO:root:Expected output size=[ 416064.]
INFO:root:Starting 9 tasks
INFO:root:Submitting task classical #1
INFO:root:Submitting task classical #2
INFO:root:Submitting task classical #3
INFO:root:Submitting task classical #4
INFO:root:Submitting task classical #5
INFO:root:Submitting task classical #6
INFO:root:Submitting task classical #7
INFO:root:Submitting task classical #8
INFO:root:Submitting task classical #9
INFO:root:Sent 530.77 KB of data
INFO:root:classical  11%
INFO:root:classical  22%
INFO:root:classical  33%
INFO:root:classical  44%
INFO:root:classical  55%
INFO:root:classical  66%
INFO:root:classical  77%
INFO:root:classical  88%
INFO:root:classical 100%
INFO:root:Received 28.61 MB of data
INFO:root:Total time spent: 65.810972929 s
INFO:root:Memory allocated: 44.86 MB
See the output with hdfview /Users/user/oqdata/calc_1/output.hdf5
```

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the developer mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-dev
  *   * Contact us on IRC: irc.freenode.net, channel #openquake
