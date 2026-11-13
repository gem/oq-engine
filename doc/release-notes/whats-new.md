Release notes (dev)
===================

Version 3.27 is the largest release ever in terms of new capabilities,
performance improvements and bug fixes, involving over 400 pull
requests.

The complete set of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.27/debian/changelog

Users who do not need the latest features and models may want to stay with the LTS
release, currently at version 3.23.5.

A summary is given below.

# IT

This is first release making heavy use of the newest AI tools
(i.e. Codex, Claude and others) in the engine codebase. As a
consequence we identified and fixed substantially more bugs than
usual. We also used AI to implement new features and to
improve our optimizations.
We also used it in purely IT work, like the removal the DbServer
service, which is now included in the WebUI service (that is only
relevant for server installations, see
https://docs.openquake.org/oq-engine/manual/engine-3.27/getting-started/installation-instructions/server.html).

# Hazard

## Classical PSHA: performance improvements

There is a major new optimization for the case of logic trees
generating variations of a base source with different MFD
parameters (see https://docs.openquake.org/oq-engine/engine-3.27/manual/user-guide/advanced/performance-approximations.html#variant-sources-optimization). This case is extremely common when performing site
specific analysis and much less common in continental scale
calculations, the reason why it has stayed unoptimized until now.
Thanks to a project with BCHydro this case is now managed properly
by the engine, resulting in a huge speedup. For instance a model
generating 100 variations of the a, b and mmax parameters for
each source will now compute the geometries, mean and stddevs
and generate the poes only once instead of 100 times. The speedup
is not 100x, since some time has to be spent multipling the 100
versions of the occupancy rates with the poes, but still pretty
large (we measured a 32x). Also, as a consequence of this project,
the implementation of the logic tree is much cleaner and for the
first time we are documenting some of the internals here:

https://docs.openquake.org/oq-engine/engine-3.27/manual/user-guide/advanced/classical-internals.html#management-of-the-uncertainties

Source uncertainties are now applied in the workers, one set of
realizations at a time, for classical and event-based calculations. In
event-based calculations, event samples can differ for the same
`random_seed`, while remaining statistically consistent. The new
`oq show usignatures` view summarizes the uncertainty signatures associated
with realizations. This is relevant only in the context of variant sources.

Moreover, we revisited the old ``ps_grid_spacing`` optimization, which
is now much more precise that it used to be (around an order of
magnitude more precise, i.e. common 10% maximum errors are now less
than 1%) and often faster. A fixed global grid is now used, thus
avoiding a bug causing distant sources to change the results for
nearby sources.

There is a new `oq run job.ini --calibrate -p ps_grid_spacing=auto` command to
automaticallt determine the best combination of `ps_grid_spacing` and `pointsource_distance`.
The approximation can now also be used with `disagg_by_src`.

We also introduced an experimental `collapse_precision` approximation to reduce the number of
contexts evaluated for Poissonian sources and
there is an entire new section in the docs explaining the various performance approximations:
https://docs.openquake.org/oq-engine/master/manual/user-guide/advanced/performance-approximations.html

Classical calculations use less memory for nonparametric sources with
gridded ruptures, which are stored as arrays.

Reading large source models,
building contexts, evaluating PoEs, and distributing tasks have been
optimized.

The area-source discretization is much faster.

## Classical PSHA: new features

Two new kinds of logic trees have been introduced:
site amplification logic trees (by Christopher Brooks) and probabilistic fault displacement
logic trees (by Yen Shin Chen).

There is also a new probabilistic fault-displacement calculator with
35 primary and secondary rupture and displacement models, all
contributed by Yen Shin Chen. An example of usage is in
demos/hazard/DisplacementPSHA while the documentation is in
https://docs.openquake.org/oq-engine/manual/engine-3.27/user-guide/advanced/probabilistic-fault-displacement.html
It should be considered experimental for the moment.

Amplification logic trees are not documented yet, but there are examples
in qa_tests_data/logictree (case_26 and case_27).

## Ground-motion models and correlation

`GridAdjustedGMPE` supports epsilon scaling, allowing users to specify the
epsilon used by the adjustment. Ray tracing for grid-adjusted models has
also been substantially accelerated and uses less memory.

The Allen (2022) model now checks whether Vs30 values are in its calibrated
range of 220–800 m/s. The default `vs30_strict=true` raises an error for
out-of-range values; `vs30_strict=false` clamps them to the calibrated range.
The US NSHM variant of the CEUS nonlinear site term includes the Vs30 floor
and rock PGA cap described by Powers et al. (2026).

The ASK14 model supports an aftershock term. For ruptures marked as
aftershocks in a `delta_rates` CSV file, users can specify the centroid
Joyner-Boore distance (`Crjb`) used by that term.

New ground-motion models include Banimahd et al. (2026) for Türkiye and
Novakovic et al. (2018) for induced seismicity. The Monteiro et al. (2026)
within-event model adds joint spatial and cross-IMT correlation for
RotD50 spectral acceleration, PGA, PGV, and selected cumulative intensity
measures.

The `oq info correlation` command lists the available correlation models.

# Risk

Connectivity calculations now support infrastructure interdependencies.
The feature is experimental and not documented yet, but there is an
example under openquake/qa_tests_data/infrastructure_risk/interdependencies.

Scenario damage calculations can treat tsunami as an independent peril.

When `time_event` is not specified, scenario risk calculations now compute
occupant and injured losses for day, night, and transit, according to the
time periods available in the exposure.

The engine now supports regular UTM site grids prepared from exposure, site CSV
files, or scenario ruptures: this is crucial for circulant-embedding calculations.

# hazardlib

The `horiz_comp_to` job parameter converts horizontal components to targets
such as geometric mean, RotD50, and RotD100. The former
`horiz_comp_to_geom_mean` boolean remains supported for backwards
compatibility.

Magnitude-dependent aspect-ratio expressions can now contain more than two
entries.

# Bug fixes

## Hazard and disaggregation

IMT-dependent logic-tree weights are now used correctly in fast mean hazard
curves and source-rate distributions. The fast mean calculation also
preserves precision for small rates. Source-rate attribution now handles
multiple atomic groups and IMT-dependent weights correctly. Atomic groups
are computed for every site label, and disaggregation retains ruptures from
all groups. The mean-curve realization ranking and conditional spectra
normalization have also been corrected.

With `maximum_rupture_depth`, ruptures deeper than the limit are now
discarded without an assertion failure.

Requests for quantile hazard maps without mean outputs no longer crash.
The `ps_grid_spacing` grid no longer depends on the bounding box of a
source group, and point-source gridding near the antimeridian is handled
correctly.

Postclassical and fast-mean calculations no longer crash on hazard chunks
with no sites.

ShakeMap `grid.xml` values are now treated as medians. Previously, they were
treated as arithmetic means, causing an inappropriate mean-to-median
conversion before generating ground-motion fields.

The ASCE7 postprocessors no longer crash when the source logic tree has
different realization counts or when an IMT has no deterministic source.
Their deterministic MCE sigmas are combined in quadrature, and GSIM weights
are matched to the actual source groups. Together, these corrections change
AELO MCE results, including a 34% increase for PGA in PAC and a 0.8%
increase in KOR in the regression cases.

## Risk and exports

Scenario aggregate risk quantiles are computed from total portfolio losses
per GMF. Damage calculations now handle multiple loss types and perils
without overstating undamaged buildings or producing incorrect building
counts. Fully correlated losses are combined correctly across taxonomies
and exposure chunks. Average losses are assigned to the correct realization,
and exceeding `avg_losses_max` with `collect_rlzs=false` now raises the
required error.

Classical risk handles assets of different taxonomies at the same site
without misplacing their loss curves or average losses.

The global SES `gmf_data` exporter now handles filtered events and writes
the correct event IDs; global SES rupture IDs are unique across models.

## Inputs, logic trees, and ground-motion models

Magnitude and b-value uncertainties are applied to large multi-point
sources, and `applyToSources` matches sources with branch-suffixed IDs.
Site-model association respects a job-file z1pt4 override from `sites_csv`
and reports missing required site parameters instead of silently producing
zero hazard. `oq show rlz` now pairs branches with their uncertainty types.
Event-based rupture extraction now reads each rupture's tectonic region type
from its own source group.

The CanadaSHM6 hard-rock correction now uses the actual Vs30 values.
Before it was incorrectly giving always the same correction, the
one for vs30 < 1100 m/s.

We fixed the ACME 2019 models correct total sigma and interpolation.

CampbellBozorgnia models now apply the epistemic adjustment and
basin terms correctly. Thanks to Mohsen Kohrangi for the report.

CampbellBozorgnia2019 CAV values are now returned in g-sec and not in m/s
(thanks to Ozan Bilal and Kyle Smith for the report).

# oq commands

There were minor fixes in the `oq compare` commands, as well in the
`oq show rlz`, `oq show branches`, `oq show branchsets`, `oq show
sm_rlzs` commands, that now also works for multi-model calculations,
such as global SES calculations.

The `oq extract agg_losses` exporter works for aggregation by ID and reports
the correct site tags.

`oq engine --param` now accepts space-separated `name=value` pairs, matching
`oq run --param`, while command-separated pairs are not accepted anymore.

`oq info logic_trees` show the available logic tree classes.
