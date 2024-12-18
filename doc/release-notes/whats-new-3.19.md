Release notes v3.19
===================

Version 3.19 is the culmination of 4 months of work involving nearly 340
pull requests. It is aimed at users wanting the latest features, bug fixes
and maximum performance. Users valuing stability may want to stay with
the LTS release instead (currently at version 3.16.8).

The complete set of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.19/debian/changelog

A summary is given below.

Multifault sources optimizations
--------------------------------

Last year we included the UCERF3 model for California in the USA model.
Since the UCERF3 model is implemented in terms of multifault sources,
which were particularly slow, it was basically impossible to run it
without resorting to tricks. The memory occupation was over 4 GB per
core and the estimated runtime over one week on a powerful server with
120 cores. Now multifault sources are as fast as other sources, the
memory occupation is under 3 GB per core and the model runs in less
than one day.

The performance improvement is impressive even for single site calculations.
For instance, performing a hazard calculation for San Francisco took
4 hours with engine-3.18 on a server with a Ryzen 7840HS processor,
while now it takes only 10 minutes.

Notice that for event-based calculations, there is no much difference,
the speedup is relevant only for classical calculations.

Classical calculations
----------------------

We have improved the `preclassical` part of the calculation, which is
now substantially faster in many cases.

We have improved the `disagg_by_src` functionality and now it does not generate
one per task per source anymore. That was very inefficient in models with
thousands of sources.

[Chris di Caprio](https://github.com/chrisdicaprio) pointed out that the 
engine was producing incorrect hazard curves in the ultra-high intensity 
region (around 10g) due to a numerical error, which has been fixed.

There was a serious bug with the ordering of the IMTs causing (in some
situations) the generation of uniform hazard spectra with two peaks.
The bug was introduced in version 3.17 and it is now finally solved.

The classical calculator has been extended to perform aftershock calculations
if a file `delta_rates.csv` with fields `source_id`, `rup_id`, `delta` is
passed to the job.ini. The `delta` field contains corrections to the
occurrence rates of the underlying ruptures. An example of usage is
given here:

https://github.com/gem/oq-engine/blob/engine-3.19/openquake/qa_tests_data/aftershock/case_1/job.ini

There is some checking for errors, for instance if there are
`source_id` or `rup_id` values that do not exist in the hazard model.

The experimental `AftershockCalculator` has been removed since its
functionality has been subsumed inside the standard classical
calculator.

Event based improvements
------------------------

It is now possible to specify a `geometry_file` in the job.ini, containing
a polygon or a multipolygon, and use it to discard the ruptures outside
the region ([#8112](https://github.com/gem/oq-engine/issues/8112)).

We fixed the exporting and then reimporting of GMFs in HDF5 format,
a feature crucial for producing a curated set of events and GMFs.
The problem was not saving the investigation_time parameter, needed
to compute properly the aggregate loss curves.

We fixed the `gmf_data` exporter which was failing with an error
in presence of a filtered site collection.

We removed a misleading warning *For large exposures you must set
collect_rlzs=true or avg_losses=false*.

hazardlib
---------------

[Chris di Caprio](https://github.com/chrisdicaprio) from GNS Science 
contributed the full set of GMPEs for the latest National Seismic 
Hazard Model for New Zealand.

We fixed an implementation bug in the ZalachorisRathje2019 GMPE, [reported by
Erika Schiappapietra](https://groups.google.com/g/openquake-users/c/fEJc7Y5mYd0/m/JTrYGA-9AQAJ). 
The magnitude scaling factor formula used is valid for Mb <= Mw < 5.8, 
but the engine was using it for Mb < Mw < 5.8, i.e. missing the case Mw == Mb.

[Thomas Bornstein](https://github.com/borthom) 
[reported an error](https://github.com/gem/oq-engine/issues/9313) 
in the implementation of the WongEtAl2022 GMPEs, which we fixed.

[Ali Talha Atici reported an issue](https://groups.google.com/g/openquake-users/c/zFQXf5Otl7w/m/JU5XYo7wAAAJ) 
with calculations using the GMPE ManeaEtAl2021. The problem was solved by renaming the
existing site parameter `fpeak` as `f0`.

[Graeme Weatherill](https://github.com/g-weatherill) 
[contributed a set of new GMPEs](https://github.com/gem/oq-engine/pull/9274): 
Weatherill2024ESHM20AvgSA, Weatherill2024ESHM20SlopeGeologyAvgSA, 
Weatherill2024ESHM20Homokedastic and GmpeIndirectAvgSA, 
for use in the European model, and improved support for AvgSA.

The NathEtAl2012 GMPE was providing unrealistic values for PGV that
could not be corrected ([#9184](https://github.com/gem/oq-engine/issues/9184)), 
so we removed support for that Intensity Measure Type.

We fixed the Goda & Atkinson cross-correlation model, that could produce
correlation coefficients larger than 1.0 for IMT pairs like {PGA, SA(0.1)}
(this is an artifact of the engine implementation that treats PGA as
SA(0.05)) ([#9207](https://github.com/gem/oq-engine/pull/9207)).

We fixed a bug in the calculation of Rjb for gridded surfaces.

We improved the algorithm used to generate kite surfaces, causing sligthly
different geometries and therefore slightly different hazard curves.

It is now forbidden to use non-standard methods in GMPE classes, resulting
in an error rather than a warning, as in the past.

Risk
----

We improved the validation of CSV exposures, producing better error
messages in case of errors in the header (due to missing fields) or in
the body of the CSV files.

We extended the exposure so that it is possible to map different fields
to the same CSV column, as in this example:
```xml
  <exposureFields>
    <field oq="night" input="total_occupants" />
    <field oq="residents" input="total_occupants" />
  </exposureFields>
```
The reason is that depending on the field name ("night" vs "residents")
the engine can use a different algorithm even if the underlying data
are the same.

We optimized some calculations involving secondary perils by making
sure that SecondaryPerils classes are instantiated only once. In the
particular case of the TodorovicSilva2022NonParametric model, we got a
huge speedup by moving the reading of the associated .onnx file at
instantiation time ([#9375](https://github.com/gem/oq-engine/pull/9375)).

We added a warning in conditioned GMFs calculations in the case when
all stations are beyond the `maximum_distance_stations` parameter, i.e.
they are not used at all ([#9275](https://github.com/gem/oq-engine/pull/9275)).

Bug fixes
---------

While working on the AELO project we discovered a long standing bug
in the disaggregration of mutually exclusive sources used in the Japan model.
This is now fixed. We also fixed a bug on disaggregation by source
by forcing a naming convention (the so called the colon convention)
on mutex sources.

In general, disaggregation by source only works if the source IDs are not
duplicated; however, for historical reasons (i.e. lack of checking) most
hazard models in the GEM mosaic contains duplicated source IDs. Now
a clear warning is printed, informing that such models cannot be used
to perform disaggregation by source. All models used in AELO calculations
have been fixed and in time we will fix the entire mosaic.
Notice that sources with the same ID in different branches of the logic tree are
accepted since they can be disambiguated by taking into account the branch ID.

While running a chain of calculations (like building the ruptures, building
the GMFs and then building the risk) has always worked, there was a bug
in the risk exporters forbidding the export. It has been fixed now.

We fixed the site model parameters in the EventBasedPSHA demo, where
`z1pt0` and `z2pt5` were exchanged.

In rare cases it was possible to get insured losses larger than ground losses
due to an ordering bug.

We fixed a bug in calculations using the --hc option: the engine was
taking the parent site collection instead of the child site collection.

We fixed a bug affecting ruptures generated by MultiFaultSources.
It was always possible to export such ruptures in CSV format with the `oq
extract ruptures`, but in some cases (due to inhomogeneous mesh arrays)
they could not be read by an event-based calculation.

The engine is now able to skip the spuriuos `__MACOSX__` directory
produced on Mac OS X when zipping a set of files.

At user request, we mad it possible to disable the `vs30_tolerance`
check on-demand, by setting `vs30_tolerance = -1`. This is only
relevant for people experimenting with the site amplification feature.

Aristotle project
-----------------

[Aristotle](https://www.globalquakemodel.org/proj/aristotle) is a
project to provide Multi-Hazard advice to the European Research
Coordination Centre in case of disasters. GEM is working on the
earthquake aspects.

As part of the Aristotle workflow, the engine has been extended to be
able to download `rupture.json` files from the USGS site so that
scenario calculations can be performed by using the GEM exposure models
and vulnerability functions. Alternatively, one can use a `rupture_dict`
parameter in the job.ini to specify a planar rupture.

Moreover, we have now a script which is able to store the GEM's global
exposure model and site parameters in a HDF5 and a fast way to retrieve
the assets and site parameters around any site in the world.

Finally, we have a geolocation utility which is able to determine
the country and the hazard mosaic model to use for each site in the world.

AELO project
--------------

[AELO](https://www.globalquakemodel.org/proj/aelo) is a project
carried out in collaboration with the USGS to provide a web service
for computing design ground motions (on rock and soil) that are
compliant with the ASCE guidelines (ASCE 7-16, ASCE 41-17, ASCE 7-22,
ASCE 41-23). After 2 years of effort the workflow for computing the
ASCE 7-16 and ASCE 41-17 parameters has been completed and the user
interface is ready, including a few plotting facilities. That
required significant changes to the underlying engine libraries, to
the WebUI and to the hazard models, as well a many bug fixes.
Special care has been taken to give clear messages and warnings in
case of low hazard sites.

As a consequence of the AELO project, now the command `oq mosaic
run_site` can process a CSV file with fields ID,Longitude,Latitude and
compute the asce41 and asce07 parameters by spawning multiple parallel
computations, one for each site in the file. The command is as efficient as
it can be and it is used to run nightly tests on ~500 sites of interest.

`oq commands`
-------------

We added a command `oq extract/ruptures?threshold=` to extract
the most relevant ruptures, i.e. the ruptures causing most of the
losses. For instance  `oq extract/ruptures?threshold=0.8` means
extracting the ruptures causing 80% or more of the losses.

Similarly, we added a command `oq export relevant_gmfs -e hdf5` to
extract the most relevant ground motions, i.e. the ground motion
fields and related events causing most of the losses. Risk
calculations can be started from the extracted GMFs and aggregated
loss curves can be build from them.

We extended the command `oq mosaic sample_rups` to multiple models.
For instance, if you wanted to generate an event set for the Mediterranean
region without double counting the ruptures you can just run
```
$ oq mosaic sample_rups EUR,NAF,MIE
```
This will generate 3 computations (one per model) each containing only
ruptures within the geographic boundaries of the hazard model.

The command `oq compare` was buggy, since the tolerance parameters
were ignored. This is now fixed.

The command `oq sample` has been extended to work for multifault sources.

We added a command `oq info executing` to see which jobs are currently
executing.

We extended `oq info` to manage shapefiles and show their content.

We extended `oq plot_assets` to plot the contour of the countries

We added a view `oq show rup:<source_id>` displaying the context
objects generated by a given source.

WebUI
-----

There was a large amount of work on the WebUI, also in relation to the
AELO project.

We improved the creation of new users and the password reset
functionality.

In the WebUI there is a new column 'Start time' with the starting time
of each calculation

The style of that table and of the buttons has been improved.

Accessing an URL corresponding to a non-existing calculation now
correctly returns a HttpResponseNotFound error.

Finally, we have a new functionality to display annoncements to all users (like
"the server will be down for maintenance next Monday").

IT highlights
-------------

We added support for Python 3.11 and removed support for Python 3.8, as
promised in the previous release. Python 3.9 is deprecated and will be
removed in the next release.  We updated numpy to version 1.26, scipy
to version 1.8.1, h5py to version 3.10, numba to 0.58.1, fiona to
version 1.9.5, GDAL to version 3.7.3, pyproj to 3.6.1 and a few other
dependencies. In particular we updated Django to version 4.2.10.

The upgrade to numpy 1.26 caused a lot of trouble since numpy >= 1.25
introduced a machine-dependent optimization in `numpy.argsort` (depending
if the processor supports the AVX-512 instruction set or not). To
keep the numbers the same, both on old processors and new processors, we
had to change the weighted quantile algorithm used to build the
hazard curves, as well as the algorithm used in the generation of
risk curves that was depending on an unspecified ordering.

We started using urllib3 to avoid SSL errors on Windows affecting the urllib
in the standard library.

We removed the DbServer from single user installations, since the database
can be accessed directly. This is useful also in HPC settings, where the user
has no permissions to install and start a global DbServer.

Finally, there were some minor improvements to the universal installer: in
particular, now it warns the user that the virtual environment must be
removed before reinstalling and suggests to use to use the `--venv`
option to build a new one.
