# Implementing a new GSIM in the OpenQuake hazard library [provisional]

Below we provide a concise description of the process to be adopted for the creation of a new GSIM (i.e. GMPE or IPE) in the OpenQuake hazard library.

- Fork the oq-hazardlib master
https://help.github.com/articles/fork-a-repo

- Implement the new GMPE using as an example a GMPE already in the oq-hazardlib whose functional form is similar to the new GMPE.
https://github.com/gem/oq-hazardlib/tree/master/openquake/hazardlib/gsim

- Create verification tables following the examples that you find here:
https://github.com/gem/oq-hazardlib/tree/master/openquake/hazardlib/tests/gsim/data
Usually we create verification tables using an independent code provided by the original authors of the new GMPE. If this is not possible - if available - we use  an independent implementation available within code accessible on the web.

- Create tests for the new GMPE using the examples available here 
https://github.com/gem/oq-hazardlib/tree/master/openquake/hazardlib/tests/gsim

- When tests are passing, update the forked repository, rerun test and if everything is still them open a pull request. To run the full suite of tests you must open a terminal and run the commands:

```bash
cd &lt;to_hazardlib_root_directory&gt;
nosetests
```

- Create a new .rst file (needed to generate automatically documentation) in this directory (several examples available):
https://github.com/gem/oq-hazardlib/tree/master/doc/sphinx/gsim

- Check that the new code fulfils PEP8 standards (usually we do this using tools such as pep8 https://pypi.python.org/pypi/pep8) 
http://legacy.python.org/dev/peps/pep-0008/

- Run pylint to check your code.
