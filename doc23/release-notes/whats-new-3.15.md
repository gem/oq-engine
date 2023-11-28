Release notes for the OpenQuake Engine, version 3.15
====================================================

The release 3.15 is the result of 5 months of work involving nearly
320 pull requests, featuring many significant optimizations and new features.

The complete list of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.15/debian/changelog

## Classical PSHA

The major highlight of the release is an optimization of point-like
sources resulting in a speedup from 1.5 to 50 times, measured on various
hazard models dominated by point-like sources. The speedup is especially
large for single site calculations. It was obtained by using
different optimizations, including a careful allocation of the arrays
and writing numba-accelerated code for
building the planar surfaces and computing the distances.

We reduced the memory consumption in the context objects, thus
solving an out of memory issue in UCERF calculations.

We improved the `ps_grid_spacing` approximation which
is now more precise. Setting the `ps_grid_spacing` parameter
now sets the `pointsource_distance` parameter too and this the
recommended way to use the feature.

We fixed a bug occuring when the grid produced by the
`ps_grid_spacing` approximation degenerates to a line, by simply not
collapsing the sources in that case.

The preclassical calculator has been optimized resulting in a 2-3x speedup
in many models. We also improved the weighting algorithm by taking into
account the number of GMPEs per tectonic region type and thus solving a
slow task issue affecting the ESHM20 model.

At user request, we made it possible to filter the ruptures of a model
by magnitude range. The way to do it is to use a magnitude-dependent
`maximum_distance`.  For instance using

  `maximum_distance = [(5.5, 70), (6, 100), (6.5, 150), (7, 200), (8, 250)]`

will discard magnitudes < 5.5 and > 8. This is semantic change with respect
to the past where outside magnitudes were not discarded.

There was a major (but internal) change to the way ruptures are stored in
classical calculations with few sites. Now we store context objects rather
than ruptures. The command `oq compare rups` has been changed accordingly,
as well as the disaggregation and conditional spectrum calculators.

The change made it possible a performance improvement in
disaggregation calculations and paved the way for disaggregation by
rupture, since now reproducible rupture
IDs are stored in the context arrays.

There was a lot of effort on the `disagg_by_src` functionality, which
has been extended to mutually exclusive sources (used in the Japan
model) and has some new features documented here:
https://docs.openquake.org/oq-engine/advanced/classical_PSHA.html#disagg-by-src

The storing of the `disagg_by_src` array is much more efficient and
there is a consistency check with the mean hazard curves which is
always enabled.

Finally, we removed a logging statement that could cause an out of
memory in some calculations: thanks to Chris Chamberlain of
GNS-Science for discovering the issue.

## Disaggregation

The disaggregation calculator was failing when a tectonic region type
had a single magnitude, or when, due to rounding issues, incorrect
magnitude bins were generated. Both issues have been fixed and we also
changed the calculator to automatically discard non-contributing
tectonic region types.

The calculator has been extended to work with mutually exclusive
sources and now it is possible to perform disaggregations of the Japan
model.

There is a new feature called `epsilon_star` disaggregation (in the
sense of the PEER report
https://peer.berkeley.edu/sites/default/files/2018_03_hale_final_8.13.18.pdf).
For examples of use see the tests in `qa_tests_data/disagg` from `case_8`
to `case_12`.

In some models with nonParametric/multiFaultSources the calculators
was returning spurious NaNs: this has been fixed.

lon,lat disaggregation with multiFaultSources was giving incorrect results:
it has been fixed now.

Finally, Anne Hulsey from GNS New Zealand contributed two new kinds of
disaggregation: `Mag_Dist_TRT` and `Mag_Dist_TRT_Eps`.

## Hazard sources

There were several changes in multi fault sources and a few bugs were
fixed while implementing the New Zealand model.  As a new feature the
SourceWriter writes multi-fault sources in HDF5 format rather than
XML, thus drastically speeding up the reading time (by 3,600 times in the
UCERF3 model). The data transfer in multi-fault sources has been
drastically reduced too.


Sources have been extended to support parametric temporal occurrence
models in their XML representation. We also have a way to serialize
parametric temporal occurrence models inside the datastore. Thanks to
such features the engine can now manage the **negative binomial temporal
occurrence model** contributed by Pablo Iturrieta and used in the latest
New Zealand model.

We added a check on sum(srcs_weights) == 1 for mutually exclusive sources
that was missing.

We fixed a bug in `upgrade_nrml` when converting point sources with
varying seismogenic depths into multipoint sources.

We changed the sourcewriter to round the coordinates to 4 digits after
the decimal point. This helps in limiting the platform dependencies,
since in general when the precision is not specified the XML generated
on a Mac with M1 processor is different from the XML generated on a
Linux/Windows Intel machine.

## hazardlib

Tom Son contributed a bug fix to the Chiou & Youngs 2014 model: the
Spectral Acceleration at T ≤ 0.3s was not being set correctly.
He also added `ztor`, `width` and `hypo_depth` estimations to the
Campbell and Bozorgnia (2014) model and suggested to add the z1pt0
parameter to the `REQUIRES_SITES_PARAMETERS` in the Boore (2014)
model. He also improved the performance of Kuehn et al. (2020).

Julián Santiago Montejo Espitia contributed the Arteta et al. (2021) GMPE.

The Hassani and Atkinson (2018) GMPE has been added to hazardlib.

The Bahrampouri (2021) Arias Intensity GMPE with region-specific
coefficients `Cm` and `Ck` has been added. Notice that the performance is
expected to be poor since a geospatial query is performed for each rupture.

We implemented a parametric Magnitude Scaling Relationship
called `CScalingMSR` for use in the New Zealand model.

We avoided building multiple times the same polygons in the Bradley (2013)
model.

We now raise a clear error when passing a string instead of an IMT to
the legacy method `get_mean_and_stddevs`.

We added a check for missing mags when calling the class GMPETable incorrectly
from hazardlib and we added a property `GMPETable.filename`.

## Risk

We added some restrictions on the risk IDs (they must be printable
ASCII characters excluding #'"); further restrictions may be added
in the future.

We added a check for inconsistent IDs between fragility and consequence
functions.

We added a warning for missing risk IDs, such as
an ID present in the `structural_vulnerability` file and missing in the
`occupants_vulnerability` file.

We changed the internal serialization of risk
functions in the datastore, as well as the storage of `agg_curves-stats`,
`src_loss_table` and `avg_losses`: this is part of a large project to
manage secondary generic secondary loss types.

At the moment the only kinds of secondary loss type implemented
are insured losses (which have been reimplemented) and total losses
(brand new). You can find examples in the event based risk tests,
but essentially it is possible to write in the job.ini something like

`total_losses = structural+contents`

or

`total_losses = structural+nonstructural+contents`

and have the new loss type pop up in the CSV outputs as a new column.
This is especially useful for computing total loss curves, or in
situations were the insurance is based on the total losses obtained by
summing different loss types.

The event based risk calculator has been refactored with some speedup
(a few percent).

Thanks to Astha Poudel and [Anirudh Rao](https://github.com/raoanirudh), 
an experimental module to assess linear infrastructure risk 
[connectivity.py](https://github.com/gem/oq-engine/blob/engine-3.15/openquake/risklib/connectivity.py)
has been added to the engine. Common metrics to measure network connectivity
loss are automatically computed for scenario_damage calculations or 
event_based_damage calculations with an exposure containing the nodes and 
links/edges describing an infrastructure network. While detailed 
documentation for the module will be added once it graduates from
the experimental stage, a working example for a water supply system
with the scenario_damage calculator can be found in the QA tests directory: 
[scenario_damage/case_15](https://github.com/gem/oq-engine/tree/engine-3.15/openquake/qa_tests_data/scenario_damage/case_15)


The `aggrisk` output, that was experimental in previous version
of the engine, has been finalized. Now it is consistent with the
sum of the average losses even for event based calculations and some
spurious warnings about `agg_losses != sum(avg_losses)`
(happening in some situations) have been removed.

In presence of an exposure, a `custom_site_id` field is automatically
added to the site collection, if not present already. It is computed
as a geohash 8-characters long and it is meant for debugging purposes.

## oq commands

The command `oq download_shakemap` has been replaced with a command
`oq shakemap2gmfs` which is able to convert a ShakeMap coming from
the USGS site into a set of ground motion fields suitable for scenario
risk or damage calculations.

We added a command `oq dbserver upgrade` to create/upgrade the schema of the
engine database without starting the DbServer. This is used in the
universal installer.

We added a command `oq compare risk_by_event` to compare event loss tables.
It raises an error if the GMFs are not compatible.

We extended the command `oq engine` with and option `--sample-sources`
to reduce large calculations by sampling the source model (useful for
debugging).

## Bug fixes and new checks

A bug in event based calculations, where far away ruptures coming from
multi fault sources were needlessly stored, has been fixed.

When using the command `oq engine --run job.ini --exports=csv` the
`realizations.csv` output was not being exported. This is now fixed.

`get_composite_source_model(oqparam)` was raising an error in some cases:
this has been fixed.

The counting of the logic tree paths (`.num_paths`)
was incorrect in some situations and has been fixed.
Moreover we raised the limit on the number of branches to 183.

The simplified logic tree implementation in the module hazardlib.lt
has been fixed and documented in the advanced manual:

https://docs.openquake.org/oq-engine/advanced/logic_trees.html

We added a check for missing site parameters, for instance when
accidentally passing a `sites.csv` file instead of a `site_model.csv` file.

We added a warning when starting from an calculation computed with an
old version of the engine.

We added a warning for missing IMTs in ShakeMaps.

When using the `--hc` options extra fields of the site collection, such as
the `custom_site_id` were lost: this is now fixed.

## Installer and dependencies

Python 3.7 is officially deprecated and the next version of the engine will
require Python 3.8, 3.9 or 3.10 to run.

The universal installer now officially supports the M1 processor with Python 3.9
(see https://github.com/gem/oq-engine/blob/engine-3.15/doc/installing/universal.md)
and Ubuntu 2022 and any linux system with Python 3.10.

We fixed a few bugs: now the installer can be run from outside of
the oq-engine directory, and there is a better error message when it is
called with an unsupported Python version.

The installer also installs the standalone tools, which are visible in
separate tabs in the WebUI. Before they had to be installed manually.

Our RPM packages use the universal installer internally.

`numba` has been added to the list of dependencies and it is now automatically
installed with the engine. The engine still works without it, though
calculations might be slower without numba.

We added NetworkX as a dependency: this is used only when performing
risk infrastructure calculations.

We upgraded pandas to version 1.3.5, to avoid a bug breaking the
risk infrastructure calculations.

We raised the toml module version to 0.10.2.

## Other

Thanks to a grant from USAID the engine manual has been converted from
LaTeX format to Sphinx format and it is now accessible online at the
address https://docs.openquake.org/oq-engine/manual/
We also overhauled the advanced manual and documented the new features.

Modern laptops/PCs tend to have many cores but not enough memory per
core. To avoid running out of memory the engine now automatically
disables parallelization if less than 0.5 GB per core is
available. We remind our users that for large calculations, 4 GB per
core is recommended; also, hyperthreading should be disabled to increase
the available memory per core.

If the DbServer does not start, it is now possible to
debug the problem by accessing the database access directly;
it is enough to set the environment variable `OQ_DATABASE=local`
or to set `dbserver.host = local` in the openquake.cfg file.

We extended the WebUI to display the host name in the calculation list:
this is useful when running calculations on a shared database.

At user request, we introduced three new environment variables `OQ_ADMIN_LOGIN`,
`OQ_ADMIN_PASSWORD`, `OQ_ADMIN_EMAIL` that can be used to set the credentials
of the administrator user in the WebUI.
