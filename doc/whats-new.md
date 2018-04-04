Release notes for the OpenQuake Engine, version 3.0
===================================================

This release drops support for Python 2.7. From now on, the engine
requires Python 3.5+ to run. Apart from this change, several new features
entered, in particular in the disaggregation calculator and in the exposure
support.  Over 110 issues were closed. For the complete list of
changes, please see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.0/debian/changelog .

Management of the source models
--------------------------------

The task distribution has been improved by changing the algorithm
used to manage the sources. As of engine 3.0, the sources are first
split and then sent to the workers. This change is reflected in the log
messages.

An improvement of the splitting procedure for complex fault sources
resulted in a substantial improvement of the parallelization for
several calculations. It also fixed a bug with the event_based_rupture
calculator generating too few tasks.

A different bug with the classical calculator generating too few tasks
when the option `optimize_same_id_sources` is set has been fixed as
well.

We extended the check on duplicated IDs in the source model to models in
the NRML 0.5 format. This means that even if a source model is split in
several files (i.e. the `<uncertaintyModel>` tag in the source model logic
tree file contains several paths) the source IDs must be unique across all
files.

Source models with time-dependent sources now require two new tags
`investigation_time` (mandatory) and `start_time` (optional, but it will
likely become mandatory in the future). The `investigation_time` is used
to check the `investigation_time` used in the `job.ini` file, so that
the user cannot accidentally use the wrong  `investigation_time`.

Hazard
--------------

Running a calculation on a big machine, copying the datastore on a small
machine (i.e. a laptop) and exporting the results now work even for
calculations involving GMPE tables i.e. prediction equations implemented
as numeric table in .hdf5 format. This is relevant for the Canada model
and others.

We have now a better error message when there are duplicated sites in the CSV;
in particular, the first line with the duplicates is shown, as well as the
line number.

We extended the event based calculator to work with mutually exclusive
(mutex) sources: this is relevant for the Japan model and others.

We fixed how the event year is set: now each stochastic event sets
is considered independent, Before the events sets were considered
temporally ordered, i.e. in a case with 2 stochastic event sets (SES)
with an investigation time of 50 years one could have years (0, 4, 13, 27, 49)
in the first SES and (55, 61, 90) in the second SES: now we would have
(0, 4, 13, 27, 49) in the first SES and (5, 11, 40) in the second. The
event in the second SES have no greater years that the events in the first SES.
This is the correct way of proceeding in the case of time-dependent models,
which were not supported before.

The net effect of the change is that the ordering of the event loss
table can be different than before, since the year was used (solely)
as an ordering parameter in the exporter.

The setting of the years now also works in case of sampling: this case
was previously untested.

Hazard disaggregation
---------------------

We fixed a small bug in the disaggregation calculation: we were
reading the source model twice without reason.

We implemented statistical disaggregation outputs. This is implemented in
a straightforward way: if there are multiple realization and in the `job.ini`
the parameter `mean_hazard_curves` and/or `quantile_hazard_curves` are set,
the mean and/or quantiles of the hazard outputs are computed. You can export
such outputs as usual.

The parameter `disagg_outputs` is now honored: for instance if you set
in the `job.ini` `disagg_outputs = Mag Mag_Dist` then only the outputs
of kind `Mag` and `Mag_Dist` are computed and stored. If `disagg_outputs`,
all the available disaggregation outputs are generated.

We introduced, experimentally, a _disaggregation by source_ feature. It is
restricted to the case of a single realization. In that case, if you set
`disagg_by_src=true` in the `job.ini`, then an output "Disaggregation by
Source" is generated. When exported, you get a set of .csv files with fields
`(source_id, source_name, poe)`. For each source with nonzero contribution
the contribution to the total probability of exceedence is given.

Hazardlib/HMTK/SMTK
--------------------

We optimized the Yu et al. (2013) GMPEs for China which is now several time
faster than before.

Graeme Weatherill ported the [Strong Motion Toolkit]
(https://github.com/GEMScienceTools/gmpe-smtk) which depends on hazardlib
and is a part of the OpenQuake suite to Python 3.5.

Risk
-----

The management of the exposure has been refactored and improved.
Ot is now possible to run a risk calculation from a pre-imported
exposure. This is very importance because now the engine is powerful
enough to run calculations with millions of assets and it is convenient
to avoid reimporting them every time if the exposure does not change.

On the same note, it is possible to use a pre-imported risk model,
without having to reimport it at each risk calculation.

We extended `get_site_collection` to read the sites from the hazard
curves when available. The sites are extracted from the exposure in
precedence over the site model.

We fixed bug in classical_risk, happening when the number of statistics
was larger than the number of realizations (for instance, in a case with
two realizations, computing mean, quantile-0.15 and quantile-0.85).

We fixed the strange issue of small negative numbers appearing in
scenario_damage outputs: this happened due to rounding errors. Now
the correct result (i.e. zeros) is stored.

We added a check in calculations reading the GMFs in CSV format: now
the must be a single one realization in the input file.

When running a scenario calculation using precomputed GMFs, a clear
error message appears when the IMTs in the GMFs are not
compatible with the IMTs in the fragility/vulnerability file.

We added a check against duplicated fields in the exposure CSV.

WebAPI/WebUI/QGIS plugin
-----------------------------------------------------

We fixed some permission bugs with the WebUI when groups are involved:
now it is possible to download the outputs of calculations run by
other people in the same group.

We added more risk outputs to the extract API. In particular now it is
possible to extract also the losses by asset coming from event based risk
calculations. Moreover it is possible to aggregate such losses by using
the usual aggregation interfaces (the web API and the QGIS plugin).

Bug fixes/additional checks
------------------------------

oq commands
-----------

The command `oq info` has been extended to source model logic tree files:
in that case it reports a summary for the full composite source model.

The command `oq dbserver stop` and `oq workers stop` now correctly
stops the zmq workers (relevant for the experimental zmq mode).

There is a new command `oq importcalc host calc_id username password`
to import remote calculations into the local engine database. The
commmand has some limitations: it works only for calculations without
a parent and only if there are no clashes between the remove calculation ID
and the local calculation ID. It should be considered an internal command.

IT
---

A huge improvement has been made in cluster situations: now the results
are returned via [ZeroMQ](http://zeromq.org/) and not via rabbimq.
This allows to bypass the limit of rabbitmq and larger computations can 
be run without running out of disk space in the mnesia directory.
Hundreds of thousands of tasks can be generated without issue, a feat
previously impossible.

Task distribution code has been simplified:
code in the state experimental/proof-of-concept has been removed: in
particular the support to ipython and the support to SGE. As it is
now, they are not used and still a significant maintenance cost.

Now we use the port 1907 for the DbServer, when installing the engine
from the packages. When installing from sources, the port is the number 1906,
as before. In this aways an installation from packages can coexists with
an installation from sources out of the box.

Internals
--------------

Now we log some information about the floating/spinning factors, which
are relevant for point sources and area sources. This is useful for us since
in the future we may introduce some optimization to reduce the
floating/spinning of the ruptures (see the manual section 2.1.1.1
for an explanation) when not relevant. Regular users can just ignore such logs.

The engine now store more information. In particular in the case of
event based calculations the `source_info` dataset contains the number
of events generated by each source. There is an utility
`utils/reduce_sm` than can read such information and reduce a source
model by removing all sources not producing events.

As usual a lot of refactoring was done and several engine tests are
faster than before.

Deprecations/removals
---------------------

The old commands `oq engine --run-hazard` and `oq engine --run-risk`, deprecated
two years ago, have been finally removed. The only command to use to run
calculations is `oq engine --run`, without distinction between hazard and
risk.

The function `openquake.hazardlib.calc.stochastic.stochastic_event_set`
has been deprecated: you can use the function
`openquake.hazardlib.calc.stochastic.sample_ruptures` instead.

As usual, exporting the results of a calculation executed with previous
version of the engine is not supported, except for hazard curves/maps and
spectra. We recommend first to export all the results you need and then
to upgrade to the latest version of the engine.
