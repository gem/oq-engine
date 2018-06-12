Release notes for the OpenQuake Engine, version 3.0
===================================================

This release drops support for Python 2.7. From now on, the engine
requires Python 3.5+ to run. Apart from this change, several new
features were implemented, like the support for time dependent source
models, automatic gridding of the exposure, enhancements to the
disaggregation calculator, improvements to the task distribution and a lot more.
Over 110 issues were closed. For the complete list of changes, please
see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.0/debian/changelog .

Management of the source model
--------------------------------

As of engine 3.0, the sources are split upfront, before filtering.
This approach became possible after optimizing the splitting procedure
for fault sources which now is extremely fast. It has several benefits
in terms of simplicity of the code and better estimation of the task
computational weight.

Moreover, it is now possible to warn the user upfront, if she uses
discretization parameters such as the `area_source_discretization`,
the `rupture_mesh_spacing` and the `complex_fault_mesh_spacing` which
are too small, thus producing millions of ruptures without need (this is
a common mistake).

Complex fault sources are now split in more sub-sources
than before and this produces a substantial improvement of the task
distribution. It also fixed a bug with the `event_based_rupture`
calculator generating too few tasks.

A different bug with the classical calculator generating too few tasks
when the option `optimize_same_id_sources` is set has been fixed as
well.

We extended the check on duplicated IDs in the source model to models in
the NRML 0.5 format. This means that if a single source model is split in
several files (i.e. the `<uncertaintyModel>` tag in the source model logic
tree file contains several paths) the source IDs must be unique across all
files.

Source models with time-dependent sources now require two new tags:
`investigation_time` (mandatory) and `start_time` (optional, but it will
likely become mandatory in the future). The `investigation_time` tag is used
to check the `investigation_time` parameter in the `job.ini` file, so that
the user cannot accidentally use the wrong investigation time.

Now we log some information about the floating/spinning factors, which
are relevant for point sources and area sources (see the manual
section 2.1.1.1 for an explanation). This is useful for us since in
the future we may introduce some optimization to reduce the
floating/spinning of the ruptures. Users can simply ignore such logs.

Hazard
--------------

We extended the event based calculator to work with mutually exclusive
(mutex) sources: this is relevant for the Japan model and others.
Thanks to some fixes to the GriddedRupture class in hazardlib now it
is also possible to export ruptures of this kind, which are relevant
for several recent hazard models.

We fixed how the event year is set in event based calculations.
Before the events sets were considered
temporally ordered, i.e. in a case with 2 stochastic event sets (SES)
with an investigation time of 50 years one could have years (0, 4, 13, 27, 49)
in the first SES and (55, 61, 90) in the second SES: now we would have
(0, 4, 13, 27, 49) in the first SES and (5, 11, 40) in the second. The
event in the second SES have no greater years that the events in the first SES
since each event set starts from the year 0.
This is the correct way of proceeding in the case of time-dependent models,
which were not supported before.

The net effect of the change is that the ordering of the event loss
table can be different than before, since the year was used (solely)
as an ordering parameter in the exporter.

Hazard disaggregation
---------------------

We implemented statistical disaggregation outputs. This is implemented
in a straightforward way: if there are multiple realizations and if in
the `job.ini` file the parameters `mean_hazard_curves` and/or
`quantile_hazard_curves` are set, then the mean and/or quantiles of the
hazard outputs are computed. You can export such outputs as usual.

The parameter `disagg_outputs` is now honored: for instance if you have
in the `job.ini` `disagg_outputs = Mag Mag_Dist`, then only the
outputs of kind `Mag` and `Mag_Dist` are computed and stored. Before
all of them were computed and stored and the parameter affected only
the export. If `disagg_outputs` is not given, all of the available
disaggregation outputs are generated, as in the past.

We introduced, experimentally, a _disaggregation by source_ feature. It is
restricted to the case of a single realization. In that case, if you set
`disagg_by_src=true` in the `job.ini`, then an output "Disaggregation by
Source" is generated. When exported, you get a set of .csv files with fields
`(source_id, source_name, poe)`. For each source with nonzero contribution
the contribution to the total probability of exceedence is given.

Finally, we fixed a small bug in the disaggregation calculator with
parameter `poes_disagg`: we were reading the source model twice without reason.

Hazardlib/HMTK/SMTK
--------------------

We optimized the Yu et al. (2013) GMPEs for China which is now several time
faster than before.

[Graeme Weatherill](https://github.com/g-weatherill) ported to Python 3.5 the [Strong Motion Toolkit](https://github.com/GEMScienceTools/gmpe-smtk),
which depends on hazardlib and is a part of the OpenQuake suite.

[Nick Ackerley](https://github.com/nackerley) fixed a bug in the HMTK
plotting libraries and added the ability to customize the figure size.

The source writer in hazardlib now checks that the sum of the
probabilities of occurrence is 1, when saving nonparametric sources.
This avoids errors when building time-dependent models.

Risk
-----

The management of the exposure has been refactored and improved.
It is now possible to run a risk calculation from a pre-imported
exposure. This is important because the engine is powerful
enough to run calculations with millions of assets and it is convenient
to avoid reimporting the exposure every time if it does not change.

On the same note, it is possible to use a pre-imported risk model,
without having to reimport it at each risk calculation.

As of engine 3.0, the exposure should contain a tag `<occupancyPeriod>`
listing the occupancy periods, i.e. subsets of `day`, `night`, `transit`,
including the case of no occupancy periods. If such tag is missing, you
will get a warning. If such tag is present, but the listed occupancy
periods are inconsistent with the ones found in the assets, a clear error
is raised.

The ability to import CSV exposures has been extended to the cases
when there are occupancy periods, which are managed simply as additional
fields. Insurance parameters (insured_losses/deductibles) are still
not supported in CSV format and the XML format is still needed for
that case. We plan to keep working on that in the future.

We extended the engine logic to read the sites from the hazard
curves, if available. Moreover we changed the logic to extract the sites
from the exposure in precedence over the site model,
if the sites are not provided explicitly (via a sites.csv file,
the hazard curves or a region).

This was necessary because of a new feature,
i.e. the automatic gridding of the exposure. If your `job.ini` file
contains an exposure, no `region` parameter and the parameter
`region_grid_spacing`, then a grid of sites is automatically generated
from the region encircling the exposure (if there is a `region` parameter the
grid is generated from the `region` as before).

Automatic gridding of the exposure is very important, because often
the assets are provided with a very high resolution (say 1 km); by
providing a coarser grid (say 5 km) the hazard part of the calculation
can become a lot faster (say 25 times faster) while producing very
similar results for the aggregated losses.

Care is taken so that points of the grid with no close assets
(i.e. outside the grid spacing) are automatically discarded; moreover,
there are checks to make sure that all assets are associated to the
grid.

Event Based Risk calculations with sampling are now officially supported,
after years in which this feature was experimental and not really working.
This is relevant for cases like the India model were the number of
realizations is so large (there are over 200,000 realizations) that full
enumeration is not an option and sampling of the logic tree is a necessity.

WebAPI/WebUI/QGIS plugin
-----------------------------------------------------

We fixed some permission bugs with the WebUI when groups are involved:
now it is possible to download the outputs of calculations run by
other people in the same group. This is useful for organizations
wanting to enable the authentications features of the WebUI.
By default, as always, the WebUI is public.

We added more risk outputs to the extract API. In particular now it is
possible to extract also the losses by asset coming from event based
risk and classical risk calculations. Moreover it is possible to
aggregate such losses by using the usual aggregation interfaces (the
web API and the QGIS plugin).

Bug fixes/additional checks
------------------------------

Running a calculation on a big machine, copying the datastore on a small
machine (i.e. a laptop) and exporting the results now works even for
calculations involving GMPE tables i.e. prediction equations implemented
as numeric tables in .hdf5 format. This is relevant for the Canada model
and others.

We have now a better error message when there are duplicated sites in the CSV;
in particular, the first line with the duplicates is shown, as well as the
line number.

We fixed a bug with newlines in the logic tree path breaking the CSV exporter
for the realizations output. This was happening with models split in multiple
files, like the CCARA model.

We fixed a bug in classical_risk, happening when the number of statistics
was larger than the number of realizations (for instance, in a case with
two realizations, computing mean, quantile-0.15 and quantile-0.85, i.e. three
statistics).

We fixed the strange issue of very small negative numbers appearing in
scenario_damage outputs: this happened due to rounding errors. Now
the correct result (i.e. zeros) is stored.

We added a check in calculations reading the GMFs in CSV format: now
there must be a single realization in the input file.

When running a scenario calculation using precomputed GMFs, a clear
error message appears when the IMTs in the GMFs are not
compatible with the IMTs in the fragility/vulnerability file.

We added a check against duplicated fields in the exposure CSV.

oq commands
-----------

The command `oq info` has been extended to source model logic tree files:
in that case it reports a summary for the full composite source model.

The command `oq dbserver stop` and `oq workers stop` now correctly
stops the zmq workers (relevant for the experimental zmq mode).

The command `oq show` was not working in multiuser situations for
calculations with a parent, since the parent was being read
from the wrong directory. This issue has been fixed.

The command `oq show job_info` now returns the amount of data received
from the controller node while the computation is running: before this
information was available only at the end of the computation.

There is a new command `oq importcalc host calc_id username password`
to import remote calculations into the local engine database. The
command has some limitations: it works only for calculations without
a parent and only if there are no clashes between the remote calculation ID
and the local calculation ID. It should be considered an internal command.

Internals
--------------

A huge improvement has been made in cluster situations: now the results
are returned via [ZeroMQ](http://zeromq.org/) and not via rabbimq.
This allows us to bypass the limitations of
[rabbitmq](https://www.rabbitmq.com/): large computations can 
be run without running out of disk space in the mnesia directory.
Hundreds of thousands of tasks can be generated without issues, a feat
previously impossible.

Notice that you may need to adjust the master node firewall, if
already configured, to allow incoming traffic on TCP port range
1907-1920.

Now we use the port 1907 for the DbServer, when installing the engine
from the packages. When installing from sources, the port is the number 1908,
as before. In this way an installation from packages can coexists with
an installation from sources out of the box.

The task distribution code has been simplified and features
in the experimental/proof-of-concept state has been removed: in
particular the support to ipython and the support to SGE have disappeared.
They were not used and they were a significant maintenance cost.
The default for the `distribution` parameter in the configuration
file openquake.cfg is now `processpool`, not `futures`. The old
syntax is still supported, but a warning will be printed, saying
to use `processpool` instead. Technically we do not rely anymore
on the Python module `concurrent.futures`, we use the module
`multiprocessing` directly.

The engine now stores more information about the sources.
In particular in the case of
event based calculations the `source_info` dataset contains the number
of events generated by each source. Moreover, there is an utility
`utils/reduce_sm` than can read such information and reduce a source
model by removing all sources not producing events.

As usual a lot of refactoring was done and several engine tests are
faster than before. Also the event based risk demo is several times
faster than before.

Deprecations/removals
---------------------

The engine does not work anymore with Python 2. Hazardlib and the
Hazard Modeller Toolkit, included in the engine, still work with
Python 2 but this is only incidental: they may stop working at
any moment without warning, since we are not testing anymore the
engine libraries with Python 2.

The old commands `oq engine --run-hazard` and `oq engine --run-risk`, deprecated
two years ago, have been finally removed. The only command to use to run
calculations is `oq engine --run`, without distinction between hazard and
risk.

The function `openquake.hazardlib.calc.stochastic.stochastic_event_set`
has been deprecated: you can use the function
`openquake.hazardlib.calc.stochastic.sample_ruptures` instead.

As usual, exporting the results of a calculation executed with a previous
version of the engine is not supported, except for hazard curves/maps/spectra.
We recommend first to export all of the results you need and then
to upgrade to the latest version of the engine.
