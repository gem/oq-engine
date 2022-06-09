The conditional spectrum calculator
========================================

The ``conditional_spectrum`` calculator is an experimental calculator
introduced in version 3.13, which is able to compute the conditional
spectrum in the sense of Baker.

In order to perform a conditional spectrum calculation you need to
specify (on top of the usual parameter of a classical calculation):

1. a reference intensity measure type (i.e. ``imt_ref = SA(0.2)``)
2. a cross correlation model (i.e. ``cross_correlation = BakerJayaram2008``)
3. a set of poes (i.e. ``poes = 0.01 0.1``)

The engine will compute a mean conditional spectrum for each ``poe`` and site,
as well as the usual mean uniform hazard spectra. The following restrictions
are enforced:

1. the IMTs can only be of type ``SA`` and ``PGA``
2. the source model cannot contain mutually exclusive sources (i.e.
   you cannot compute the conditional spectrum for the Japan model)

An example can be found in the engine repository, in the directory
openquake/qa_tests_data/conditional_spectrum/case_1. If you run it,
you will get something like the following::

 $ oq engine --run job.ini
 ...
  id | name
 261 | Full Report
 262 | Hazard Curves
 260 | Mean Conditional Spectra
 263 | Realizations
 264 | Uniform Hazard Spectra

Exporting the output 260 will produce two files ``conditional-spectrum-0.csv``
and ``conditional-spectrum-1.csv``; the first will refer to the first ``poe``,
the second to the second ``poe``. Each file will have a structure like
the following::

  #,,,,"generated_by='OpenQuake engine 3.13.0-gitd78d717e66', start_date='2021-10-13T06:15:20', checksum=3067457643, imls=[0.99999, 0.61470], site_id=0, lon=0.0, lat=0.0"
 sa_period,val0,std0,val1,std1
 0.00000E+00,1.02252E+00,2.73570E-01,7.53388E-01,2.71038E-01
 1.00000E-01,1.99455E+00,3.94498E-01,1.50339E+00,3.91337E-01
 2.00000E-01,2.71828E+00,9.37914E-09,1.84910E+00,9.28588E-09
 3.00000E-01,1.76504E+00,3.31646E-01,1.21929E+00,3.28540E-01
 1.00000E+00,3.08985E-01,5.89767E-01,2.36533E-01,5.86448E-01

The number of columns will depend from the number of sites. The
conditional spectrum calculator, like the disaggregation calculator,
is mean to be run on a very small number of sites, normally one.
In this example there are two sites 0 and 1 and the columns ``val0``
and ``val`` give the value of the conditional spectrum on such sites
respectively, while the columns ``std0`` and ``std1`` give the corresponding
standard deviations.

Conditional spectra for individual realizations are also computed and stored
for debugging purposes, but they are not exportable.

The implementation was adapted from the paper *Conditional Spectrum
Computation Incorporating Multiple Causal Earthquakes and
Ground-Motion Prediction Models* by Ting Lin, Stephen C. Harmsen,
Jack W. Baker, and Nicolas Luco (http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.845.163&rep=rep1&type=pdf) and it is rather sophisticated.
The core formula is implemented in the method
`openquake.hazardlib.contexts.get_cs_contrib`.

The ``conditional_spectrum`` calculator, like the disaggregation calculator,
is a kind of post-calculator, i.e. you can run a regular classical calculation
and then compute the  ``conditional_spectrum`` in post-processing by using
the ``--hc`` option.
