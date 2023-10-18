Version 3.18 is the culmination of 3 months of work involving around 200
pull requests. It is aimed at users wanting the latest features
and maximum performance. Users valuing stability may want to stay with
the LTS release instead (currently at version 3.16.7).

The complete set of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.18/debian/changelog

A summary is given below.

# Memory and space savings

After years of effort, we finally managed to get a drastic reduction
in memory consumption in classical calculations. For instance, in
cluster situations, instead of requiring 128 GB for the master node,
now we require ⅓rd of that. Moreover, for large calculations, now
the worker nodes require nearly half of the memory that was required
before. This was achieved by implementing an automatic parallel tiling
mechanism invisible to the user.

There was an even more impressive memory reduction in event based
calculations, which now requires 2-3 times less memory than
before. This is particularly important on small machines (i.e. desktop
computers and mini pc) since they tend to have many threads and not
enough memory. Right now all of the models in GEM's hazard mosaic can be run
on a machine with 16 virtual cores and 64 GB of RAM and for most models even
32 GB of RAM is sufficient. Earthquake computing is more accessible
than ever.

Related to the memory saving, there was also a substantial reduction
in disk space occupation in classical calculations. By storing the
rates as 32 bit floats instead of 64 bit floats we saved 25% of the
disk space.

# Optimizations in the hazard calculators

Most classical calculations are now faster since the `pointsource_distance`
approximation is enabled by default, with a value of 100 km.

We optimized the calculation of quantile hazard curves and maps (up to
7 times for the European model) by simply replacing a list comprehension
with a bit of numpy magic on the indices.

We optimized the event based calculator and now the generation of
ground motion fields can be up to 3 times faster, as measured in the
model for South America.

We reduced by 20% the data transfer in by transferring the ground motion
fields as dictionaries of arrays rather then DataFrames and we
we reduced the memory consumption by 10% by avoiding an unwanted cast
from 32 bit floats to 64 bit floats.

We reduced the slow tasks in event based calculations
and we removed a slowdown in large calculations when reading
an unneeded event array.

We changed the stochastic part of the algorithm generating the GMFs
to avoid unwanted correlations in the case of full enumeration (see
https://github.com/gem/oq-engine/issues/9073).

# Work on hazardlib

Marco Pagani fixed a long standing resampling bug affecting
the simple fault sources and therefore affecting most hazard models;
the impact on the numbers, however, is negligible.

There was a lot of work on the KiteFaultSurface class which has been
refactored and optimized by caching surfaces already
instantiated and by implementing a faster `.count_ruptures()` method.
Models with many KiteFaultSources (like the CCA model)
can be 3 or more times faster in event based calculations.

Laurentiu Danciu and Athanasios Papadopoulos contributed a set of
adjusted Swiss GMPEs for application in the Earthquake Risk Model of
Switzerland.

# Scenarios with conditioned GMFs

There was a subtantial amount of work on the scenario calculator for
conditioned GMFs, first introduced as an experimental feature in
engine 3.16. Originally it worked only for `truncation_level=0` and
`number_of_ground_motion_fields = 1` while now it has been extended to
the general case. Moreover we have added a new parameter
`maximum_distance_stations` that can be used to filter out stations
which are very distant from the rupture (in the sense of the `rrup`
distance).  We also optimized the calculator which is now faster than
before.  Many bugs have been ironed out and a few consistency checks
has been added. It much more reliable than in the past, however it
should still be considered in experimental status.

# New features: AEP/OEP curves, infrastructure risk, liquefaction

At user request, we extended the event based risk calculator to
produce Aggregate Exceedance Probability (AEP) and Occurrence
Exceedance Probability (OEP) loss curves (see
https://github.com/gem/oq-engine/issues/8971). The way to enable the
feature is to add the line `aggregate_loss_curves_types = aep`
or `aggregate_loss_curves_types = oep` in the `job.ini` file.
It is possible to compute both kind of curves
at the same time by adding `aggregate_loss_curves_types = aep, oep`.

After 6 months of hard work, finally the engine supports infrastructure
risk, contributed by Astha Poudel and the GEM staff in
https://github.com/gem/oq-engine/issues/8655. The feature
is documented in the [official manual](https://docs.openquake.org/oq-engine/engine-3.18/manual/risk.html#infrastructure-risk-analysis)

There was a major overhaul of the secondary perils module
(see https://github.com/gem/oq-engine/pull/8982)
including the following regional liquefaction models:

ZhuEtAl2017LiquefactionCoastal and ZhuEtAl2017LiquefactionGeneral,
RashidianBaise2020Liquefaction, AllstadtEtAl2022Liquefaction,
AkhlagiEtAl2021LiquefactionA and AkhlagiEtAl2021LiquefactionB
Bozzoni2021LiquefactionEurope, TodorovicSilva2022NonParametric.

The TodorovicSilva2022NonParametric model is based on a machine 
learning approach and therefore now the engine supports the onnx runtime.

# Bug fixes and better error messages

Parallelizing engine calculations with pytest, GNU parallel or other
approaches did not work due to conflicts in the calculation IDs (i.e.
two calculations could get the same ID). This issue has been fixed.

The internal output `avg_gmf` was computed incorrectly due to an ordering
bug in the event ID. This has been fixed.

There was a regression in engine 3.17 breaking the disaggregation by source
for the Japan model. It has been fixed.

We fixed a bug in calculations with a filtered site collection using
the HM2018CorrelationModel. The model should still be considered
experimental.

When configured for multiple users the WebUI allowed people to see
the results produced by other users knowing the URL. This is not
possible anymore.

Removing a calculation through the WebUI failed on Windows due to the
use of a wrong path separator. This has been fixed.

The command `oq reaggregate` was failing with a cryptic error message
when starting from a calculation with a missing or inconsistent
`aggregate_by`. Now there is a clear error.

The command `oq engine --delete-calculation XXX` could not remove the
calculation file `calc_XXX.hdf5` when the DbServer was on a different
machine, or when the DbServer user had no permissions to delete. Now
the deletion is performed directly by the user running the command.

We fixed consequence calculations for 'homeless', 'fatality' and 'injury'
with and without a specified 'time_event'.

There is now a better error message for logic trees with branchsets
exceeding the limit of 183 branches.

There was a `ValueError: max() arg is an empty sequence` caused by
sources below the `minimum_magnitude`: now they are simply discarded.

We raise now a clear error message "quantiles are not supported with
collect_rlzs=true" when the calculation of quantiles is not supported.

We fixed a log message that was displaying a wrong number for
the size of the produced GMFs in event based calculations.

A site model can be split in multiple files. There is now a check on
the headers and an error is raised if the headers are not consistent.

# AELO project

There was a substantial amount of work on the AELO project. The engine
is finally able to compute the ASCE-41 and ASCE-7 parameters by using
code from the USGS (the `rtgmpy` library).

# Other

After more than four years since their 
[deprecation](https://github.com/gem/oq-engine/pull/4524), 
we have finally removed the XML outputs for hazard curves, hazard maps 
and uniform hazard spectra. They can only be exported in CSV format.

We improved the universal installer to use the `--trusted-host`
feature: this is necessary for corporate users with a firewall
forbidding downloads from PyPI.

We also changed the universal installer to read the requirements
from the stable version and not from master, unless --version
is specified.

This was essential because we upgraded Shapely to version 2.0.1
and Pandas to version 2.0.3 which are incompatible with the past and
therefore with the old behavior the installer would have produced a
broken installation.

We also upgraded Django to version 3.2.21 with some security fixes and we
included in the engine distribution the onnx runtime, needed
for the new liquefaction models.

Finally, we introduced experimental support for HPC clusters and supercomputers
using the SLURM scheduler. People interested in becoming beta testers
are invited to contact us.
