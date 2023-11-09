Release notes for the OpenQuake Engine, version 3.8
===================================================

This is a major release featuring several optimizations, new features and bug
fixes: around 285 pull requests were merged.

For the complete list of changes, see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.8/debian/changelog

## Major optimizations

Classical calculations dominated by point sources with non-trivial
nodal plane / hypocenter distributions and using the
`pointsource_distance` approximation (see
https://github.com/gem/oq-engine/blob/engine-3.8/doc/adv-manual/common-mistakes.rst#pointsource_distance)
have been optimized. The improvement applies to several models, and in
particular the once extra-slow Canada and Australia national hazard
calculations are now 2-3× faster.

Large ebrisk calculations has been substantially optimized in
memory occupation, particularly when generating aggregate loss curves
for a large numbers of tags. The gain can be of orders of
magnitude. This was made possible by storing the (partial) asset loss
table (see
https://github.com/gem/oq-engine/blob/engine-3.8/doc/adv-manual/risk.rst#the-asset-loss-table)
and by computing the loss curves in post-processing.

In general the memory occupation of the engine in calculations with subtasks
(i.e. classical and ebrisk) has gone down, since we
discovered that more data than needed was accidentally transferred
and the issue has been fixed resulting
in a substantial improvement (like from 120 GB to 30 GB of RAM used in
the master node for the Australia calculation).

The task distribution, has been substantially changed and
improved. Now we are back to an algorithm that makes the number of
generated tasks deterministic, while in engine 3.6 and 3.7 the number was
dependent on the load on the server. The difficult part was to make
this possible without incurring in the slow task penalty and actually
we managed to improve on that front too. Moreover, differently from
engine 3.7, now the engine will try to submit all tasks upfront,
unless the parameter `num_cores` is set in the `job.ini` file.

## Other optimizations

We reduced the data transfer in classical and event based calculations
by reading the site collection instead of transferring it, thus fixing
a (minor) regression temporarily introduced in engine 3.7.

We were parsing the gsim logic tree file (and the underlying files, if any)
multiple times; this has been fixed.

We changed the seed algorithm used when sampling the source models to
avoid using more GMPEs than needed in some cases. Due to this change,
if there is more than one source model you could get different numbers
with respect to engine 3.7, but this is a non-issue. We also changed
the logic tree sampling algorithm by ordering the branchsets
lexicographically by tectonic region type. This can also affect the
numbers but, again, it is akin to a change of seed and therefore a
non-issue.

We reduced the memory footprint in event based and ebrisk
calculations by reading one rupture at the time in the worker nodes,
instead of a bunch of ruptures. Moreover the rupture prefiltering mechanism
has been greatly optimized by using a KDTree approach and by removing
the need for prefiltering the ruptures twice.

We optimized the computation of PointSources in the case when only the rjb
distance is required: then the hypocenter distribution can be collapsed.

Some models (like the Canada model 2015) may have duplicated values
in the nodal plane or hypocenter distributions, causing the calculation
to become slower. This has been fixed and now the engine automatically
regularizes the nodal plane and hypocenter distributions, by printing
a warning.

## New features

We extended the framework to compute consequences from scenario
damage calculations. Any kind of consequence can be
computed by adding a custom plugin function, even if at the moment the only
plugin function included in the engine is the one to compute economic
losses. We will add more plugins in the near future.

We changed the format for the consequence file, which now can be a
simple CSV file with the coefficients per each damage state per each
loss type per each tag name per each plugin function (see
https://github.com/gem/oq-engine/blob/engine-3.8/doc/adv-manual/risk-features.rst
for an explanation).

There is a new experimental calculator `event_based_damage` which is
able to compute damage probabilities starting from an event based hazard
calculation and a set of fragility curves. Essentially, it is a
generalization of the `scenario_damage` calculator to the case of
multiple ruptures. The calculator is also able to compute extended consequences
from the damage probabilities. The work is in progress and the calculator will
likely be extended and improved in the future; if you are interested in
become beta testers, please let us know.

There is an experimental way to serialize ruptures in text
files (`oq extract rupture/<rup_id> <calc_id>`) but it has been left
undocumented on purpose since it will likely change.
Scenario calculators can read a rupture exported in the new format,
so it is already possible to run an event based
calculation, extract interesting ruptures and then perform scenarios
on those. The challenge is to make this work across different versions
of the engine and this is why it is still in experimental status.
Beta testers are welcome.

We extended the disaggregation calculator so that it can work with
multiple realizations at once, provided the user specifies
the `rlz_index` or the `num_rlzs_disagg` parameters in the job.ini.
This is useful in order to assess the variability of the disaggregation
results depending on the chosen realizations. Beta testers are welcome.

We revised the logic to manage GMPE depending on an external file - like
the commonly used `GMPETable` which depends on an .hdf5 file - and
introduced a naming convention: now GMPE arguments ending in `_file`
or `_table` as considered path names relative to the `gsim_logic_tree`
file and are automagically converted into absolute path names.
Moreover the GMPE logic tree is properly saved in the datastore,
including the external files, so that a calculation can be copied
to a different machine without losing information (before this was
implemented in a hackish way working only for .hdf5 tables).

Finally we added a mechanism to override the `job.ini` parameters from
the command line; here is an example overriding the `export_dir`
parameter:
```bash
  $ oq engine --run job.ini --exports csv --param export_dir=/my/output/dir
```

## Work on hazardlib

[G. Weatherill](https://github.com/g-weatherill) added a configurable nonergodic option to BC Hydro and
SERA GMPEs. Moreover he revised the SERA BCHydro Epistemic GMPES,
updated the SERA craton GMPE coefficients, added a fix to the Kotha
2019 GMPE, and implemented Abrahamson et al. (2018) "BC Hydro Update"
GMPE.

[M. Pagani](https://github.com/mmpagani) added some of the Morikawa-Fujiwara GMPEs for Japan.
Moreover he added an alternative way controlling the way the OQ Engine
models hypocenters in distributed seismicity (see
https://github.com/gem/oq-engine/pull/5209). In order to use this option,
the user must set in the .ini file `shift_hypo = true`.

[R. Gee](https://github.com/rcgee) fixed the `CampbellBozorgnia2003NSHMP2007` GMPEs which was
missing the line `DEFINED_FOR_REFERENCE_VELOCITY= 760`. This affected
the latest Alaska model that could not be run.

[M. Simionato](https://github.com/micheles) introduced a geometric average GMPE called
`AvgGMPE` which is able to compute the geometric average of its underlying
GMPEs, with the proper weights. It can be used to collapse the GMPE logic
tree, for users wanting to do so. This can reduce the size of the generated
GMFs by orders on the magnitude, depending on the size of the
GMPE logic tree.

Finally, we cached the method `CoeffsTable.__getitem__` to avoiding excessive
interpolation.  The issue was visible if the `CoeffsTable` was
instantiated inside the method `get_mean_and_stddevs`, which is a very
bad idea performance-wise. Now we have added a check to forbid such
instantiation. The right place where to instantiate the `CoeffsTable` is
inside the `__init__` method of the GMPE.

## Changes in the inputs

In the `job.ini` file we recommend to use the names `mean` and `quantiles`
instead of old names `mean_hazard_curves` and `quantile_hazard_curves`. The old
names still work and will always work for backward compatibility, but the
new names are better since the calculation of statistics applies also to
other outputs and not only to the hazard curves.

In the `job.ini` we changed the syntax for the `RepiEquivalent` feature, see
https://github.com/gem/oq-engine/blob/engine-3.8/doc/adv-manual/equivalent-distance-approximation.rst#equivalent-epicenter-distance-approximation
The old syntax is still working but it raises a deprecation warning.

The GMF importer in CSV format has been extended, and it can import
files with more IMTs than the ones used in the calculation: they are
simply imported and then ignored, without raising an exception.

## Changes in the outputs

We harmonized the headers in the CSV files exported from the engine.
In particular we renamed rlzi -> rlz_id, ordinal -> rlz_id, asset ->
asset_id, id -> asset_id, rupid -> rup_id, id -> event_id in various
files (there were plenty of such inconsistencies for historical reasons).

We fixed the order when exporting the ruptures in CSV: this is very
useful when comparing the results of two calculations with different
parameters. The order is now by rupture ID, `rup_id`.

We fixed the CSV exporter for the ruptures, since the boundary
information was truncated at 100 characters. Actually, we completely
rewrote it and now the information is extracted via the
`/extract/rupture_info` in a very efficient way, because the WKT is
gzipped, with a reduction in the data transfer up to 100x. 

The QGIS plugin has been updated to use the new API which has been
extended to accept a `min_mag` parameter to filter out the small
magnitudes and reduce substantially the download time.

We deprecated the XML exporter for the ruptures, since it is extremely
verbose and inefficient. In the future we will replace it with a better
solution. For the moment you can still use it or, better, you can use
the `/extract/rupture_info` binary API.

In `ebrisk` calculations we have clearly split the outputs aggregated
by tag from the total outputs: the new names are 'Aggregate
Losses/Aggregate Loss Curves', and 'Total Losses/Total Loss Curves'
respectively. This avoids a lot of confusion, because in the past the
total loss curves where are also called aggregate.  The total outputs
are computed from the event loss table while the aggregate outputs are
computed from the asset loss table. We have also removed the outputs
`agg_maps-rlzs` and `agg_maps-stats` that were only accidentally
exported in engine 3.7.

## Bug fixes

We fixed the ShakeMap download to support again ShakeMaps in zipped format,
a regression accidentally introduced in engine 3.7.1.

We fixed an issue of quotes in the exposure tags.

We fixed a long standing issue with NaNs in `scenario_damage` calculations:
the cause was a missing `noDamageLimit` in the fragility files. Now a
missing `noDamageLimit` is treated as zero.

We fixed a SWMR bug in the disaggregation calculator, happening some times
with large calculations and giving mysterious read errors.

The GMFs were stored even with `ground_motion_fields=false` in case of
`hazard_curves_from_gmfs=true`. This has been fixed.

The removal of calculations that was not working since it was
trying to delete obsolete and non-existing files has now been fixed.
We also fixed the command `oq reset` when used with a stopped DbServer.

We hard-coded the distance used in the filtering to `rrup`, to simplify
the logic and to avoid an error in disaggregation with GMPEs not using
`rrup` (the distance was not saved but needed, thus causing a failure).

We fixed a bug in `ebrisk` with `aggregate_by` when building the
`rup_loss_table`.

One of our users discovered a RecursionError when pickling Python
objects in a disaggregation calculation:

```python
  pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
  RecursionError: maximum recursion depth exceeded while calling a Python object
```
We temporarily fixed this by raising the recursion limit, but let us know if you get
the same error (it should appear only in extra-large calculations).

The error message for pickling over the 4 GB limit is now sent back
to the controller node instead of appearing only in the worker logs.

## New checks

We relaxed a check that was too string on the `minimum_intensity` parameter
of the previous calculation.

We relaxed the check on IMT-dependent weights: now in case of sampling the
IMT-dependent weights are ignored and the engine prints a warning, but does
not stop.

We added a check on acceptable input keys in `the job.ini` to protect against
mispellings like `esposure_file` instead of `exposure_file`.

We added a warning against implicit hazard levels, extracted from the
risk functions. In the future specifying explicitly the hazard levels
will become mandatory.

We added a check for duplicated sites in the site model. This typically
happens when the user supplies more than 5 digits for the geographic
coordinates, while the engine truncate to 5 digits (1 meter resolution)
and then sites that looks different becomes duplicated. In turn, this
may cause wrong asset associations and produce completely bogus numbers
in the final results.

There is now an error *You are specifying grid and sites at the same time:
which one do you want?* to force users to be explicit with their input files.
Moreover, setting both `hazard_curves.csv` and `site_model.csv` is an error
and it is correctly flagged so.

On the other hand, speciying both sites and site models at the same time
is now valid again and the "sites overdetermined" check has been removed.

Trying to read a GMFs file in XML format, a feature which had been
removed long ago, now raises a clear error message.

There is a new upper limit on the size of event based calculations, to
stop people from trying to run impossibly large calculations. You will
get an error if the number of sites times the number of events is larger
than the parameter `max_potential_gmfs` which has a default value of 2E11.

We improved the error message when using precomputed gmfs in scenarios
with `event_id` not starting from zero.

We improved the error message for empty risk EB calculations: now you
will get *There are no GMFs available: perhaps you set
ground_motion_fields=False or a large minimum_intensity*.

## WebUI and WebAPI

As usual, we worked on the WebAPI to better support the
QGIS plugin; in particular it is now possible to extract a specific
ground motion field by specifying the ID of the event generating it
and by calling the URL `/v1/calc/ID/extract/gmf_data?event_id=XXX`.

It is also possible to extract the total number of events with a call
to `/v1/calc/ID/extract/num_events`.

The call to `/v1/calc/ID/status` now correctly returns an HTTP error
404 for non-existing calculations.

We now store the WKT representation of each source geometry and we
added an endpoint `/extract/source_info?sm_id=0` to get that information.

We added an endpoint `/v1/calc/validate_zip` for use in the Input
Preparation Toolkit, to validate the input files.

When using access control in the WebUI we changed the default `ACL_ON = True`
to False, thus making it possible to export results from calculations
ran by other users, if the calculation ID is known.

Finally, Django has been upgraded to the version 2.2.

## IT

The `zmq` mechanism, which has been in experimental stage
for years, has finally been promoted to *production ready*: both of our clusters
use it. The celery/rabbitmq distribution mechanism is not deprecated yet,
but eventually it will be, because `zmq` is a superior alternative, using
less memory and being more efficient, as well as having no dependency
from Erlang.

The engine distribution now includes pandas, a feature much
requested by our users. There is also some support for converting datasets
in the datastore into pandas DataFrames. The goal is to make it easy
to postprocess the engine results with pandas. For instance the portfolio
loss curves in event based risk calculations are now computed with pandas.

We introduced support for RHEL and CentOS 8, which is also used for our
Docker images.

We improved the Windows distribution that now can be
used also to migrate to a development installation from a nightly
release.

Alberto Chiusole made the point that the engine should report the
number of available cores, not the number of real cores, since they
are not necessarily the same in a container. We fixed that on
Linux by using the cpu_affinity function (not available on macOS).

Some internal commands (in particular `oq show performance`,
`oq show task_info` and `oq show job_info`) have been fixed,
changed or enhanced, so that they now return more correct
information. After two years we are finally back to a situation
where they can be called on a running calculation, thanks
to the usage of the SWMR mode in the HDF5 libraries.
