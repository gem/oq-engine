Release notes v3.26
===================

Version 3.26 is the culmination of four months of work involving over
320 pull requests. It is the minimum version able to run the [2026
release of GEM's Global Seismic Hazard and Risk Models]
(https://www.globalquakemodel.org/GEMNews/gem-2026-unveil-new-global-earthquake-risk-products).
Users who do not need the latest models may want to stay with the LTS
release, currently at version 3.23.4.

The complete set of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.26/debian/changelog

A summary is given below.

# Hazard

## Rupture sampling

The performance of the command generating the Global Stochastic Event
Set has been drastically improved by changing the algorithm to
use the multinomial distribution with weights proportional to
the number of samples per source model. That makes over an order
of difference in models with high source multiplicity like New Zealand.

Moreover, by splitting the multifault and multipoint sources in a
smarter way, we were able to reduce the slow tasks and to save
memory. Without these improvements, the Global SES with the latest
models could not run because of out-of-memory errors.

We fixed a rupture sampling bug in the case of mutually exclusive ruptures,
affecting Japan in the Nankai area and the USA model in the New Madrid area.

Moreover, it is now possible to pass the `--cache=true` parameter to the
`global_ses` script to avoid recomputing models.

We now save `year` and `ses_id` in the events dataset, supporting risk 
calculations starting from SES hdf5 files.

We introduced a dictionary `TRT -> maximum_rupture_depth` to discard
very deep ruptures.

We now provide a clear error message in the case of duplicated rupture IDs,
which can only happen if there is a bug in the sampling implementation.

We now manage the `CompositeSourceModel` in the same way in both
classical and event-based calculations. In particular, we
optimized identical sources, reducing the memory consumption for
models such as New Zealand by an order of magnitude while also doubling the
speed.

We also optimized reading and sampling multifault sources by
parallelizing `build_secparams` and splitting the sources
before `preclassical` or `sample_ruptures`.

Finally, we optimized the method `src.count_ruptures()` for multifault
sources.

## Classical PSHA

There was a severe memory bug (producing a list of
contexts instead of an iterator) that caused some models to use several GB
of RAM per core (up to 10 GB). Now all models can be run with less
than 2 GB per core.

We fixed a SourceFiltering bug in the case of a small number of sites, causing
very slow tasks. The improvement in speed can be dramatic (for example,
we measured a 6× speedup in a calculation for MIE).

We fixed a prefiltering bug affecting point sources spanning over 180 degrees
of longitude at the poles (i.e. oceanic sources were incorrectly
discarded).

The mosaic geometries have been fixed. They are now read and validated
using geopandas. The `mosaic.gpkg` file is also included in the internal
checksum logic (i.e. if you change `mosaic.gpkg`, the cache is
invalidated).

We extended the usability of `use_rates = true` to IMT-dependent weights.
As a result, the Canada model can now be computed with full enumeration
even if there are more than 7 million realizations.

We added a warning in the preclassical phase suggesting the use of
`use_rates = true` if only mean curves are required.

In the case of IMT-dependent logic trees, it is now possible to list
unsupported IMTs if their weight is zero. This makes it possible to run
the JPN model with a single calculation, whereas previously we had to
perform two separate calculations, one for PGA and one for SA(0.2).

We added epistemic uncertainty options for aspect ratios:
`setAspectRatioAbsolute` and `setAspectRatioRelative` (see
https://github.com/gem/oq-engine/pull/11410).

We added epistemic uncertainty settings for relative seismogenic depth:
`adjust_lower_seismogenic_depth` and `adjust_upper_seismogenic_depth`
(see https://github.com/gem/oq-engine/pull/11415).

## hazardlib: new features and fixes

Savash Ceylan contributed a set of GMPEs: EdwardsFah2013Foreland3Bars,
BindiEtAl2011Rhypo, ECOS2009VariableDepth, and ECOS2009FixedDepth (see
https://github.com/gem/oq-engine/pull/11543).

Thuany Costa de Lima contributed a fix to the coefficient table
for BaylessSomerville2024 (see https://github.com/gem/oq-engine/pull/11553).

We added the ability to specify a distribution of hypocenters in simple
fault sources (see https://github.com/gem/oq-engine/pull/11430).

We added the magnitude-scaling relationship `BCHydroNVAMSR`,
required for the BC Hydro Northern Volcanic Arc (NVA) source zone
(see https://github.com/gem/oq-engine/pull/11420).

We added additional magnitude-scaling relationships to WC1994
and Thingbaijam2017 (see https://github.com/gem/oq-engine/pull/11508
and https://github.com/gem/oq-engine/pull/11496).

We extended the `ModifiableGMPE` capabilities to apply a delta variance
adjustment to tau (τ) or phi (φ). The deltas can also be IMT-dependent
(see https://github.com/gem/oq-engine/pull/11297).

We implemented the Holmgren et al. (2024) GMM requested by Bruce Worden
(see https://github.com/gem/oq-engine/issues/9910).

We added an `AlternativeCharacteristicMFD` class (see
https://github.com/gem/oq-engine/pull/11360) and updated the source
reader to understand it at the XML level.

We fixed `SiMidorikawa1999` to correctly use `Rhypo` instead of
`Rrup` for the NE correction term (see https://github.com/gem/oq-engine/pull/11307).

We refactored the BCHydro GSIM to improve the handling of ESHM20 FABA models.

We added an H3 grid lookup capability to the HDF5-based GSIM adjustment
utility class (see https://github.com/gem/oq-engine/pull/11380).

We permitted sentinel values for the `z_sed` parameter used in the
CEUS Coastal Plains adjustment factor (see
https://github.com/gem/oq-engine/pull/11387).

We added the NIED 2025 NSHM sigma model to the Morikawa and Fujiwara
2013 GMM (see https://github.com/gem/oq-engine/pull/11418). We also
fixed some unit conversion bugs, along with a bug where the `xvf` cap of 75
km was being applied incorrectly (see
https://github.com/gem/oq-engine/pull/11361).

We added BC Hydro subclasses of the NGA-1 GMMs (see
https://github.com/gem/oq-engine/pull/11427).

We added the ability to specify magnitude-dependent aspect ratios
(see https://github.com/gem/oq-engine/pull/11423).

We added a ray-tracing utility to `GridAdjustedGMPE`
(see https://github.com/gem/oq-engine/pull/11436).

We extended the SourceWriter to work with nonparametric sources
using `NegativeBinomialTOM`.

# Risk

We added the capability to compute embodied carbon loss as a new risk metric
in risk calculations, by supporting the new loss type, `embodied_carbon`, 
with its own vulnerability functions.

Scenario calculations have been optimized by considering only the
sites/assets within the integration distance of the rupture and then
distributing by GMFs. Depending on the calculation, the new approach
can provide a substantial speedup, especially for conditioned scenarios (in a
`scenario_damage` calculation for the PAPERS project, the measured
speedup was 100×).

We added the parameters `truncation_level_between` and
`truncation_level_within` for use in scenario calculations. We also
added support for sampling the GMFs from the truncated multivariate normal
distribution.

We improved the error triggered when all assets are filtered out to something
like `FilteredAway: No assets within <RuptureFilter mag=4 dist=50>`.

In conditioned scenarios, sites farther away than the asset-site
association distance now raise an error, but not if they are station sites.
This makes it possible to run some OQImpact calculations that would otherwise fail.

We fixed a false duplicated-stations error by rounding longitudes
and latitudes to five digits, as usual.

We added an exposure aggregation exporter called using `export aggexp_by`.

We store a `filtered_ruptured` dataset in ebrisk calculations,
as well as a `relevant_events` dataset.

We addressed an issue where the ShakeMap was being downloaded twice
unnecessarily.

We added support for risk calculations that depend on `AvgSA`
and also added `PGA` to the `AvgSA` computation (see
https://github.com/gem/oq-engine/pull/11263).

We implemented secondary perils for calculations starting from 
ShakeMaps by reading `PGV` information.

We added a CSV exporter for exposure grouped by region and
liquefaction/landslide LSE.

Finally, it is now possible to run the 2026 Global Seismic Hazard
and Risk Models without running out of memory, even on a
relatively small machine (16 cores with 96 GB of RAM), whereas previously
more than twice the resources were required. The runtime with only
16 cores will be measured in days for the GRM and weeks for the GHM, so
we still recommend using an enterprise-class server.

## Bug fixes

Amir Shahmohammadian contributed a fix for a bug in the treatment of
the PGV period in the Jayaram and Baker (2009) spatial correlation model,
which resulted in an incorrect coefficient of b = 22.0 instead of b = 25.7.

We fixed a bug in `check_aki_richards_convention` where the bottom-left
depth was used twice instead of using the bottom-left and upper-left depths.

We fixed the `avg_gmf` CSV exporter so that it only considers the
filtered site collection (i.e. the non-discarded sites) associated to
nonzero ground motion values. Moreover, we are not exporting the
standard deviations (but they are still available in the datastore).

We fixed the `aggexp_tags` and `aggrisk_tags` exporters. In some
cases they exported inconsistent results (i.e. tags present
in `aggexp_tags` but missing in `aggrisk_tags`, or vice versa).

We fixed several bugs in the procedure that exports the `job.zip`
file, particularly for ShakeMap calculations.

Storing a logic tree with more than `sys.maxsize` (~9E18) potential paths
previously failed. We now store the number of paths as a string attribute in
the HDF5 file, since it is used solely for debugging.

We now raise an early error when unsupported IMTs are used in
ConditionalGMPEs.

We avoided wasting time computing realization quantiles in
`scenario_damage`.

The land-cover coefficient in the Nowicki Jessee model was being
incorrectly assigned its default value because it was not
converted to an integer (i.e. 60.0 was considered different from
60), resulting in a missing key and the default value being returned.

## Other

We added a `keep_trt` parameter to discard all sources except those
with the specified tectonic region type. This is useful for debugging.

We added the ability to define a reference `z1pt4` parameter in the job
configuration file for use with the latest Japan model.

As usual, there was work on the WebUI for the AELO and OQImpact
projects, including restricting the visibility of the datastore and
`job.zip` download buttons to advanced users and improving several
plots.

We refactored the testing approach so that the AELO and IMPACT
tests can now be run together in a single action.

We added `run_scenario_from_ses_rupture`, a feature used only in
the context of the PAPERS project.

# IT

We upgraded the geospatial libraries, in particular GDAL to version
3.13.1.

In `devel_server` installations, `oq --version` now returns the Git hash
if the repository is accessible to the openquake user (i.e. if
`git config --add safe.directory` has been set). Otherwise, only the
major version is returned. The same version is also stored as a
global attribute of the datastore file `calc_XXX.hdf5`.

We made the engine more robust against out-of-memory errors. If the OOM killer
terminates a worker, the master is notified and the entire calculation is terminated,
instead of waiting for output that will never arrive.
