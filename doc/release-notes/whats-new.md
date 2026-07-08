Release notes (dev)
===================

Version 3.26 is the culmination of 3 months of work involving over 320
pull requests. It is the minimum version able to run the 2026 release of Global
Hazard and Risk Models. Users not needing the latest models may want to
stay with the LTS release, currently at version 3.23.4.

The complete set of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.26/debian/changelog

A summary is given below.

# Hazard

## Rupture sampling

The performance of the command generating the global Stochastic Event
Set has been drastically improved by reducing slow tasks and by saving
memory. Without such improvements the global SES with the latest
models could not be computed due to out-of-memory errors. The change
required splitting the multifault and multipoint sources in a
different way and thus changing the rupture seed generation algorithm.

We fixed a rupture sampling bug in the case of mutually exclusive ruptures,
affecting Japan in the Nankai area and the USA model in the New Madrid area.

Moreover, it is now possible to pass a `--cache=true` parameter to the
`global_ses` script to avoid recomputing models.

We now save `year` and `ses_id` in the events dataset, which are
needed for the Global Risk Model.

We introduced a dictionary `TRT -> maximum_rupture_depth` to discard
very deep ruptures.

We have a clear error message in the case of duplicated rupture IDs,
which can only happen if there is a bug in the sampling implementation.

We now manage the `CompositeSourceModel` in the same way both in
classical and in event-based calculations, and in particular we
optimized identical sources: that reduced the memory consumption for
models like New Zealand by an order of magnitude, also doubling the
speed.

We also optimized reading and sampling multifault sources by
parallelizing `build_secparams` and by splitting the sources
before `preclassical` or `sample_ruptures`.

Finally, we optimized the method `src.count_ruptures()` for multifault
sources.

## Classical PSHA

There was a dramatic memory bug (producing a list of
contexts instead of an iterator) causing some models to use several GB
of RAM per core (up to 10). Now all the models can be run with less
than 2 GB per core.

We fixed a SourceFiltering bug in the case of few sites, causing
terrible slow tasks. The improvement in speed can be dramatic (i.e.
we have measured a 6x speedup in a calculation for MIE).

We fixed a prefiltering bug affecting point sources spanning over 180 degrees
of latitude at the poles (i.e. oceanic sources were incorrectly
discarded).

The mosaic geometries have been fixed; now they are read and validated
by using geopandas. The `mosaic.gpkg` file is also considered in the internal
checksum logic (i.e. if you change `mosaic.gpkg` the cache is
invalidated).

We extended the usability of use_rates = true to IMT-dependent weights,
i.e. the Canada model can now be computed with full enumeration
even if there are more than 7 million realizations.

We added a warning in the preclassical phase suggesting the usage of
`use_rates = true` if only mean curves are required.

In the case of IMT-dependent logic trees it is now possible to list
unsupported IMTs if their weight is zero. That made it possible to run
the JPN model with a single calculation, while before we had to
perform two different calculations, one for PGA and one for SA(0.2).

We added an epistemic uncertainty option for aspect ratios,
'setAspectRatioAbsolute' and 'setAspectRatioRelative' (see
https://github.com/gem/oq-engine/pull/11410).

We added an epistemic uncertainty setting for relative seismogenic depth,
'adjust_lower_seismogenic_depth' and 'adjust_upper_seismogenic_depth'
(see https://github.com/gem/oq-engine/pull/11415).

## job.ini extensions

We added a `keep_trt` parameter to discard all sources except the
ones with the specified tectonic region type. This is useful while debugging.

We added the parameters `truncation_level_between` and
`truncation_level_within` for use in scenario calculations.

We added the ability to define a reference `z1pt4` parameter in the job
configuration file, to be used with the latest Japan model.

## hazardlib: new features and fixes

Savash Ceylan contributed a set of GMPEs: EdwardsFah2013Foreland3Bars,
BindiEtAl2011Rhypo, ECOS2009VariableDepth, ECOS2009FixedDepth (see
https://github.com/gem/oq-engine/pull/11543).

Thuany Costa de Lima contributed a fix to the coefficient table
of BaylessSomerville2024 (see https://github.com/gem/oq-engine/pull/11553).

We added the ability to specify a distribution of hypocenters in simple
fault sources (see https://github.com/gem/oq-engine/pull/11430).

We added the Magnitude-Scaling Relationship `BCHydroNVAMSR`,
required for the BC Hydro Northern Volcanic Arc (NVA) source zone
(see https://github.com/gem/oq-engine/pull/11420).

We added additional magnitude-scaling relationships to WC1994
and to Thingbaijam2017 (see https://github.com/gem/oq-engine/pull/11508
and https://github.com/gem/oq-engine/pull/11496).

We extended the `ModifiableGMPE` capabilities to apply a delta variance
tweak to tau (τ) or phi (φ). The deltas can also be IMT-dependent
(see https://github.com/gem/oq-engine/pull/11297).

We implemented the Holmgren et al. (2024) GMM requested by Bruce Worden
(see https://github.com/gem/oq-engine/issues/9910).

We added an `AlternativeCharacteristicMFD` class (see
https://github.com/gem/oq-engine/pull/11360)
and made it usable in area sources. 

We fixed the `SiMidorikawa1999` to correctly use `Rhypo` instead of
`Rrup` for the NE correction term (see https://github.com/gem/oq-engine/pull/11307).

We refactored the BCHydro GSIM to improve handling of ESHM20 FABA models.

We added an h3 grid-lookup capability from the HDF5-based GSIM adjustment
utility class (see https://github.com/gem/oq-engine/pull/11380).

We permitted sentinel values for the `z_sed` parameter used in the
CEUS coastal plains adjustment factor (see
https://github.com/gem/oq-engine/pull/11387).

We added the NIED 2025 NSHM sigma model to the Morikawa and Fujiwara
2013 GMM (see https://github.com/gem/oq-engine/pull/11418). We also
fixed some unit conversion bugs plus a bug where the `xvf` cap of 75
km was being applied incorrectly (see
https://github.com/gem/oq-engine/pull/11361).

We added BC Hydro subclasses of the NGA-1 GMMs (see
https://github.com/gem/oq-engine/pull/11427).
 
We added the ability to specify magnitude-dependent aspect ratios.
(see https://github.com/gem/oq-engine/pull/11423).

We added a raytracing utility to `GridAdjustedGMPE`.
(see https://github.com/gem/oq-engine/pull/11436).

We extended the SourceWriter to work with nonparametric sources
with `NegativeBinomialTOM`.

# Risk

We added the capability to compute the carbon footprint in the Global Risk
Model thanks to a new loss type `embodied_carbon` with its own vulnerability
functions.

Scenario calculations have been optimized by considering only the
sites/assets within the integration distance from the rupture and then
distributing by GMFs. Depending on the calculation the new approach
can give a large speedup, especially for conditioned scenarios (in a
scenario_damage calculation for the PAPERS project the measured
speedup was 100x).

We added support for sampling the GMFs from the truncated multivariate normal
distribution.

We improved the error triggered when all assets are filtered out to something
like `FilteredAway: No assets within <RuptureFilter mag=4 dist=50>`.

In conditioned scenarios sites more distant than the asset-site
association distance raise an error, but not if they are station sites.
That makes it possible to run some OQImpact calculation that would fail
otherwise.

We fixed a fake duplicated stations error by rounding longitudes
and latitudes to 5 digits as usual.

We added an exposure aggregation feature called `export aggexp_by`.

We store a `filtered_ruptured` dataset in ebrisk calculations,
as well as a `relevant_events` dataset.

We addressed an issue where the ShakeMap was being downloaded twice
unnecessarily.

We added support to run risk calculations that depend on `AvgSA`
and then added `PGA` to the `AvgSA` computation (see
https://github.com/gem/oq-engine/pull/11263).

We implemented secondary perils for ShakeMaps by reading the
`PGV` information.

We added a CSV exporter for the exposure grouped by region and
liquefaction/landslide LSE.

Finally, let us note that is now possible to run the 2026 Global Hazard
and Risk Models without running out of memory even on a
relatively small machine (16 cores with 96 GB of RAM) while before
more than double the resources were required. The runtime with only
16 cores will be of days for the GRM and of weeks for the GHM, so
we still advise to use an enterprise-class server.

## Bug fixes

Amir Shahmohammadian contributed a fix to a bug in the treatment of
PGV period in the Jayaram and Baker (2009) spatial correlation model
resulting in a wrong coefficient b = 22.0 instead of b = 25.7.

We fixed a bug in `check_aki_richards_convention` where the bottom-left
depth was used twice instead of bottom-left and upper-left.

We fixed the `avg_gmf` CSV exporter to only consider the filtered
site collection (i.e. the non-discarded sites).

We fixed the exporters `aggexp_tags` and `aggrisk_tags`: in some
cases they were exporting inconsistent results (i.e. tags present
in `aggexp_tags` and missing in `aggrisk_tags` or vice versa).

We fixed several bugs in the procedure exporting the `job.zip`
file, particularly in the case of ShakeMap calculations.

Storing a logic tree with more than `sys.maxsize` (~9E18) potential paths
failed; now we just store the number of paths as a string attribute in the
HDF5, since it is used solely for debugging.

We now raise an early error when using unsupported IMTs in
ConditionalGMPEs.

We avoided wasting time in scenario_damage computing the realization
quantiles.

The landcover coefficient in the Nowicki Jessee model was being
incorrectly assigned to the default value, because it was not
converted into an integer (i.e. 60.0 was considered different from
60), thus resulting in a missing key returning the default value.

## Other

As usual there was work on the WebUI for the AELO and OQImpact
projects, like for instance restricting the visibility of the
datastore and `job.zip` download buttons only to advanced users
or improving a few plots.

We refactored the testing approach so that now the AELO and IMPACT
tests can be run together in a single action.

We added a `run_scenario_from_ses_rupture` functionality used only in
the context of the PAPERS project.

# IT

We upgraded the geospatial libraries, in particular GDAL to version
3.13.1.

In `devel_server` installations `oq --version` now returns the git hash
if the repository is accessible to the openquake user, i.e. if
`git config --add safe.directory` has been set. Otherwise only the
major version is returned. The same version is stored as a
global attribute of the datastore file `calc_XXX.hdf5`.

We made the engine more robust against out-of-memory errors: if the OOMKiller
kills a worker, the master is notified and then the full calculation is killed,
instead of waiting for an output that will never arrive.
