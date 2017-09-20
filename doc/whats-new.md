Release notes for the OpenQuake Engine, version 2.6
===================================================

Several new features where introduced in this release. Several bugs
were fixed, some outputs were changed and there were a few
improvements to the installers, to the Web User Interface(WebUI) and
to the engine itself.

More than 130 pull requests were closed. For the complete list of
changes, please see the changelog:
and https://github.com/gem/oq-engine/blob/engine-2.5/debian/changelog.

Hazard
---------------

We changed the source weighting algorithm, which is now proportional to the
the number of affected sites. The net effect is a best task distribution,
so some calculations dominated by slow tasks are faster than before.

We fixed a few bugs in the hazard exporters; moreover we have now an
experimental command `oq extract hazard/rlzs` solves the problem of
generating a single .hdf5 file with all hazard curves, maps and
uniform hazard spectra for all realizations; this was requested by
some power users and it is documented in
https://github.com/gem/oq-engine/blob/master/doc/oq-commands.md

In hazardlib we implemented the Munson and Thurber 1997 (Volcanic)
GMPE and XXX.  The CoeffsTable was enhances so that it can be
instantiated with dictionaries as well as strings.

We also fixed some small bugs (one in the Hazard Modeller Toolkit,
one in the script `correct_complex_sources.py`) and added a few additional
checks.

If there are multiple realizations and no hazard stats,
it is an error to set `hazard_maps=true` or `uniform_hazard_spectra=true`,
because there will be no output (now we only export the statistics).
There is also a check that the number of intensity measure types when
generating uniform hazard spectra is greater than one.

We extended the `sz` field in the rupture surface to 2 bytes, making it
possible to use a smaller mesh spacing;

We fixed a bug when computing the rjb distances with multidimensional
meshes, which could be important for hazardlib users, but not for engine
users.

Risk
--------------

Now the engine installer includes three web applications previously
only available on the OpenQuake Platform: the Input Preparation
Toolkit (IPT), the Taxonomy Glossary application and TaxtWEB. This
means that they are available in the desktop too. In the future such
applications will be fully integrated with the QGIS plugin.

There is a new experimental calculator called `gmf_ebrisk` which is able to
perform an event based risk calculation starting from ground motion fields
provided as a CSV file. In order to implement this feature we changed the
CSV export format of the ground motion fields which is
now the same both for event based and scenario calculators. Also the
internal storage of the GMFs has changed to make the import/export
procedure simpler.

We implemented risk statistics for the `classical_damage` calculator
and the `classical_bcr` calculator: before they were missing and the
user had to do the computation manually from the outputs by realization.

We implemented the concept of *asset tag* in the exposure. The
risk calculators are able to compute losses aggregated by tag now.
This is documented in the current version of the manual.

There is a better error message when running a risk file in absence of a
preceding hazard calculation.

The statistical loss curves exporter for `classical_risk` calculation
was exporting bogus numbers, even if the data in the datastore were
correct. This has been fixed.

We optimized the generation of loss_maps and curves in event based risk: now it
is done in parallel whenever possible.

We changed the algorithm used in the calculation of loss curves (both
aggregated and per-asset curves). Now the losses are given in terms of
return periods. If the return periods are not specified in the `job.ini`
file, the engine automatically generates a sensible range of return
periods. There is not need to specify the `loss_ratios` in the `job.ini`
file as it was required by the previous algorithm.

We are also working on the QGIS plugin side to be able to plot easily
the loss curves in terms of return periods, and this will probably be
ready for the next release.

WebUI and QGIS plugin
---------------------

We are visualizing the `calculation_mode` field in the WebUI now,
instead of the `job_type` field, which is less specific and interesting.

We removed an excessive check from the WebUI: now if an output exists,
it can be downloaded even if the calculation was not successful.

Now we show the user the error message in the case of a calculation
that cannot be deleted from the WebUI.

We changed the .npz exporters of the hazard outputs to make the import
into a single QGIS layer easier.

We have now in place an automatic testing mechanism making sure that
all the outputs of the demos are loadable by the QGIS plugin. The
plugin itself has a lot more features, documented *here*.

oq commands
---------------

We added four new `oq` commands:

- `oq checksum <job_file_or_job_id>` computes a 32 bit checksum for a
   calculation or a set of input files; this is useful to check if a
   given calculation has been really performed with the given input files
   and no parameters have been modified later;
- `oq extract <what> <calc_id>` allows to save a specified output into an
  .hdf5 file
- `oq dump <dump.zip>` allows to dump the database of the engine and all
  the datastores into a single .zip file
- `oq restore <dump.zip> <oqdata>` allows to restore a dump into an empty
  directory.

We added a view `oq show dupl_sources` and enhanced `oq info
job.ini` to display information about the duplicated sources; moreover,
some warnings are logged if duplicated sources are found. In the
future we may decide to optimize the engine for this situation; for
the moment (as in the past) the engine is performing twice the same
computation if the same source appears twice in the full source model.

Moreover we extended the `oq reset` command to work on multi user
installations. Finally, we renamed `oq engine --version-db` to `oq engine
--db-version`, to avoid confusion between `oq --version` (the version
of the code) and `oq engine -version` (that was returning the version
of the database).

Other
-----

We changed the 'CTRL-C' behaviour to make sure that all children
processes are killed when a calculation is interrupted.

Python 3.6 is not officially supported, however we have fixed the only test
which was breaking and we know for sure that it works. We also fixed some
tests breaking with numpy 1.13 which however is still not officially supported.

We fixed some tests breaking on macOS; the numbers there are slightly
different, since the scientific libraries are compiled differently.
This platform should be trusted less than Linux and Windows.

The engine has now a dependency from [zeromq](http://zeromq.org/) which is
used internally in the DbServer application. In the future zeromq maybe
used also to manage the task distribution: this would mean freeing the engine
from the dependencies from rabbitmq and celery. However, this is a long
term goal, for the year 2018 or later.

Internals
---------

As always, there were several internal changes to the engine. Some of
them may be of interests to power users and people developing with the
engine.
We added a 'celery-status' script in 'utils': this is only useful
for users with a cluster.

We added support for Django 1.11, while keeping support for older versions.

We steadily improved our packaging and installation procedures.

We added a flag `split_sources` in the job.ini, which by default is false.
When set, sources are not split anymore. This will be useful in the future
when implementing disaggregation by source.

We changed the sampling logic in the event based calculators: this may change
the GMFs generated when `number_of_logic_tree_samples` is nonzero in some
pathological cases, but has not effect at all in realistic case.

We added an exporter `gmf_scenario/rup-XXX` to export the GMFs generated
by a specific rupture.

Some internal and undocumented exporters for the GMFs in `.txt` format
have been removed.

We fixed the database migration procedure which is now transactional again.

[Our roadmap for abandoning Python 2](https://github.com/gem/oq-engine/issues/2803) has been updated.
