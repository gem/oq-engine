# Running OpenQuake Engine Lite on Mac OS X
This page describes the steps necessary to run the development version of the OpenQuake Engine Lite (**oq-lite**), **oq-hazardlib** and **oq-risklib** on MacOS X. The recommended method is using [MacPorts](https://www.macports.org/) on MacOS X 10.10 Yosemite. 

## Install primary dependencies
First of all you need to have Xcode installed. It can be downloaded from the [AppStore](https://itunes.apple.com/us/app/xcode/id497799835?ls=1&mt=12). [MacPorts](https://www.macports.org/) needs also to be installed; you can follow the instructions on their website: https://www.macports.org/install.php.

## Install the OpenQuake dependencies via 'port'

As first step you have to sync your port index
```bash
$ sudo port sync
```

then you can proceed with the Engine Lite dependencies installation
```bash
$ sudo port install python27 py27-pip py27-ipython py27-jupyter py27-futures py27-h5py py27-lxml py27-mock py27-nose py27-numpy py27-psutil py27-scipy py27-shapely
```

set MacPorts' own python as the default python. It's strongly recommended to do same also with 'pip' and 'ipython'.
```bash
$ sudo port select --set python python27
$ sudo port select --set pip pip27
$ sudo port select --set ipython py27-ipython
```

## Clone the OpenQuake repos and configure them

Clone the OpenQuake Hzardlib and Risklib repositories. In this example they will be cloned in a 'GEM' folder in the user home directory
```bash
$ mkdir $HOME/GEM && cd $HOME/GEM
$ git clone --depth=1 https://github.com/gem/oq-hazardlib.git
$ git clone --depth=1 https://github.com/gem/oq-risklib.git
```

the `--depth` flag will make a 'shallow clone', reducing the size of the downloaded files.

### Compile the Hazardlib speedups

For more details see: https://github.com/gem/oq-hazardlib/wiki/Installing-C-extensions-from-git-repository
```bash
$ cd oq-hazardlib
$ python setup.py build_ext
$ cd openquake/hazardlib/geo
$ ln -s ../../../build/lib.*/openquake/hazardlib/geo/*.so .
```

### Set the PYTHONPATH and the PATH

The PYTHONPATH must be set; also the system PATH must be fix to include the oq-lite entry point
```bash
$ echo 'export PYTHONPATH="$HOME/GEM/oq-hazardlib:$HOME/GEM/oq-risklib:$PYTHONPATH"' >> $HOME/.profile
$ echo 'export PATH="$HOME/GEM/oq-risklib/bin:$PATH"' >> $HOME/.profile
$ source $HOME/.profile
```

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
  * Contact us on IRC: irc.freenode.net, channel #openquake
