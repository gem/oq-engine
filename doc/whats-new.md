Release notes for the OpenQuake Engine, version 2.6
===================================================

Several new features where introduced in this release. Several bugs
were fixed, some outputs were changed and there were a few
improvements to the installers, to the Web User Interface(WebUI) and
to the engine itself.

More than 100 pull requests were closed. For the complete list of
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
one in the script `correct_complex_sources.py`) and added an additional
check: if there are multiple realizations and no hazard stats,
it is an error to set `hazard_maps=true` or `uniform_hazard_spectra=true`,
because there will be no output (now only export the statistics).
We extended the `sz` field in the rupture surface to 2 bytes, making it
possible to use a smaller mesh spacing;
We fixed a bug when computing the rjb distances with multidimensional meshes.

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

WebUI
-----

We are visualizing the `calculation_mode` field in the WebUI now,
instead of the `job_type` field, which is less specific and interesting.

We removed an excessive check from the WebUI: now if an output exists,
it can be downloaded even if the calculation was not successful.

Now we show the user the error message in the case of a calculation
that cannot be deleted from the WebUI.

Fixed a bug introduced by a change in Django 1.10 that was causing
the HTTP requests log to be caught by our logging system and
then saved in the DbServer.


Infrastructure
---------------

- Added support for Django 1.11
- Added the 'celery-status' script in 'utils'

Renamed `oq engine --version-db` to `oq engine --db-version`, to avoid
confusion between `oq --version` (the version of the code) and
`oq engine -version` (that was returning the version of the database)/

We extended the `oq reset` command to work on multi user installations

We added three new `oq` commands:

- `oq extract <what> <calc_id>` allows to save a specified output into an
  .hdf5 file
- `oq dump <dump.zip>` allows to dump the database of the engine and all
  the datastores into a single .zip file
- `oq restore <dump.zip> <oqdata>` allows to restore a dump into an empty
  directory

We changed the 'CTRL-C' behaviour to make sure that all children
processes are killed when a calculation is interrupted.
  

-- changes
Optimized the generation of loss_maps in event based risk: now it is done in parallel, except when reading the loss ratios
Replaced the agg_curve outputs with losses by return period outputs

--- bugs


--- new checks

Added a check that on the number of intensity measure types when
generating uniform hazard spectra (must be > 1)

Internals
---------

As always, there were several internal changes to the engine. Some of
them may be of interests to power users and people developing with the
engine.

Added a command `oq show dupl_sources` and enhanced `oq info job.ini`
to display information about the duplicated sources; also added some
warnings if duplicated sources are found. In the future we may decide
to optimize the engine for this situation; for the moment is doing
(as always) twice the needed computation if the same source appears
twice in the full source model.

We added a flag `split_sources` in the job.ini, which by default is false.
When set, sources are not split anymore. This will be useful in the future
when implementing disaggregation by source.

Turned the DbServer into a multi-threaded server
Used zmq in the DbServer
Extended the demo LogicTreeCase1ClassicalPSHA to two IMTs and points
Removed the automatic gunzip functionality and added an automatic
checksum functionality plus an `oq checksum` command

We changed the sampling logic in the event based calculators: this may change
the GMFs generated when `number_of_logic_tree_samples` is nonzero in some
pathological cases, but has not effect at all in realistic case.

We added an exporter `gmf_scenario/rup-XXX` to export the GMFs generated
by a specific rupture.

[Our roadmap for abandoning Python 2](https://github.com/gem/oq-engine/issues/2803) has been updated.
