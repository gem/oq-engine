## Continuous integration and testing for OpenQuake

### Automatic testing

The OpenQuake code is automatically tested by a [Continuous integration](https://ci.openquake.org) system at every merge and every night. This system uses [Jenkins](http://jenkins-ci.org/).

### Manual testing

The full suite of tests for the OpenQuake Engine can be run using `nose`

```
nosetests -v -a '!slow'
```

The command must be run from the OpenQuake Engine code location. On a development installation this is usually `oq-engine`. On production system it can be `/usr/lib/python2.7/site-packages/openquake` or `/usr/lib/python2.7/dist-packages/openquake`.
