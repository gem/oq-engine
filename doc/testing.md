## Continuous integration and testing for OpenQuake

### Automatic testing

The OpenQuake code is automatically tested by Continuous integration systems, [Jenkins](https://ci.openquake.org) and [Travis](https://travis-ci.org/gem/oq-engine), at every merge and every night.

### Manual testing

The full suite of tests for the OpenQuake Engine can be run using `pytest` from [**source code**](installing/development.md):

```bash
$ oq dbserver start
$ pytest -v openquake
```

Python packages can also be specified to run only a subset of tests. Some examples are:

```bash
# Hazardlib
$ pytest -vs openquake/hazardlib

# Calculators
$ oq dbserver start
$ pytest -vs openquake/calculators

# Engine server
$ oq dbserver start
$ pytest -vs openquake/server
```

See the `pytest` [documentation](https://docs.pytest.org/en/latest/contents.html) for further information and command options.

Some tests in specific packages do require the DbServer to be started first (`oq dbserver start`).

***

## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
