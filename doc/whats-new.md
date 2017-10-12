Release notes for the OpenQuake Engine, version 2.6
===================================================

This release introduced several improvements and new features in the
hazard and risk calculators. Several bugs were fixed, some outputs
were changed and there were a few improvements to the installers, to
the Web User Interface (WebUI) and to the engine itself.

More than 130 pull requests were closed. For the complete list of
changes, please see the changelog:
https://github.com/gem/oq-engine/blob/engine-2.6/debian/changelog.

Hazard
---------------

We changed the source weighting algorithm, which is now proportional
both to the number of ruptures and to the number of affected
sites. The consequence is a better task distribution, so that some
calculations dominated by slow tasks are faster than before.

We fixed a few bugs in the hazard exporters; moreover we have now an
experimental command `oq extract hazard/rlzs` which is able to produce
a single .hdf5 file with all hazard curves, maps and
uniform hazard spectra for all realizations; this was requested by
some power users and it is documented in
https://github.com/gem/oq-engine/blob/engine-2.6/doc/oq-commands.md.

We changed the numbering algorithm of the event IDs in the event based
calculator. Now the event IDs are independent from the number of
generated tasks. Therefore you will see different event IDs in the
rupture exports, the ground motion field exports and the event loss
table exports.

In hazardlib we implemented the Munson and Thurber 1997 (Volcanic)
Ground Motion Prediction Equation (GMPE) and the Atkinson 2010 GMPE
modified for Hawaiʻi. The Coefficients Table was enhanced so that it can be
instantiated with dictionaries as well as strings — this is useful
for users who need to modify the Coefficients Table dynamically.
We fixed a bug when computing the Rjb distances with multidimensional
meshes, which could be important for hazardlib power users.
We fixed a bug with MultiPointSources, in the case of an `arbitraryMFD`
magnitude-frequency-distribution. The Hazard Modeller's Toolkit parser has
been updated to read source models in the NRML 0.5 format.

We also fixed some small bugs (one in the Hazard Modeller's Toolkit,
one in the script `correct_complex_sources.py`), and added a few additional
checks. In particular, if there are multiple realizations and no hazard stats,
it is now an error to set `hazard_maps=true` or `uniform_hazard_spectra=true`,
because there will be no output (since we now only export the statistics).
There is now also a check that the number of intensity measure types
is greater than one if `uniform_hazard_spectra=true`.

We extended the `sz` field in the rupture surface to 2 bytes, making it
possible to use a smaller mesh spacing. This is useful when 
comparing the results produced by the engine with results produced 
by other software.

Risk
--------------

Now the engine installer includes three web applications previously
only available on the OpenQuake Platform: the Input Preparation
Toolkit (IPT), the Taxonomy Glossary and TaxtWEB. In the
future, such applications will be fully integrated with the QGIS
plugin.

There is a new experimental calculator called `gmf_ebrisk` which is able to
perform an event based risk calculation starting from ground motion fields
provided as a CSV file. The format of the GMFs has to be the same as for
a scenario calculation and requires specifying the parameter
`number_of_ground_motion_fields` in the job.ini. In the future the calculator
will be extended to work with generic ground motion fields, with a different
number of events for each realization.

In order to implement the `gmf_ebrisk` calculator we changed the
CSV export format of the ground motion fields which is
now the same as the input format. Moreover we use the same format
both for event based and scenario calculators. Also the
internal storage of the GMFs has changed to make it more similar
to the input/output format, so that the I/O operations are faster.

We implemented risk statistics for the `classical_damage` calculator
and the `classical_bcr` calculator: before they were missing and the
user had to do the computation manually from the individual realizations.

We implemented the concept of *asset tag* in the exposure — the
risk calculators are now able to compute losses aggregated by tag 
(see [#2943](https://github.com/gem/oq-engine/pull/2943)).
For a definition of the *tag* concept please see the current version
of the manual.

We improved the algorithm used in the calculation of loss curves for both
aggregated and per-asset loss curves. Now the losses are given in terms of
return periods specified in the job configuration file 
(see [#2845](https://github.com/gem/oq-engine/pull/2845)). 
If the return periods are not specified in the configuration file, 
file, the engine automatically generates a sensible range of return
periods. As a consequence, there is no need to specify the 
parameter `loss_ratios` for the asset loss curves, 
or the parameter `loss_curve_resolution` for the aggregate
loss curves in the configuration file as was required by the previous algorithm.

The statistical loss curves exporter for `classical_risk` calculations
was exporting incorrect numbers, even if the data in the datastore were
correct; this has now been fixed. The statistical loss curves exporter for
`event_based_risk` was not implemented; now it has been implemented.

The generation of loss maps and loss curves in event based risk 
calculator has been optimized. Now, this is done in parallel whenever possible.

A better error message is provided now if the user attempts to run a 
risk job in the absence of a preceding valid hazard calculation.

WebUI and QGIS plugin
---------------------

We are visualizing the `calculation_mode` field in the WebUI now,
instead of the `job_type` field, which is less specific.

We removed an excessive check from the WebUI: now if an output exists,
it can be downloaded even if the full calculation was not successful.

Now we show the user the error message in the case of a calculation
that cannot be deleted from the WebUI.

We changed the .npz exporters of the hazard outputs to make the import
into a single QGIS layer easier.

We now have in place an automatic testing mechanism making sure that
all the outputs of the demos that are loadable by the QGIS plugin are
actually imported and visualized correctly. The plugin itself has several
new features, documented [here](https://plugins.qgis.org/plugins/svir/version/2.6.1/).

We started work to make the risk outputs readable from the QGIS
plugin and we will be able to plot some of them in the next release of
the plugin.

oq commands
---------------

We added four new `oq` commands:

- `oq checksum <job_file_or_job_id>` computes a 32 bit checksum for a
   calculation or a set of input files; this is useful to check if a
   given calculation has been really performed with the given input files
   and no parameters have been modified later on
- `oq extract <what> <calc_id>` allows to save a specified output into an
  .hdf5 file
- `oq dump <dump.zip>` allows to dump the database of the engine and all
  the datastores into a single .zip file
- `oq restore <dump.zip> <oqdata>` allows to restore a dump into an empty
  directory.

We added a view `oq show dupl_sources` and enhanced `oq info
job.ini` to display information about duplicated sources; moreover,
some warnings are logged if duplicated sources are found. In the
future we may decide to optimize the engine for this situation; for
the moment (as in the past) the engine is performing twice the same
computation if the same source appears twice in the full source model.

We extended the `oq reset` command to work on multi user
installations.

We renamed `oq engine --version-db` to `oq engine
--db-version`, to avoid confusion between `oq --version` (the version
of the code) and `oq engine --version` (that was returning the version
of the database).

Other
-----

Python 3.6 is not officially supported, however we have fixed the only test
which was breaking and we know that it works. We also fixed some
tests breaking with numpy 1.13 which however is still not officially supported.

We fixed some tests breaking on macOS; the numbers there are slightly
different, since the scientific libraries are compiled differently.
This platform should be trusted less than Linux, that remains our reference.

The engine has now a dependency from [zeromq](http://zeromq.org/) which is
used internally in the DbServer application. In the future zeromq may be
used to manage the task distribution: this would free the engine
from the dependencies from rabbitmq and celery. However, this is a long
term goal, for the year 2018 or later.

We added a 'celery-status' script in 'utils': this is only useful
for users with a cluster.

We added support for Django 1.11, while keeping support for older versions.

We improved our packaging and installation procedures. In particular now
the RPM installer does not override the user `openquake.cfg` with a new
one when performing an upgrade.

A new flag, `split_sources`, can now be set in the job configuration file
By default, this flag is set to `true`. If set to `false`, sources will not 
be split by the engine. This will be useful in the future
when implementing disaggregation by source.

We changed the sampling logic in the event based calculators: this may change
the GMFs generated when `number_of_logic_tree_samples` is nonzero in some
pathological cases, but has no effect at all in realistic cases.

We added an exporter `gmf_scenario/rup-XXX` to export the GMFs generated
by a specific rupture.

Some internal and undocumented exporters for the GMFs in `.txt` format
have been removed.

[Our roadmap for abandoning Python 2](https://github.com/gem/oq-engine/issues/2803) has been updated.
