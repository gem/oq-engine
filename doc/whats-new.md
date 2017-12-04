Release notes for the OpenQuake Engine, version 2.8
===================================================

Several improvements entered in this release, most notably about
the disaggregation calculator and the classical calculator with sampling.
Over 110 issues were closed. For the complete list of changes, please see
the changelog:
https://github.com/gem/oq-engine/blob/engine-2.8/debian/changelog .

Disaggregation
--------------

We changed the algorithm for building the disaggregation bins. The new
algorithm is simpler and depends directly on the integration
distance. The big advantage compared to the past algorithm is that the
bins are always the same across different realizations, therefore it
will be possible to implement statistical disaggregation
outputs, like a mean disaggregation matrix. This is not done yet, but it
is scheduled for future releases.

Thanks to the new algorithm, performing a classical calculation when
`iml_disagg` is set in the `job.ini` file has become redundant:
therefore, such step has been removed. The `iml_disagg` configuration
variable is not documented in the manual, even if it entered 
a long time ago, because it should still be considered experimental.

We have added more checks and validations.  In particular
`intensity_measure_types_and_levels` cannot be set if `iml_disagg` is
set (since it is inferred from it) and `poes_disagg` cannot be set
if `iml_disagg` is set. Moreover, if one or more of the parameters
`mag_bin_width`, `distance_bin_width`, `coordinate_bin_width`,
`num_epsilon_bins` is missing in the `job.ini` file an early error is
raised. There is also an *a posteriori* check when `poes_disagg` is
given, raising a warning if the aggregated poes are too different from
the expected ones (this may happen due to numerical interpolation
errors when the disaggregation intensities are extracted from the
inverse hazard curves).

Since the bins may be different than before and because of other changes
(in particular now a disaggregation calculation may see a smaller logic
tree than before since the reduction of the logic tree feature works better),
having different disaggregation outputs than before is expected. However,
since the internal algorithm implemented in the hazardlib library is
exactly the same as before, in comparable situations (i.e. same bins,
same logic tree) the numbers will be the same as before.

Other Hazard
--------------

The progress on hazard was not limited to the disaggregation
calculator. In particular, there was a crucial progress on the
classical calculator in presence of sampling: we found a performance
issue affecting calculations with an extra large GSIM logic tree (case
in point: the India model, with 245,760 realizations). Now the engine
is not stuck anymore while sampling the logic tree. In regular cases
(i.e. if your model has less than 245,760 GSIM realizations) you will
not see any performance difference, but you will still see that the
produced numbers are different than in previous versions of the
engine, since we changed the sampling algorithm and the way the
realization weights are managed. This is akin to a change of seed: the
really significant quantities will not change.

A lot of refactoring went into the logic tree code; as a consequence
the data transfer in the realization objects has been reduced.

We fixed and documented in the manual the magnitude-distance filtering
which now has become an official feature of the engine.

We changed the HDF5 format for hazard curves and maps, when exported
via the command `oq extract hazard/rlzs`: now it is friendlier than
before.  The old format is still available via the command `oq extract
qgis-hazard/rlzs`; the name reflects the fact that it is meant to be
used by the QGIS plugin via the REST API.

We improved the task distribution in large hazard calculations by
improving the filtering of MultiPointSources.

There has been some work also on hazardlib, in particular on the GMPEs
for the SGS model.

Risk
----

For what concerns risk, we continued the work on the risk outputs initiated
a few releases ago. In particular, we removed all the outputs that were
deprecated in engine 2.7, since they can be generated dynamically with
extraction commands, the REST API or via the QGIS plugin.
Moreover some bugs in the outputs were fixed. In particular now 
the average losses for `classical_risk` are exposed to the engine
(before they were computed but not visible from the engine database);
same for the `loss_curves-stats` and `loss_maps-stats`. The command
`oq export loss_curves` has been fixed. A rare ordering error happening in the
classical_bcr calculator has been fixed.

The parameter `number_of_ground_motion_fields` is optional again in
all calculators reading the GMFs from an external file (in engine 2.7
it was mandatory in some cases).
We fixed several bugs in the new and still experimental calculator
`gmf_ebrisk`. We added more validation tests to the input GMFs file
in .csv format, and better error messages. In particular now there are good
error messages if the user forgets sites and sites.csv in the job.ini,
if the user sets a wrong site_id in the sites.csv file,
if the user specifies a non-existing file in the job.ini, if the user
sets `conditional_loss_poes` but forget to set `asset_loss_table`,
if the user forget the source_model_logic_tree file or if the user forgets
the `--hc` option in calculations that require it.

Other
--------------

There are two new `oq` command: `oq abort <calc_id>` to kill a running job
and `oq zip <job.ini> <archive.zip>` to collect all the files relevant for
a calculation in a single zip archive. This is crucial for users that
have troubles with a specific calculation and want to send use their
input files for help in debugging the issue.

`oq dbserver stop` has been extended to stop also the zmq workers,
if the zmq distribution is used.

Now the WebUI starts new jobs in separate processes, thus achieving true
parallelism: before it was possible to launch only one job at the time.
Each job has a process name of the form `oq-job-<calc_id>`, so it is
easy to find and kill jobs from the task manager. Similarly, the dbserver
process is now called `oq-dbserver` and the workers processes are called
`oq-worker`. 

We fixed some bugs when reading `openquake.cfg` for a Python virtual
environment.

`oq engine --run archive.zip` now works with Python 3 too.

Deprecations/removals
----------------------

In this release we deprecated the `.geojson` exporters for hazard curves
and maps. In the next release they will be removed. Hazard curves and maps
should be exported in .csv or .hdf5 format, or even read programmatically
from the datastore.

We removed the deprecated risk outputs `dmg_by_tag`, `dmg_total`
`losses_by_tag` and `losses_total`.  We removed the obsolete parameter
`loss_curve_resolution` which has not been used for a few releases.

We removed the method `gsim.disaggregate_poe`, but the main hazardlib
disaggregation utility, `openquake.hazardlib.calc.disagg.disaggregation`
still works as before, it is just faster.

Python 2 decommissioning
------------------------

[We completed phase 1 of our roadmap for abandoning Python 2](https://github.com/gem/oq-engine/issues/2803). In
short, even if the engine still supports Python 2.7 and you can use
it by installing from sources, we only provides installers with
Python 3.5 for Windows, macOS and Linux. The
official Ubuntu and Red Had packages are still using Python 2.7, but they
will replaced by Python 3.5 in phase 2 of the roadmap. Next year the
engine will be Python 3 only. The time to migrate is now!
