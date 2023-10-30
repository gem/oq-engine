# Implementing a new GSIM in the OpenQuake hazard library [provisional]

Below we provide a concise description of the process to be adopted for the creation of a new GSIM (i.e. GMPE or IPE) in the OpenQuake hazard library.

- Read the [Development guidelines](development-guidelines.md)

- Fork the oq-engine master
https://help.github.com/articles/fork-a-repo

- Implement the new GSIM using as an example of a GSIM already in the oq-engine, whose functional form is similar to the new GSIM.
https://github.com/gem/oq-engine/tree/master/openquake/hazardlib/gsim

- Acceleration should be returned in units of g, and standard deviation values in natural logarithm. If this is not consistent with the original GMPE, then a conversion needs to be made.

- Create verification tables following the examples that you find here:
https://github.com/gem/oq-engine/tree/master/openquake/hazardlib/tests/gsim/data
Usually we create verification tables using an independent code provided by the original authors of the new GSIM. If this is not possible - if available - we use an independent implementation available within code accessible on the web. If verification tables are missing, this must be clearly stated as in this example https://github.com/gem/oq-engine/blob/master/openquake/hazardlib/gsim/raghukanth_iyengar_2007.py#L119

- Create tests for the new GSIM using the examples available here 
https://github.com/gem/oq-engine/tree/master/openquake/hazardlib/tests/gsim

- When tests are passing, update the forked repository, rerun tests and if everything is still okay, open a pull request. To run the full suite of tests, open a terminal and run the following commands:

```bash
cd oq-engine;
pytest -xv openquake/hazardlib
```

- Update the following .rst file (needed to generate automatically documentation):
https://github.com/gem/oq-engine/blob/master/doc/sphinx/openquake.hazardlib.gsim.rst

- Check that the new code fulfils PEP 8 standards (usually we do this using tools such as flake8 https://pypi.python.org/pypi/flake8) 
https://www.python.org/dev/peps/pep-0008/

- A particular point to note is that, as explained in [Python documentation](https://docs.python.org/3.7/tutorial/datastructures.html#sets),
"Curly braces or the set() function can be used to create sets. Note: to create an empty set you have to use set(), not {}; the latter creates an empty dictionary".
Therefore assignment statements such as REQUIRES_RUPTURE_PARAMETERS = {'mag'} and REQUIRES_RUPTURE_PARAMETERS = set() are both correct.

- Update the changelog file 
https://github.com/gem/oq-engine/blob/master/debian/changelog following the [Developers notes](updating-the-changelog.md)
