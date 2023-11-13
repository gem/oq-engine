Release notes for the OpenQuake Engine, version 3.5
===================================================

This is a major release featuring a new `multi_risk` calculator,
several improvements to the hazard and risk calculators as well as a
few bug fixes. Nearly 140 pull requests were merged. For the complete list
of changes, see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.5/debian/changelog

Hazard calculators
-----------------------------------

1. There was a big improvement in the case of extra-large source
models. Now we use approximately 4 times less memory then before: for
instance, we went down from 100 GB of RAM required to run Australia, to
only 25 GB. This makes it possible to run large calculations on
memory-constrained machines. The change also reduces substantially the
data transfer in sources. It was made possible by an advance in the
parallelization strategy introduced in engine 3.4 (subtasks) that also
reduced substantially the problem of slow tasks.

2. We reduced the data transfer when computing the hazard curves and
statistics, sometimes with spectacular results (like reducing the
calculation time from 42 minutes to 42 seconds). Usually however the
computation of the curves and statistics does not dominate the total
time, so you may not see any significant difference.

3. We optimized the checks performed on the source model logic tree, 
things like making sure that `applyToSources` refers to sources that
actually exists. Again, even if the gain was spectacular (from 15
minutes to 15 seconds in the case of Australia), you will likely see
no difference because those checks are not dominating the total
computation time, unless you are using the `preclassical` calculator.

4. We restored the traditional sampling logic used in the engine until
18 months ago. This makes the implementation of some feature easier,
since all the realizations have the same weight, at the cost of making
more difficult other features that were deemed less important.
In practice, it means that you will have slightly different numbers
in calculations with sampling of the logic tree, but such differences
are akin to a change of the `random_seed`, i.e. not relevant.

5. Since a long time ago, the event based calculator has a debug flag
`compare_with_classical=true` which can be used to compare the
produced hazard curves with the classical hazard curves. Since it was a
debugging flag meant for internal usage it was missing some pieces, in
particular it was not possible to export the generated curves in the
usual way. This has been fixed.

6. Since release 3.4 the GMF exporter exports a file `sig_eps.csv`
containing for each event ID the associated inter-event standard deviation
and the residual. There is now an additional column `rlzi` for the
associated realization index.

Risk calculators
-----------------

1. A major refactoring of all risk calculators was performed, with a
significant benefit both in terms of reduced complexity and of
improved speed. In particular we saw a speedup of 2x in some event
based risk calculations (in the risk part, not the hazard part).

2. In order to make the refactoring possible we had to change the
`classical_risk` calculator, that was using different loss ratios for
different taxonomies. Now the calculator uses the same loss ratios for
all taxonomies. As a consequence, you may see some slight difference
in the generated loss curves.

3. We changed the order in which the events are stored, with an effect on
event based risk calculations with coefficients of variations. The change
is akin to a change of seed, i.e. not relevant. Moreover, now
the epsilons are stored and not transferred via rabbitmq, thus making
the calculator simpler and more efficient.

4. Thanks to the change in the epsilons, now the `ebrisk` calculator is able
to manage vulnerability functions with coefficients of variations, which
means that it is getting close to become a full replacement for the event
based risk calculator. Also, some export bugs in `ebrisk` were fixed.

5. `event_based_risk` calculations with zero coefficients of variations (i.e.
with no epsilons) have been optimized in the same way as we did for `ebrisk`.
This makes a difference if you have multiple assets of the same taxonomy on
the same hazard site, otherwise the performance is the same as before.

6. The way the risk models are stored internally has changed significantly,
to make it possible (in the future) an unification of the `scenario_risk`
and `scenario_damage` calculators.

67. We changed the `scenario_damage` calculator to accept silently single event
calculations (before it was raising a warning): in this case we do not
compute and do not export the standard deviations (before they were
exported as NaNs).

8. A new flag `modal_damage_state` has been added to the scenario damage
calculator. If it is set, instead of exporting for each asset the
number of buildings in each damage state, the engine will export for
each asset the damage state where most buildings are. This is a new
and still experimental feature.

9. A new experimental calculator called `multi_risk` has been introduced in
the context of the CRAVE project (Collaborative Risk Assessment for Volcanoes
and Earthquakes). It allows to compute losses and fatalities for volcanic perils
associated to ash fall, lava, lahar and pyroclastic flow, but it is designed
to be extensible to other kind of perils.

hazardlib
----------

We had five external contributions to hazarlib.

1. Michal Kolaj provided tabular GMPEs for Canada.
2. Graeme Weatherill provided the Kotha et al. (2019) shallow crustal GMPE
   and added a few adjustments to the BC Hydro GMPE to allow the user to
   calibrate the anelastic attenuation coefficient (theta 6) and the
   statistical uncertainty (sigma mu), for use in SERA project.
3. Guillaume Daniel updated the Berge-Thierry (2003) GSIMs and added several
   alternatives for use with Mw.
4. Chris van Houtte from New Zealand added a new class for Christchurch
   GSIMs of kind Bradley (2013b).
5. Giovanni Lanzano from INGV contributed the Lanzano and Luzi (2019)
   GMPE for volcanic zones in Italy


The job queue
---------------

The engine has now a job queue. The feature for the moment is experimental
and disabled by default, but it will likely become the standard in the future.
To enable the queue set the `serialize_jobs` flag in the openquake.cfg file:

```
[distribution]
serialize_jobs = true
```
When the queue is on, calculations are serialized, i.e. if N users try to
run calculations concurrently only one calculation will run (the first
submitted) and the other N-1 will wait. As soon as a calculation ends, the next
one in the queue will start, by preserving the submission order. The queue
is very simple and has no concept of priority, but it is extremely useful in
case of large calculations. It solves the problem of a large calculation
sending the cluster out of memory and killing the calculations of other
users.

As a side effect of the work on the queue system, various things have been
improved. In particular, now importing the engine as a library will not
change the way the SIGTERM, SIGINT and SIGHUP signals are managed, an ugly
side effect of previous releases of the engine. 

Bug fixes
-----------

1. There was a bug in the management of the disaggregation variable
`iml_disagg`: now the IMTs are correctly normalized. Without the fix,
using "SA(0.7)" in `iml_disagg` and "SA(0.70)" in the vulnerability
functions (or viceversa) would have raised an error.

2. When reading the site model in CSV format (a recently introduced
feature) the field names were not ordered and `vs30measured` was read
as a float, not as a boolean. This caused an error which has been
fixed.

3. There was a bug while exporting the hazard curves in the case of
GMPETables (i.e. for the Canada model). It has been fixed.

4. There was also a bug in the GMF export when the GMFs were
originally coming from a CSV file, a regression introduced in engine
3.4. It has been fixed.

5. We were losing line number information when parsing invalid
gsim_logic_tree.xml files: now the error message contains the right
line number.

6. There was a bug when using `applyToSources` with `applyToBranches`
in source model logic tree with multiple source models. It has been
fixed and now it is actually required to specify `applyToBranches` in
such situations.

7. It was impossible to export individual hazard curves from an event based
calculations, since only the statistical hazard curves were stored. The issue
has been fixed.

oq commands
-----------

1. We extended the command `oq prepare_site_model` to work with sites.csv files
and not only exposures. This make it possible to prepare the site model files
for hazard calculations, when the exposure is not know.

2. We extended the command `oq restore` to download from URLs and to
change the calculation owner: as a consequence, we have now an
official mechanism to distribute engine calculations as a zip archive
of HDF5 files.

Deprecations
--------------------

1. Source model logic trees with more than one branching level are deprecated
and raise a warning: they will raise an error in the future.

2. Windows 7 is deprecated as a platform for running the engine since it is
reaching the [End-of-Life](https://www.microsoft.com/en-us/windowsforbusiness/end-of-windows-7-support).

Removals
------------------------

1. We removed the dependency from rtree. Now it is a bit easier to install
the engine on Python 3.7 where the rtree wheel is not available.

2. We changed a bit the web API used by the QGIS plugin and removed
the endpoints `aggregate_by/curves_by_tag` and `aggregate_by/losses_by_tag`.
They were experimental and we have now a better way to perform the aggregations.

3. We removed the 'gsims' column from the realizations output since it was
buggy (the names of the GSIMs could be truncated for long lists) and not
particularly useful.

4. We removed from the engine the ability to compute insured
losses. This feature has been deprecated for a long time and was also
buggy for scenario_risk. Users wanting the feature back should talk
with us.

5. We removed the parallel reading of the exposure introduced in engine v3.4
since it was found buggy when used with the ebrisk calculator. It may return
in the future.
