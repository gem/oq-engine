.. _vector-valued-psha:

Vector-valued PSHA Calculations
===============================

The post-processing framework and Vector-valued PSHA calculations
-----------------------------------------------------------------

Since version 3.17 the OpenQuake engine has special support for custom postprocessors. A postprocessor is a Python 
module located in the directory ``openquake/calculators/postproc`` and containing a ``main`` function with signature::

	def main(dstore, [csm], ...):
	    ...

Post-processors are called after a classical or preclassical calculation: the ``dstore`` parameter is a DataStore 
instance corresponding to the calculation, while the ``csm`` parameter is a CompositeSourceModel instance (it can be 
omitted if not needed).

The ``main`` function is called when the user sets in the job.ini file the parameters ``postproc_func`` and ``postproc_args``. 
``postproc_func`` is the dotted name of the postprocessing function (in the form ``modulename.funcname`` where ``funcname`` 
is normally ``main``) and ``postproc_args`` is a dictionary of literal arguments that get passed to the function; if not 
specified the empty dictionary is passed. This happens for instance for the conditional spectrum post-processor since it 
does not require additional arguments with respect to the ones in ``dstore['oqparam']``.

The post-processing framework was put in place in order to run VPSHA calculations. The user can find an example in 
``qa_tests_data/postproc/case_mrd``. In the job.ini file there are the lines::

	postproc_func = compute_mrd.main
	postproc_args = {
	  'imt1': 'PGA',
	  'imt2': 'SA(0.05)',
	  'cross_correlation': 'BakerJayaram2008',
	  'seed': 42,
	  'meabins': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
	  'sigbins': [0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
	  'method': 'indirect'}

while the postprocessor module ``openquake.calculators.postproc.compute_mrd`` contains the function::

	# inside openquake.calculators.postproc.compute_mrd
	def main(dstore, imt1, imt2, cross_correlation, seed, meabins, sigbins,
	         method='indirect'):
	    ...

Inside ``main`` there is code to create the dataset ``mrd`` which contains the Mean Rate Distribution as an array of 
shape L1 x L1 x N where L1 is the number of levels per IMT minus 1 and N the number of sites (normally 1).

While the postprocessing part for VPSHA calculations is computationally intensive, it is much more common to have a 
light postprocessing, i.e. faster than the classical calculation it depends on. In such situations the postprocessing 
framework really shines, since it is possible to reuse the original calculation via the standard ``--hc`` switch, i.e. you 
can avoid repeating multiple times the same classical calculation if you are interested in running the postprocessor 
with different parameters. In that situation the ``main`` function will get a DataStore instance with an attribute ``parent`` 
corresponding to the DataStore of the original calculation.

The postprocessing framework also integrates very well with interactive development (think of Jupyter notebooks). The 
following lines are all you need to create a child datastore where the postprocessing function can store its results 
after reading the data from the calculation datastore::

	>> from openquake.commonlib.datastore import read, create_job_dstore
	>> from openquake.calculators.postproc import mypostproc
	>> log, dstore = create_job_dstore(parent=read(calc_id))
	>> with log:
	..     mypostproc.main(dstore)

***************************************

The conditional spectrum post-processor
---------------------------------------

Since version 3.17 the engine includes an experimental post-processor which is able to compute the conditional spectrum.

The implementation was adapted from the paper *Conditional Spectrum Computation Incorporating Multiple Causal 
Earthquakes and Ground-Motion Prediction Models* by Ting Lin, Stephen C. Harmsen, Jack W. Baker, and Nicolas Luco 
(http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.845.163&rep=rep1&type=pdf) and it is rather sophisticated.

In order to perform a conditional spectrum calculation you need to specify, in addition to the usual parameter of a 
classical calculation:

1. a reference intensity measure type (i.e. imt_ref = SA(0.2))
2. a total-residual correlation model (i.e.
   total_residual_correlation_model = BakerJayaram2008)
3. a set of poes (i.e. poes = 0.01 0.1)

The engine will compute a mean conditional spectrum for each ``poe`` and site, as well as the usual mean uniform hazard 
spectra. The following restrictions are enforced:

1. the IMTs can only be of type ``SA`` and ``PGA``
2. the source model cannot contain mutually exclusive sources (i.e. you cannot compute the conditional spectrum for the Japan model)

An example can be found in the engine repository, in the directory openquake/qa_tests_data/conditional_spectrum/case_1. 
If you run it, you will get something like the following::

	$ oq engine --run job.ini
	...
	 id | name
	261 | Full Report
	262 | Hazard Curves
	260 | Mean Conditional Spectra
	263 | Realizations
	264 | Uniform Hazard Spectra

Exporting the output 260 will produce two files ``conditional-spectrum-0.csv`` and ``conditional-spectrum-1.csv``; the 
first will refer to the first poe, the second to the second poe. Each file will have a structure like the following::

	 #,,,,"generated_by='OpenQuake engine 3.13.0-gitd78d717e66', start_date='2021-10-13T06:15:20', checksum=3067457643, imls=[0.99999, 0.61470], site_id=0, lon=0.0, lat=0.0"
	sa_period,val0,std0,val1,std1
	0.00000E+00,1.02252E+00,2.73570E-01,7.53388E-01,2.71038E-01
	1.00000E-01,1.99455E+00,3.94498E-01,1.50339E+00,3.91337E-01
	2.00000E-01,2.71828E+00,9.37914E-09,1.84910E+00,9.28588E-09
	3.00000E-01,1.76504E+00,3.31646E-01,1.21929E+00,3.28540E-01
	1.00000E+00,3.08985E-01,5.89767E-01,2.36533E-01,5.86448E-01

The number of columns will depend from the number of sites. The conditional spectrum calculator, like the disaggregation 
calculator, is meant to be run on a very small number of sites, normally one. In this example there are two sites 0 and 1 
and the columns ``val0`` and ``val`` give the value of the conditional spectrum on such sites respectively, while the 
columns ``std0`` and ``std1`` give the corresponding standard deviations.

Conditional spectra for individual realizations are also computed and stored for debugging purposes, but they are not 
exportable.
