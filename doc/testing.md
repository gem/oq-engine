## Continuous integration and testing for OpenQuake

### Automatic testing

The OpenQuake code is automatically tested by a [Continuous integration](https://ci.openquake.org) system at every merge and every night. This system uses [Jenkins](http://jenkins-ci.org/).

Current build status is  [![Build Status](https://ci.openquake.org/job/master_oq-hazardlib/badge/icon)](https://ci.openquake.org/job/master_oq-hazardlib/)

### Manual testing

The suite of tests for the OpenQuake Hazardlib can be run using `nose`

```
nosetests -v -a '!slow'
```

The command must be run from the OpenQuake Hazardlib code location. On a development installation this is usually `oq-hazardlib`. On production system it can be `/usr/lib/python2.7/site-packages/openquake/hazardlib` or `/usr/lib/python2.7/dist-packages/openquake/hazardlib`.
