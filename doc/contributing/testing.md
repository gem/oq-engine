# Continuous integration and testing for OpenQuake

## Automatic testing

The OpenQuake code is automatically tested by Continuous integration systems (GitHub and GitLab Actions), at every merge and every night.

## Manual testing

The tests for the OpenQuake Engine can be run by using `pytest`, assuming you have an [**installation from sources**](../getting-started/installation-instructions/development.rst).
First of all you need to create the engine database:

```bash
$ oq engine --upgrade-db
```

Then you can run the tests as follows:

```bash
# Hazardlib
$ pytest -vs openquake/hazardlib

# Calculators
$ pytest -vs openquake/calculators
```

See the `pytest` [documentation](https://docs.pytest.org/en/latest/contents.html) for further information and command options.

***

# Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
