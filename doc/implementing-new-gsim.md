# Implementing a new GSIM in the OpenQuake hazard library [provisional]

Below we provide a concise description of the process to be adopted for the creation of a new GSIM (i.e. GMPE or IPE) in the OpenQuake hazard library.

- Read the [Development guidelines](development-guidelines.md) and the [Developers notes](developers-notes.md)

- Fork the oq-engine master
https://help.github.com/articles/fork-a-repo

- Implement the new GMPE using as an example of a GMPE already in the oq-engine whose functional form is similar to the new GMPE.
https://github.com/gem/oq-engine/tree/master/openquake/hazardlib/gsim

- Create verification tables following the examples that you find here:
https://github.com/gem/oq-engine/tree/master/openquake/hazardlib/tests/gsim/data
Usually we create verification tables using an independent code provided by the original authors of the new GMPE. If this is not possible - if available - we use an independent implementation available within code accessible on the web. If verification tables are missing this must be clearly stated as in this example https://github.com/gem/oq-engine/blob/master/openquake/hazardlib/gsim/raghukanth_iyengar_2007.py#L119

- Create tests for the new GMPE using the examples available here 
https://github.com/gem/oq-engine/tree/master/openquake/hazardlib/tests/gsim

- When tests are passing, update the forked repository, rerun tests and if everything is still okay, open a pull request. To run the full suite of tests you must open a terminal and run the commands:

```bash
cd oq-engine;
nosetests -vsx openquake.hazardlib
```

- Update the following .rst file (needed to generate automatically documentation):
https://github.com/gem/oq-engine/blob/master/doc/sphinx/openquake.hazardlib.gsim.rst

- Check that the new code fulfils PEP8 standards (usually we do this using tools such as flake8 https://pypi.python.org/pypi/flake8) 
http://legacy.python.org/dev/peps/pep-0008/

- Update the changelog file 
https://github.com/gem/oq-engine/blob/master/debian/changelog following the [Developers notes](developers-notes.md)
