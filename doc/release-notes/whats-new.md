Release notes v3.27
===================

With more than 470 pull requests, version 3.27 is our largest release to
date in terms of new capabilities, performance improvements, and bug fixes.

The complete set of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.27/debian/changelog

Users who do not need the latest features and models may want to stay with
the LTS release, currently at version 3.23.5.

# Hazard

## Logic trees: new features and optimizations

Two new kinds of logic trees have been introduced: site amplification
logic trees (by Christopher Brooks) and probabilistic fault displacement
logic trees (by Yen-Shin Chen).

Site amplification logic trees are documented in
[Site model inputs](https://docs.openquake.org/oq-engine/engine-3.27/manual/user-guide/inputs/site-model-inputs.html#amplification-logic-trees).
Test cases 26 and 27 in `qa_tests_data/logictree` demonstrate their use.

Probabilistic displacement logic trees are documented in
[Probabilistic fault displacement](https://docs.openquake.org/oq-engine/engine-3.27/manual/user-guide/advanced/probabilistic-fault-displacement.html).
The `demos/hazard/DisplacementPSHA` demo exercises the new probabilistic
fault-displacement calculator. Use it with
`calculation_mode = displacement` and the required
`pfd_logic_tree_file`, which selects from a library of 35 primary and
secondary rupture and displacement models contributed by Yen-Shin Chen.

Both types of logic trees are new and should currently be considered
experimental.

Two new source logic-tree uncertainties have been added:

- `minMagGRAbsolute` replaces the minimum magnitude of a truncated Gutenberg–Richter MFD
- `multiMFDAbsolute` replaces the MFDs of all points in a multi-point source.

There are also three new uncertainties specific to the BCHydro project:

- `recurSet` selects the recurrence model and maximum magnitude
- `recurRow` selects recurrence parameters, such as b-value, reference magnitude, and rate
- `rateSplit` sets how the rate is divided between background and fault sources.

A major optimization now handles logic trees that generate variations of
a base source with different magnitude-frequency distributions. This
case is extremely common in site-specific analyses. Thanks to the BCHydro
project, the engine handles this efficiently, with a measured 60-fold
speedup.

We also removed a limitation of the previous implementation that made it
impossible to run calculations with variant sources and too many
realizations (approximately more than 60,000).

The internals of the classical calculator and the logic tree
management are now documented in [Management of the uncertainties]
(https://docs.openquake.org/oq-engine/engine-3.27/manual/user-guide/advanced/classical-internals.html#management-of-the-uncertainties).

The engine is able to detect models where variant sources are
treated inefficiently and issue a warning. The warning suggests running
`oq check_input job.ini --optimize`, which rewrites the source models and
logic tree so the variant-source optimization can be applied. This makes
little difference for the GEM Mosaic models, but it can have a large
effect elsewhere. For example, the optimization speeds up a French model
used by EDF by a factor of 32.

As a consequence of the changes to event-based calculations with variant
sources, the sampled events may differ from previous versions even with
the same `random_seed`, while remaining statistically consistent.

## Classical PSHA: performance improvements

We revisited the `ps_grid_spacing` optimization. It is now much more
precise—about an order of magnitude more precise—and often faster.
Maximum errors of around 10%, which were relatively common before, are
now below 1%.

We now use a fixed global grid, avoiding a bug that caused distant sources
to change results for nearby sources. `ps_grid_spacing` can also be used
with `disagg_by_src`; previously, it could not.

A new command, `oq engine --calibrate job.ini`, automatically determines
the best combination of `ps_grid_spacing` and `pointsource_distance`.
We also introduced an experimental `collapse_precision` approximation to
reduce the number of contexts evaluated for Poissonian sources.
A new section in the documentation explains the performance
approximations:
https://docs.openquake.org/oq-engine/engine-3.27/manual/user-guide/advanced/performance-approximations.html

We introduced a few job parameters useful for debugging and performance work:

- `filter_sourcecodes` (keep only sources with the specified codes)
- `keep_rupdata` (set it to false to avoid storing rupture data when there
  are few sites)
- `collapse_precision` (for performance, see above)

Reading large source models, building contexts, evaluating PoEs, and
distributing tasks have been optimized. The area-source
discretization is up to 4.8 times faster. For example, building the
composite source model of AUS is now more than three times faster than
before. The preclassical phase of large calculations is generally faster,
despite the additional calibration phase.

The context arrays are now passed to the GMPEs in chunks of at most 10,000
rows. This keeps the arrays in the processor's L2 cache and can make a
significant difference. For instance, in the Tonga model, the
"computing mean_std" operation became five times faster.

The engine now records the number of contexts in the `nctxs` dataset and
provides the `oq show context_reduction` view, which displays the
reduction factors due to gridding, `pointsource_distance`,
`collapse_precision` and the variant-sources optimization.

Other performance improvements include faster Joyner-Boore distances for
2D meshes (about four times faster in the Alaska model), an improved
source-weighting algorithm, parallel hazard-curve building even with few
sites, and a `save_rates` phase that is 200 times faster in BCHydro-style
calculations.

Finally, classical calculations now use much less memory for
nonparametric sources with gridded ruptures. These are saved in the
datastore as arrays instead of pickles, using about three times less
memory.

## Global Stochastic Event Set

Global SES rupture IDs are now unique across models (note that
existing SES.hdf5 files must be regenerated).

The `gmf_data` exporter now handles filtered events and writes
the correct event IDs.

Exports and inspection commands now correctly handle each model's
realizations and logic-tree views.

## Hazardlib

Amir Banimahd contributed the Banimahd et al. (2026) ground-motion
model for Türkiye.

Savas Ceylan contributed period-selectable Swiss site-specific SA
corrections, which can be applied with `ModifiableGMPE`; only the site
columns for the selected periods are required.

The Novakovic et al. (2018) model is available for induced seismicity.

The Campbell and Bozorgnia (2019) CAV and IA model has been moved to its
own module. This also fixes a units error: CAV is now returned in g-sec
rather than m/s. Thanks to Ozan Bilal and Kyle Smith for reporting it.

CampbellBozorgnia models now apply the epistemic adjustment
correctly. Thanks to Mohsen Kohrangi for the report.

The `GridAdjustedGMPE` ground motion model now supports epsilon
scaling, allowing users to specify the epsilon used by the
adjustment. Ray tracing for grid-adjusted models has also been
substantially accelerated (more than 10x) and uses less memory.

The Allen (2022) model now checks whether Vs30 values are in its
calibrated range of 220-800 m/s (thanks to Anthony Carapetis). The
default (`vs30_strict=true`) raises an error for out-of-range values;
`vs30_strict=false` clamps them to the calibrated range.

The US NSHM variant of the CEUS nonlinear site term now includes the Vs30
floor (200 m/s) and rock PGA cap (1 g) described by Powers et
al. (2026).

The ASK14 model supports an aftershock term. For ruptures marked as
aftershocks in a `delta_rates` CSV file, users can specify the centroid
Joyner-Boore distance (`Crjb`) used by that term.

The CanadaSHM6 hard-rock correction now uses the actual Vs30 values.
Previously, the code passed the `vs30_ge1100` boolean mask instead of
Vs30 values, so hard-rock sites were corrected as if Vs30 were 1 m/s.

We fixed the ACME 2019 models' total sigma and interpolation.

The Bayless and Abrahamson (2018) model now corrects high-frequency
total sigma and missing mean predictions near 24 Hz. It applies the
missing smoothing step to the nonlinear site term and interpolates the
computed log EAS and standard deviations for off-grid frequencies.

The `horiz_comp_to` job parameter converts horizontal components to
targets such as geometric mean, RotD50, and RotD100, using the ratios
tabulated by Beyer & Bommer (2006) and Boore & Kishida (2017). The old
`horiz_comp_to_geom_mean` boolean is still accepted as an alias for
`horiz_comp_to = geometric_mean`, but it should be considered deprecated.

Planar rupture contexts now supply the closest-point coordinates
requested by ground-motion models, including the combined `clon_clat`
parameter used by the nonergodic Zhao et al. (2016) slab model.

The new `dip_spacing = inferred` setting for simple fault sources adjusts
the rupture mesh spacing to fit the fault width. The default,
`dip_spacing = mesh_spacing`, keeps the rupture mesh spacing unchanged.

The piecewise linear magnitude-dependent rupture aspect ratio can now
use more than two entries, which is useful for approximating a generic
aspect-ratio function.

Kite fault surface geometry calculations have been corrected and made
more robust. The regression cases showed minor changes in Türkiye.

Simple fault rupture floating now preserves the intended weights of the
hypocentral depth distribution.

The signature of the `MultiPointSource` class has been changed to be
consistent with all the other parametric sources. If your code
uses the old signature, you will get a very clear error message
explaining which arguments have to be swapped.

## Bug fixes

IMT-dependent logic-tree weights are now used correctly when computing
hazard-curve statistics, fixing a regression in Canada's national hazard
model. We also preserve precision for small rates.

Atomic groups are computed for every site label, and disaggregation
retains ruptures from all groups. Those bugs affected the USA and
Japan model, but the numeric differences are minor.

Disaggregation calculations had a bug in mean-curve realization ranking.
It did not affect Global Hazard Mosaic results: the GHM uses the fast
mean path, while the bug affected the slow mean path.

A missing normalization factor in conditional-spectrum calculations has
been added.

Setting `maximum_rupture_depth` now discards deeper ruptures without
raising an assertion error.

Requests for quantile hazard maps without mean outputs no longer cause
crashes.

Postclassical and fast-mean calculations no longer crash on hazard chunks
with no sites.

The ASCE7 postprocessors no longer crash when the source logic tree has
different realization counts or when an IMT has no deterministic source.

The deterministic MCE sigmas are now combined in quadrature, and GSIM
weights are matched to the actual source groups. Together, these
corrections change AELO MCE results, including a 34% increase in PGA for
PAC and a 0.8% increase in KOR in the regression cases.

Site-model association respects a job-file `z1pt4` override when using
`sites_csv` and reports missing required site parameters instead of
silently producing zero hazard.

Event-based rupture extraction (`get_ebruptures`) now reads each
rupture's tectonic region type from its own source group. Previously, it
used the first TRT for all ruptures.

The error message "too many potential logic tree paths" now explains
when `use_rates` can help.

## Other

The Hazard Modeller's Toolkit (HMTK) is no longer bundled with the
engine, since it has been moved into the OpenQuake Model
Building Toolkit (OQ-MBTK).

# Correlation models and conditioned GMFs

The correlation models have been reorganized into a common library, with
one module per model and backward-compatible legacy imports. The
`oq info correlation` command lists the available models by type and
name. The new or newly enabled models include:

- Baker and Bradley (2017) empirical cross-IMT correlation;
- Du and Ning (2021) within-event joint spatial and cross-IMT
  correlation;
- Wang and Du (2013) joint spatial and cross-IMT correlation;
- Markhvida et al. (2018) joint spatial and cross-IMT correlation;
- Schiappapietra et al. and Aldea et al. (2022) within-event spatial
  correlation;
- Monteiro et al. (2026) within-event joint spatial and cross-IMT
  correlation;
- Loth and Baker (2013) joint spatial and cross-IMT correlation, with
  circulant embedding;
- Abrahamson et al. (2014) between-event and within-event cross-IMT
  correlation for PGA-SA-PGV.

The conditioned GMF calculator now supports memory-efficient circulant
embedding on large regular grids, local Kriging for off-grid stations,
and scalable station-conditioned correlated GMF calculations.

The `correlation_strategy` parameter selects either
`cholesky_decomposition` or `circulant_embedding`. In impact mode, it is
set automatically to `circulant_embedding`.

The correlation parameters have been renamed to distinguish the residual
component. `ground_motion_correlation_model` and
`ground_motion_correlation_params` are now
`within_event_correlation_model` and `within_event_correlation_params`.
The `cross_correlation` parameter has been replaced by
`between_event_correlation_model` or, for the conditional spectrum,
`total_residual_correlation_model`. The old names are still accepted for
compatibility, but new job files should use the new names.

# Risk: New Features

Scenario damage calculations can treat tsunami as an independent peril.

Connectivity calculations support infrastructure interdependencies
through a postprocessor. The feature is experimental and not
documented yet, but there is an example under
`openquake/qa_tests_data/infrastructure_risk/interdependencies`. The
interdependencies analysis requires `aggregate_by = id` in both the
parent and the child calculation, since the assets are identified by
their index.

When `time_event` is not specified, scenario risk calculations now
compute occupant and injury losses for whichever of the day, night,
transit, and average periods are present in the exposure. If you want
the old behaviour, set `time_event = avg`. Some outputs use `occupants_avg`
instead of `occupants` for the average occupancy losses.

The engine supports regular UTM site grids prepared from exposure data,
site CSV files, or scenario ruptures. This is crucial for
circulant-embedding calculations and is implemented by
`oq prepare_site_model`.

The impact API can provide authorized users with provenance information
about the scientific model repositories used to build the global
exposure. Impact calculations can generate multi-page country reports
with `make_impact_reports = true`. The report includes the input `notes`
and the selected time of day, specified with the `report_time_event`
parameter. The impact form defaults to a `region_grid_spacing` of 1 km.

# Risk: new optimizations and fixes

One change doubled the speed of Global Risk Model calculations:
vectorizing random-number generation for unique events (`rng.beta`). This
operation had been the main performance bottleneck.

Scenario aggregate risk quantiles are now correctly computed from the
total portfolio losses per event.

Damage calculations now handle multiple loss types and
perils without overstating undamaged buildings or producing incorrect
building counts.

Fully correlated losses are combined correctly across
taxonomies and exposure chunks.

Average losses are now assigned to the correct realization, and exceeding
`avg_losses_max` with `collect_rlzs=false` raises an error as expected.

Classical risk handles assets of different taxonomies at the same site
without misplacing their loss curves or average losses.

ShakeMap `grid.xml` values are now treated as medians. Previously they
were treated as arithmetic means, causing an inappropriate mean-to-median
conversion before generating ground-motion fields.

# IT

## OQ commands
I wa
- `oq -v` returns the Git hash in development installations, now reliably also on
  `devel_server` installations
- `oq engine --param` now accepts space-separated `name=value`
  pairs, matching `oq run --param`, instead of comma-separated pairs
- `oq engine --make-report` now generates a Markdown report instead of an
  HTML report
- `oq show rlz` now pairs branches with their uncertainty types
- `oq info logic_trees` lists the available logic tree classes
- `oq show usignatures` displays the uncertainty signatures of a
  calculation, and `oq show context_reduction` displays the reduction of
  the contexts
- `oq check_input` command prints uncertainty signatures and
  logic tree core size without running the calculation
- `oq extract agg_losses` works when calculations are aggregated by ID
  and reports the correct `site_id` tags
- The `avg_gmf` extractor omits zero values by default. Set
  `filter_zeros=0` to retain them; the CSV exporter does this to keep site
  rows aligned across IMTs.
- `oq sample` can now manage ESRI `.asc` files and reduce SES HDF5 files.
- `oq compare workflow` compares the mean hazard maps of a workflow
  with exported CSV files

## WebUI

The WebUI calculation list is now paginated (10 items by default,
configurable with `CALC_LIST_PAGE_SIZE`).

Extracted HTML tables can be sorted by column.

The WebUI has a "Download zip" button.

The WebUI supports sharing and unsharing jobs through a Django
permission. Authorized job owners can share their jobs with other users,
while level-2 users cannot share or unshare jobs they do not own.

The WebUI now uses Django 5.2 LTS and django-cookie-consent 1.0.
On Red Hat Enterprise Linux 8 and its derivatives, this Django version
requires SQLite 3.31 or newer.

## Other IT

We upgraded numpy to version 2.4.6, SciPy to version 1.17.1, Numba to
version 0.67.0, GDAL to version 3.13.1, GeoPandas to 1.1.4, and pyogrio
to version 0.12.1, along with other libraries, to include the latest
security fixes.

If a large ZeroMQ packet is lost under high throughput, the calculation
now fails with a clear error instead of hanging indefinitely.

The repository now includes an AI contribution policy in `AI_POLICY.md`.
