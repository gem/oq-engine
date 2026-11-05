Release notes (dev)
===================

```{warning}
The `[dbserver]` section of `openquake.cfg` does not exist anymore.
Starting from version 3.27 its keys live in the `[server]` section:

- `host`, `receiver_host` and `receiver_ports` keep their names;
- `file` has been renamed `dbfile`;
- the `port` key has been removed;
- the `oq dbserver` command and the DbServer daemon have been removed.

Versions up to 3.26, including the LTS release 3.23, still use the
`[dbserver]` section with the `file` key, so the configuration files
must be updated when upgrading.
```

Version 3.27 adds new capabilities for hazard, risk, and infrastructure
calculations, alongside substantial performance improvements. The complete
list of changes is in the [changelog](https://github.com/gem/oq-engine/blob/master/debian/changelog).

# Hazard

## Classical PSHA

The new `ps_grid_spacing=auto` option compares candidate point-source
approximations against exact results at a sample of sites and chooses a
cost-effective combination of `ps_grid_spacing` and `pointsource_distance`.
The approximation can also be used with `disagg_by_src` for calculations
with few sites.

The experimental `collapse_precision` approximation reduces the number of
contexts evaluated for fault and Poissonian sources. Sources with equivalent
ground-motion requirements can share collapsed contexts. A fixed global
grid is now used to collapse point sources, so distant padding sources do
not change the results for nearby sources.

Classical calculations use less memory for nonparametric sources with
gridded ruptures, which are stored as arrays. Reading large source models,
building contexts, evaluating PoEs, and distributing tasks have also been
optimized. In the performance demo, `get_poes` decreased from 1,324 to
899 seconds. The area-source discretization in preclassical calculations is
up to 4.8 times faster.

Source uncertainties are now applied in the workers, one set of
realizations at a time, for classical and event-based calculations. In
event-based calculations, event samples can differ for the same
`random_seed`, while remaining statistically consistent. The new
`oq show usignatures` view summarizes the uncertainty signatures associated
with realizations.

Magnitude-dependent aspect-ratio expressions can now contain more than two
entries.

Site amplification logic trees can now be used in disaggregation
calculations. They were previously supported only in classical PSHA.

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

The engine now includes a probabilistic fault-displacement calculator with
35 primary and secondary rupture and displacement models. Its logic tree
supports uncertainty across the selected models.

Connectivity calculations support infrastructure interdependencies through
a postprocessor. They can combine asset-level outputs from parent and child
calculations.

Scenario damage calculations can treat tsunami as an independent peril.

When `time_event` is not specified, scenario risk calculations can compute
occupant and injured losses for day, night, and transit, according to the
time periods available in the exposure. The impact interface and reports
show the selected time of day. Country impact reports can span multiple
pages and include the rupture and epicenter when available.

Impact defaults for `maximum_distance` and `truncation_level` can be chosen
from the rupture magnitude. Level 1 users can also set `maximum_distance`
up to 500 km.

The engine supports regular UTM site grids prepared from exposure, site CSV
files, or scenario ruptures for circulant-embedding calculations.

The `horiz_comp_to` job parameter converts horizontal components to targets
such as geometric mean, RotD50, and RotD100. The former
`horiz_comp_to_geom_mean` boolean remains supported for backwards
compatibility.

The impact API can provide authorized users with provenance information
about the scientific model repositories used to build the global exposure.
The WebUI calculation list is paginated, and extracted HTML tables can be
sorted by column.

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
without misplacing their loss curves or average losses. The
`oq extract agg_losses` exporter works for aggregation by ID and reports
the correct site tags.

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

The CanadaSHM6 hard-rock correction uses the actual Vs30 values. Fixes to
the ACME 2019 models correct total sigma and interpolation, and
CampbellBozorgnia models now apply the epistemic adjustment and basin terms
correctly. CampbellBozorgnia2019 CAV values are returned in g-sec.

## Other

Exports and inspection commands for multi-model calculations now handle
each model's realizations and logic-tree views. The `oq compare uhs`
command compares matching IMTs. The `too many potential logic tree paths`
message now explains when `use_rates` can help.

# Other changes

`oq engine --param` now accepts space-separated `name=value` pairs, matching
`oq run --param`.

The complete release changes, including additional optimizations and
internal updates, are listed in the changelog linked above.
