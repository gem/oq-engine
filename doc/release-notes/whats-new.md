Release notes v3.27
===================

Version 3.27 is the largest release ever in terms of new capabilities,
performance improvements and bug fixes, involving more than 450 pull
requests.

The complete set of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.27/debian/changelog

Users who do not need the latest features and models may want to stay with
the LTS release, currently at version 3.23.5.

# Hazard

## Classical PSHA: variant sources

There is a major new optimization for the case of logic trees generating
variations of a base source with different magnitude-frequency
distributions. This case is extremely common in site-specific analyses and
much less common in continental-scale calculations, which is why it had
remained unoptimized until now. Thanks to a project with BCHydro the case
is now managed properly by the engine, with a large speedup (we measured
a 60x).

Moreover we removed a limitation of the previous implementation that made it impossible
to run the BCHydro calculation with full numeration. The internals of the classical calculator
and the logic tree management are now finally documented in
[Management of the uncertainties](https://docs.openquake.org/oq-engine/engine-3.27/manual/user-guide/advanced/classical-internals.html#management-of-the-uncertainties).

The engine is now able to detect models where variant sources are
treated inefficiently and to raise a warning in that case. The warning
suggests to run `oq check_input job.ini --better-smlt` which will
rewrite the source models and the logic tree file in such a way that
the variant sources optimization can be applied. In the GEM mosaic
models this will hardly make a difference, however there a cases were
the difference is impressive (we have a model for France use by EDF where
the variant sources optimization gives a 32x speedup).

Note: as a consequence of the change in event-based calculations with
variant sources the event samples can differ for the same
`random_seed`, while remaining statistically consistent.

## Classical PSHA: performance improvements

We revisited the old `ps_grid_spacing` optimization, which is now much
more precise than it used to be (around an order of magnitude more
precise, i.e. 10% maximum errors which were relatively common before
are now below 1%) and often faster. Moreover, we are now using a fixed global grid,
thus avoiding a bug that caused distant sources to change the results
for nearby sources.

There is a new commands `oq engine --calibrate job.ini`
that automatically determines the best combination of
`ps_grid_spacing` and `pointsource_distance`. The approximation can now
also be used with `disagg_by_src`, provided the calculation has few sites.

We also introduced an experimental `collapse_precision` approximation to
reduce the number of contexts evaluated for Poissonian sources. Sources
with equivalent ground-motion requirements can share collapsed contexts.
There is an entire new section in the docs explaining the performance
approximations:
https://docs.openquake.org/oq-engine/engine-3.27/manual/user-guide/advanced/performance-approximations.html

Classical calculations use less memory for nonparametric sources with
gridded ruptures, which are now stored as arrays (about 3x less memory).
Reading large source models, building contexts, evaluating PoEs, and
distributing tasks have also been optimized. In the `performance.zip`
demo `get_poes` decreased from 1,324 to 899 seconds. The area-source
discretization in preclassical calculations is up to 4.8 times faster
(for the AUS model, the rupture floating factor went from 29 seconds to
1 second). Building the composite source model of AUS now takes 77
seconds instead of 252, and unpickling the preclassical results of
Melbourne went from 108 to 15 seconds.

The contexts are now passed to the GMPEs in chunks of at most 10,000
rows, since the GMPEs are memory-bound on very large arrays: in the Tonga
model with `ps_grid_spacing=50` the "computing mean_std" phase went from
43,645 to 8,756 seconds.

The engine now records the number of contexts in the `nctxs` dataset and
provides the `oq show context_reduction` view, which displays the
reduction factors due to gridding, `pointsource_distance`,
`collapse_precision` and the variant-sources optimization.

Classical calculations with `disagg_by_src` send smaller packets from
workers. If a ZeroMQ packet is lost, the calculation now fails with an
error instead of continuing with incomplete data.

Other performance work includes faster Joyner-Boore distances for 2D
meshes (about 4x in an Alaska calculation), a better source weighting
algorithm, parallel hazard-curve building even with few sites, a 200x
faster `save_rates` phase in BCHydro-style calculations, and a
vectorized `MultiEventRNG.beta` that doubles the speed of the Global
Risk Model.

## Classical PSHA: new features

Two new kinds of logic trees have been introduced: site amplification
logic trees (by Christopher Brooks) and probabilistic fault displacement
logic trees (by Yen-Shin Chen).

Site amplification logic trees are configured with
`ampl_logic_tree_file`, a NRML XML file with a single
`uncertaintyType="amplificationModel"` branchset. They are now supported
in disaggregation calculations as well, and are documented in
[Site model inputs](https://docs.openquake.org/oq-engine/engine-3.27/manual/user-guide/inputs/site-model-inputs.html#amplification-logic-trees).

There is also a new probabilistic fault-displacement (PFD) calculator
with 35 primary and secondary rupture and displacement models, all
contributed by Yen-Shin Chen. It is used with
`calculation_mode = displacement` and a mandatory
`pfd_logic_tree_file`; the intensity measure type is `Disp` and the
levels are displacements in meters. An example of usage is in
`demos/hazard/DisplacementPSHA`, while the documentation is in
[Probabilistic fault displacement](https://docs.openquake.org/oq-engine/engine-3.27/manual/user-guide/advanced/probabilistic-fault-displacement.html).
It should be considered experimental for the moment.

New job parameters useful for debugging and performance work include
`filter_sourcecodes` (keep only sources with the given codes),
`keep_rupdata` (store rupture data also when there are many sites) and
`collapse_precision` (see above).

For simple fault sources, set `dip_spacing = inferred` in the job file to
adjust the down-dip mesh spacing to fit the fault width. The default,
`dip_spacing = mesh_spacing`, uses the rupture mesh spacing unchanged.
The piecewise linear magnitude-dependent rupture aspect ratio can now
use more than two entries.

Two new source logic-tree uncertainties are available.
`minMagGRAbsolute` replaces the minimum magnitude of a truncated
Gutenberg–Richter MFD, and `multiMFDAbsolute` replaces the MFDs of all
points in a multi-point source.

## Ground-motion models and correlation

`GridAdjustedGMPE` supports epsilon scaling, allowing users to specify the
epsilon used by the adjustment. Ray tracing for grid-adjusted models has
also been substantially accelerated (more than 10x) and uses less memory.

The Allen (2022) model now checks whether Vs30 values are in its
calibrated range of 220-800 m/s. The default `vs30_strict=true` raises an
error for out-of-range values; `vs30_strict=false` clamps them to the
calibrated range. The US NSHM variant of the CEUS nonlinear site term
includes the Vs30 floor (200 m/s) and rock PGA cap (1 g) described by
Powers et al. (2026).

The ASK14 model supports an aftershock term. For ruptures marked as
aftershocks in a `delta_rates` CSV file, users can specify the centroid
Joyner-Boore distance (`Crjb`) used by that term.

New ground-motion models include Banimahd et al. (2026) for Türkiye and
Novakovic et al. (2018) for induced seismicity. The Campbell and
Bozorgnia (2019) CAV and IA model has been split into its own module,
fixing a units error (CAV is now returned in g-sec rather than m/s).

The `horiz_comp_to` job parameter converts horizontal components to
targets such as geometric mean, RotD50 and RotD100, using the ratios
tabulated by Beyer & Bommer (2006) and Boore & Kishida (2017). The old
`horiz_comp_to_geom_mean` boolean is still accepted as an alias for
`horiz_comp_to = geometric_mean`.

## Correlation models and conditioned GMFs

The correlation models have been reorganized into a common registry, with
one module per model and backward-compatible legacy imports. The
`oq info correlation` command lists the available models by type and
name.

The new or newly enabled models include:

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

The conditioned GMF calculator can now use memory-efficient circulant
embedding on large regular grids, local Kriging for off-grid stations,
and scalable station-conditioned correlated GMFs. The
`correlation_strategy` parameter selects between
`cholesky_decomposition` and `circulant_embedding`; it is set
automatically to `circulant_embedding` in impact mode.

```{warning}
The correlation parameters have been renamed to distinguish the residual
component. `ground_motion_correlation_model` and
`ground_motion_correlation_params` are now
`within_event_correlation_model` and `within_event_correlation_params`.
The `cross_correlation` parameter is now
`between_event_correlation_model` or, for the conditional spectrum,
`total_residual_correlation_model`. The old names are still accepted for
compatibility, but new job files should use the new names.
```

# Risk

Connectivity calculations now support infrastructure interdependencies
through a postprocessor. The feature is experimental and not documented
yet, but there is an example under
`openquake/qa_tests_data/infrastructure_risk/interdependencies`. The
interdependencies analysis requires `aggregate_by = id` in both the
parent and the child calculation, since the assets are identified by
their index.

Scenario damage calculations can treat tsunami as an independent peril.

When `time_event` is not specified, scenario risk calculations now
compute occupant and injured losses for day, night, transit and average,
limited to the periods present in the exposure. The default `time_event`
is now unset instead of `"avg"`, and some outputs use `occupants_avg`
instead of `occupants` for the average occupancy losses. The impact
interface and reports show the selected time of day through the
`report_time_event` parameter.

The engine supports regular UTM site grids prepared from exposure, site
CSV files or scenario ruptures. This is crucial for
circulant-embedding calculations and is implemented by
`oq prepare_site_model`.

The impact API can provide authorized users with provenance information
about the scientific model repositories used to build the global
exposure. The WebUI calculation list is paginated (10 items by default,
configurable with `CALC_LIST_PAGE_SIZE`), extracted HTML tables can be
sorted by column, and the WebUI has a "Download zip" button. Impact
calculations can generate multi-page country reports with
`make_impact_reports = true`; the input `notes` are shown in the report.
The default `region_grid_spacing` of the impact form is 1 km.

# WebUI, server and IT

The WebUI now uses Django 5.2 LTS and django-cookie-consent 1.0.

The WebUI supports sharing and unsharing jobs through a Django
permission: authorized job owners can share their jobs with other users,
while level-2 users cannot share or unshare jobs they do not own.

We upgraded numpy to version 2.4.6, SciPy to version 1.17.1, Numba to
version 0.67.0, GDAL to version 3.13.1, GeoPandas to 1.1.4, pyogrio to
0.12.1.

We recommend Python 3.13, although versions 3.11 to 3.13 are supported.

The repository now includes an AI contribution policy in `AI_POLICY.md`.

# Other commands and exports

- `oq engine --make-report` now generates a Markdown report instead of an HTML one.
- `oq engine --param` now accepts space-separated `name=value`
  pairs, matching `oq run --param`; comma-separated pairs are not accepted
  anymore.
- `oq -v` returns the Git hash in a development installation.
- `oq run --calibrate` stops after the calibration of
  `ps_grid_spacing` and `pointsource_distance`, and stores the result in
  the datastore.
- `oq run --mean-rates` prints the mean hazard rates of the first site,
  computed without parallelization.
- `oq run --ct` is an abbreviation for `--concurrent-tasks`.
- `oq check_input --better-smlt` reduces sources with the same geometry
  and different MFDs, and now generates a `job.zip`; the engine also
  warns about sources with different IDs, the same geometry and
  different MFDs, which are likely variants of a base source.
- `oq info logic_trees` lists the available logic tree classes.
- `oq info correlation` lists the correlation models.
- `oq show usignatures` displays the uncertainty signatures of a
  calculation, and `oq show context_reduction` displays the reduction of
  the contexts.
- `oq check_input` command prints the uncertainty signatures and the core
  size of a calculation without running it
- `oq extract agg_losses` now works when the calculation is aggregated by
  id, and the site_id tags of the aggregated losses are correct.
- The `avg_gmf` exporter exports only nonzero values, and the extractor
  accepts an optional `filter_zeros` parameter.
- `oq sample` can now manage ESRI `.asc` files and reduce SES HDF5 files.
- `oq compare workflow` compares the mean hazard maps of a workflow
  with exported CSV files.

# Bug fixes

## Hazard and disaggregation

IMT-dependent logic-tree weights are now used correctly in fast mean
hazard curves and source-rate distributions. The fast mean calculation
also preserves precision for small rates. Source-rate attribution now
handles multiple atomic groups and IMT-dependent weights correctly.
Atomic groups are computed for every site label, and disaggregation
retains ruptures from all groups. The mean-curve realization ranking and
conditional spectra normalization have also been corrected.

With `maximum_rupture_depth`, ruptures deeper than the limit are now
discarded without an assertion failure.

Kite fault surface geometry calculations have been corrected and made
more robust. The regression cases showed minor changes in Türkiye.
Simple fault rupture floating now preserves the intended weights of the
hypocentral depth distribution.

Uncertainty histogram calculations preserve probability mass at zero
rates and retain global uncertainty indices during convolution.

Requests for quantile hazard maps without mean outputs no longer crash.
The `ps_grid_spacing` grid no longer depends on the bounding box of a
source group, and point-source gridding near the antimeridian is handled
correctly.

Postclassical and fast-mean calculations no longer crash on hazard chunks
with no sites.

ShakeMap `grid.xml` values are now treated as medians. Previously they
were treated as arithmetic means, causing an inappropriate mean-to-median
conversion before generating ground-motion fields.

The ASCE7 postprocessors no longer crash when the source logic tree has
different realization counts or when an IMT has no deterministic source.
Their deterministic MCE sigmas are combined in quadrature, and GSIM
weights are matched to the actual source groups. Together, these
corrections change AELO MCE results, including a 34% increase for PGA in
PAC and a 0.8% increase in KOR in the regression cases.

The global SES `gmf_data` exporter now handles filtered events and writes
the correct event IDs; global SES rupture IDs are unique across models.
Existing SES files must be regenerated.

## Risk and exports

Scenario aggregate risk quantiles are computed from total portfolio
losses per GMF. Damage calculations now handle multiple loss types and
perils without overstating undamaged buildings or producing incorrect
building counts. Fully correlated losses are combined correctly across
taxonomies and exposure chunks. Average losses are assigned to the
correct realization, and exceeding `avg_losses_max` with
`collect_rlzs=false` now raises the required error.

Classical risk handles assets of different taxonomies at the same site
without misplacing their loss curves or average losses.

The `oq extract agg_losses` exporter works for aggregation by ID and
reports the correct site tags.

## Inputs, logic trees, and ground-motion models

Magnitude and b-value uncertainties are applied to large multi-point
sources, and `applyToSources` matches sources with branch-suffixed IDs.
Site-model association respects a job-file z1pt4 override from
`sites_csv` and reports missing required site parameters instead of
silently producing zero hazard. `oq show rlz` now pairs branches with
their uncertainty types. Event-based rupture extraction now reads each
rupture's tectonic region type from its own source group.

The CanadaSHM6 hard-rock correction now uses the actual Vs30 values.
Before it was passing the boolean mask of `vs30_ge1100` as the Vs30
values, so hard-rock sites were corrected using a Vs30 of 1 m/s.

We fixed the ACME 2019 models' total sigma and interpolation.

CampbellBozorgnia models now apply the epistemic adjustment
correctly. Thanks to Mohsen Kohrangi for the report.

CampbellBozorgnia2019 CAV values are now returned in g-sec and not in
m/s (thanks to Ozan Bilal and Kyle Smith for the report).

The Swiss site-specific SA corrections can be applied with
`ModifiableGMPE`; only the site columns for the selected periods are
required. For PGA, the correction retains the mean, phi and tau and
recomputes total sigma.

The Bayless and Abrahamson (2018) model now corrects high-frequency
total sigma and missing mean predictions near 24 Hz. It applies the
missing smoothing step to the nonlinear site term and interpolates the
computed log EAS and standard deviations for off-grid frequencies.

Planar rupture contexts now supply the closest-point coordinates
requested by ground-motion models, including the combined `clon_clat`
parameter used by the nonergodic Zhao et al. (2016) slab model.

## Other

Exports and inspection commands for multi-model calculations now handle
each model's realizations and logic-tree views. The `oq compare uhs`
command compares matching IMTs. The "too many potential logic tree
paths" message now explains when `use_rates` can help.

# Upgrading

- The Hazard Modeller's Toolkit (HMTK) is no longer bundled with the
  engine. Its components are planned to move to the OpenQuake Model
  Building Toolkit (OQ-MBTK).
- On Red Hat Enterprise Linux 8 and its derivatives, the Django upgrade
  requires SQLite 3.31 or newer for the WebUI.
- Python callers that construct `MultiPointSource` directly must supply
  `rupture_mesh_spacing` after `mfd` and pass
  `temporal_occurrence_model` after `rupture_aspect_ratio`. The final
  argument is still `mesh`.
- The correlation parameters have been renamed (see the warning above).
  The ShakeMap `spatial_correlation` parameter is obsolete: leave
  `within_event_correlation_model` unset to disable correlation.
- In event-based calculations the events and the results can change for
  the same `random_seed`, since the uncertainties are now applied in the
  workers; they are statistically consistent, but a few expected files
  have been regenerated.
- The global SES rupture IDs are now unique across models, so existing
  SES files must be regenerated.
- The default `time_event` for scenario risk is now unset instead of
  `"avg"`; if you want the old behaviour, set `time_event = avg`.
- When `ps_grid_spacing` is used without `pointsource_distance`, the
  calibrated default is now 25 km instead of 50 km.
- The dataset `trt_smrs_gid` has been renamed `core_trt_smrs`.
- The `horiz_comp_to_geom_mean` boolean is deprecated in favour of
  `horiz_comp_to = geometric_mean`.
- `oq engine --param` now uses space-separated `name=value` pairs;
  comma-separated pairs are not accepted anymore.
