# Implementing a new GSIM in the OpenQuake hazard library [provisional]

Below we provide a concise description of the process to be adopted for the creation of a new GSIM (i.e. GMPE or IPE) in the OpenQuake hazard library.

- Read the [Development guidelines](https://github.com/gem/oq-engine/blob/master/doc/contributing/development-guidelines.md)

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
https://github.com/gem/oq-engine/blob/master/doc/api-reference/openquake.hazardlib.gsim.rst

- Check that the new code fulfils PEP 8 standards (usually we do this using tools such as flake8 https://pypi.python.org/pypi/flake8) 
https://www.python.org/dev/peps/pep-0008/

- A particular point to note is that, as explained in [Python documentation](https://docs.python.org/3.7/tutorial/datastructures.html#sets),
"Curly braces or the set() function can be used to create sets. Note: to create an empty set you have to use set(), not {}; the latter creates an empty dictionary".
Therefore assignment statements such as REQUIRES_RUPTURE_PARAMETERS = {'mag'} and REQUIRES_RUPTURE_PARAMETERS = set() are both correct.

- Update the changelog file 
https://github.com/gem/oq-engine/blob/master/debian/changelog following the [Developers notes](updating-the-changelog.md)

# Implementing a new conditional GSIM in the OpenQuake hazard library

Conditional GMPEs within OpenQuake are specified within `ModifiableGMPE`. We use `ModifiableGMPE` because it allows us to easily specify each conditional GMPE
that we wish to use to compute each IMT (probably) not supported by the underlying GSIM which we are conditioning the predictions of the conditional GMPE upon.
See `oq-engine/openquake/hazardlib/gsim/mgmpe/modifiable_gmpe.py` for more information on `ModifiableGMPE`.

For an example of this syntax within a GMPE XML, you can inspect `oq-engine/openquake/qa_test_data/classical/case_90/conditional_gmpes.xml`, within which
a different conditional GMPE is specified for each IMT not supported by the underlying GSIM (here the underlying GSIM is `AbrahamsonGulerce2020SInter`).

To implement a conditional GMPE within the OQ Engine, the implementation procedure differs slightly from a more conventional GMPE. 

The first thing to note, is that you must add an attribute to the `GSIM` object called `REQUIRES_IMTS` which is a list containing (as `imt` objects) the
IMTs required by the conditional GMPE for the conditioning process. For example, the `MacedoEtAl2019SInter` GMPE requires both `PGA` and `SA(1.0)` for the
prediction of `IA` (Arias Intensity) and therefore this information must be provided in the `GSIM` object for use within `ModifiableGMPE` when it is handling
the IMTs that are needed for each conditional GMPE. Please refer to `AbrahamsonBhasin2020` for a (slightly) more complex example of how this attribute can be
managed if necessary (there is a case where the conditioning period of the spectral acceleration is magnitude-dependent and therefore unknowable apriori). An error
is raised in `ModifiableGMPE` if a conditional GMPE lacks this attribute.  It is also important to emphasise that `REQUIRED_IMTS` is different to the information
stored within `DEFINED_FOR_INTENSITY_MEASURE_TYPES`.

The second thing to note, is that the `compute` method of conditional GMPEs is less conventional (but still abides to the requirements defined within the `MetaGSIM`
metadata class). We recommend inspecting either the `MacedoEtAl2019SInter` or `AbrahamsonBhasin2020` GSIMs to understand how the `compute` method (and the variables
fed into it) are handled throughout the GSIM itself when computing the conditioned intensity measures. The main thing to take away is that the predictions from the
IMTs required by the conditional GMPE are stored in the dictionary called `base_preds` which is an argument into the `compute` method for conditional GMPEs.

Lastly, you can use regular GSIM unit tests, but you must make use of `modified_gsim` (which is found within `oq-engine/openquake/hazardlib/valid`) to instantiate
the `GSIM_CLASS` object which is always required for a standard GSIM unit test. Examples of this can be found in the unit tests for `MacedoEtAl2019SInter` and
`AbrahamsonBhasin2020S`.