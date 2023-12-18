Release notes v3.7
==================

This is a major release featuring several important fixes and
improvements, especially to the event based and disaggregation
calculators, plus a new task queue. More than 220 pull requests were merged.

For the complete list
of changes, see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.7/debian/changelog

Disaggregation
--------------

We fixed a bug in disaggregations with nonparametric sources:
they were being incorrectly discarded.

We fixed a bug in disaggregations crossing the international
date line: the lon-lat bins were incorrectly computed.

We fixed the filtering procedure by discarding ruptures
over the integration distance that were incorrectly not discarded before.

We implemented various optimizations to make it possible to run
calculation with many sites (where many means less than a thousand,
disaggregating is still expensive).

We changed the exporter for `disagg_by_src` to export filenames
containing the site ID and not longitude and latitude, consistently
with the other disaggregation exporters.

We generate the output `disagg_by_src` even in the
case of multiple realizations, but only the chosen realization is considered.

There is a new configuration parameter `max_sites_disagg` which can be used
to constraint the maximum number of disaggregation sites; the default is 10.

We added an experimental API `extract/disagg_layer` to extract the
disaggregation outputs for multiple sites at once.

Event based
-----------

There was a crucial change in the event based calculators: we moved
from 64 bit event IDs to 32 bit event IDs. The change was necessary to
accomodate Excel users, because Excel silently converts 64 bit
integers to floats and truncates the numbers, thus causing the IDs to
be non-unique. This is not a problem of the engine per se, but it
caused endless trouble in the past, so it has been fixed at the source.

Users taking advantage of the relation `rupture_ID = event_ID //
2 ** 32` will have to change their scripts and extract the rupture_ID
from the events table instead, since the relation does not hold true
anymore. The others will not see any change, except that the event
IDs in their event loss table will be smaller numbers.

When exporting the event loss table a new field `rupture_id` will be
visible. The event loss table has been unified (as much as possible)
between scenario, event based and event based calculations.

We added a new output `Events` which is a CSV with
fields id, rup_id, rlz_id where `id` is the 32 bit event ID, `rup_id`
is the rupture ID and `rlz_id` is the realization ID.
 
We fixed the multiplicity value exported in the `ses.xml` file:
now it is consistent with value exported in the `ruptures.csv` file
even in the case of full enumeration.

We fixed a bug which was causing a wrong bounding box to be exported
in the `ruptures.csv` file (with a lon<->lat inversion).

The `ruptures.csv` exporter has been changed to use a comma as separator and
not a tab, to be consistent with all other exporters.

We extended the computation of the rupture loss table to the `ebrisk`
calculator.

We changed `ebrisk` to produce an output `avg_losses-stats`, consistently
with the `event_based_risk` calculator.

We added a check for missing `risk_investigation_time` in `ebrisk`
calculations.

A substantial amount of work was spent to reduce the problem of slow tasks
in the `ebrisk` calculator. Now the task distribution is a lot better, the
memory consumption is greatly reduced and data transfer is a lot less
than before.

The ability to compute insured losses has been restored experimentally
from the `ebrisk` calculator. It works in a different way than before
and it is not documented on purpose. But if you are interested in
testing it you can get in touch with us.

Hazardlib
---------

Graeme Weatherill contributed a few updates of the Kotha et al. (2019)
GMPE with new coefficients using a robust linear mixed regression
analysis. There are three new subclasses for modelling site amplifications:
see https://github.com/gem/oq-engine/pull/4957 for the details.

Graeme also contributed four site amplification models for SERA (see
https://github.com/gem/oq-engine/pull/4968 for the details) and a
preliminary scalable backbone GMPE for application to the stable
cratonic parts of Europe, based on an analysis of epistemic
uncertainty in the NGA East suite
(see https://github.com/gem/oq-engine/pull/4988).

Kris Vanneste updated the coefficients table of the Atkinson (2015) GMPE
to the latest version of the published paper.

Guillaume Daniel contributed an implementation of the (Ameri) 2017 GMPE.

We added a new rupture-site metric: the azimuth to the closest point on the
rupture.

There was a bug fix in the Youngs and Coppersmith (1985)
GMPE: due to numerical issues, instantiating the GMPE with the classmethod
`YoungsCoppersmith1985MFD.from_total_moment_rate` was producing wrong
numbers.

There were some internal changes to the GMPE instantiation mechanism,
so that now users of hazardlib do not need to call the `.init()` method
manually.

Other Hazard
------------

There was a subtle bug introduced in engine 3.3 that went unnoticed for
nearly a year: due to a change in the prefiltering mechanism,
for complex fault sources producing large ruptures
some ruptures at the limit of the integration distance
could be incorrectly discarded, thus producing a lower hazard.
This was discovered in the South America model, where there are complex
fault sources with magnitudes up to 9.65.

There was a memory issue in the GMPE logic tree sampling procedure, visibile
for logic trees with billions of branches, like in the SERA model. This
has been fixed, by not keeping the full tree in memory, similarly to
what we do for the source model logic tree.

The source weighting algorithm has been improved, thus reducing even more the
issue of slow tasks in classical calculations. There was also some
refactoring of the internals of classical calculations

There were spurious warnings of kind `RuntimeWarning: invalid value
encountered in greater` introduced by some debug code in engine 3.6
for calculations with a site model; they have been removed.

We added a clearer error message when the user try to use a correlation
model with truncation_level = 0.

We removed the output `sourcegroups.csv` which was of little interest to the
final users.

Risk
----

We restored the ability to accept loss ratios > 1, but only for
vulnerability functions of kind LN, i.e. using the LogNormal distribution.

We fixed a bug for vulnerability functions of kind BT, i.e. using the Beta
distribution: the seed was not set properly and the results were not
reproducible.

There was a bug when importing the GMFs from a CSV file, if the sites were
not ordered by lon, lat, causing the wrong risk to be computed.

There was a bug in the `realizations` exporter for scenarios with
parametric GSIMs, where newlines were not quoted.

We added some metadata to the risk CSV exporters, in particular the
`risk_investigation_time`.

We now raise a clear error for unquoted WKT geometries in multi-risk
calculations.

We now raise a clear error when the `aggregate_by` flag is used in calculators
different from `ebrisk`.

We optimized the aggregation facilities of the engine by leveraging
on `numpy.bincount`, with a speedup of more than an order of magnitude.

We changed the default value for the `site_effects` parameter to false;
this is necessary for the ShakeMap calculator since recent USGS
ShakeMaps are taking into account the site effects already and we need
to avoid overamplification.

When exporting the realizations from a ShakeMap risk calculation the
`branch_path` field has now the value `FromShakemap` instead of
`FromFile`.

IT
--

There were three major IT projects in this release.

1. There was a substantial amount of work on the *zmq distribution
mechanism* which now works correctly on clusters. It is still in an
experimental status and there a few minor features to be tuned, but we
are already running our production calculations with it, with many
advantages with respect to using the celery/rabbitmq combo. In the
future we plan to abandon celery/rabbitmq in favor of the pure zmq
mechanism.  You can already already use the new approach by following
the documentation.

2. Extra-large classical calculations (i.e. Australia) are always been prone to
run out of memory, due to the sheer amount of data to transfer.  The
solution has been the introduction of a *task queue* acting before the
rabbitmq/zmq queue. For instance, in a cluster with celery instead of
sending 10,000 tasks to rabbitmq at once, causing the system to go out
of memory, the engine sends the tasks to the task queue, from which
only one task at the time is sent at rabbitmq, once there is a free
core. Thanks to this mechanism it is also possible to control the
number of cores used by the engine by setting the parameter
`num_cores` in the `job.ini`. If it is not set, all of the available
cores are used, but it can be set to a smaller number to leave some
cores free for other purposes.

3. For several releases the engine has been producing a couple of files
calc_XXX.hdf5 and cache_XXX.hdf5 for each calculation. The *cache file*
has been finally removed. It was introduced as a hack to work around some
limitations of HDF5, causing a lot of data duplication. It is not neeeded
anymore, since we are now using the SWMR feature of h5py properly. This
was a major effort requiring nearly 25 pull requests to be completed.

There were also a few minor fixes/changes.

The `-l` switch in `oq engine --run` finally works and in particular it is
possible to see the debug logs when `-l debug` is passed on the command line.

Deleting a calculation from the command-line or from the WebUI
now only hides the calculation from the user. The calculation is actually
kept in the database and can be restored.

It is still possible to really delete the calculations of an user with
the command `oq reset`. Still, it has been made safer and only datastores
corresponding to calculations in the database are removed.

Calculations that fail in the validation phase, before starting, are
now hidden to the user, to avoid littering. The error message
is still clearly displayed to the user in all cases (command-line, Web UI,
QGIS plugin)

We fixed/changed several APIs for interacting with the QGIS plugin.

Moreover, we worked at the documentation, with various improvements both to the
manual and to the GitHub repository.

Libraries and Python 3.7
------------------------

We upgraded numpy to version 1.16, scipy to 1.3 and h5py to 2.9:
with such libraries the engine works with Python 3.7. Actually, we have
a cluster in production using it and we have switched the development to
Python 3.7. However, we are still providing
Python 3.6 in our packages with the goal of migrating to 3.7
in the future. The migration to numpy 1.16 required disabling
OpenBLAS threads to avoid oversubscription: therefore importing the
engine sets the environment variable OPENBLAS_NUM_THREADS to '1'.

Supported operating systems
---------------------------

Support for the operating system Fedora 28 has ceased because it reached the
End-Of-Life. Support for Fedora 31 (currently in beta) has been introduced.
