Release notes v3.24
===================

Version 3.24 is the culmination of 9 months of work involving over 500
pull requests. It is aimed at users wanting the latest features, bug
fixes and maximum performance. Users valuing stability may want to
stay with the LTS release instead (currently at version 3.23.3).

The complete set of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.24/debian/changelog

The major changes are in multifault sources (relevant for the USA,
China, Japan and New Zealand models), in secondary perils (i.e. liquefaction
and landslides) and in the script generating the global stochastic
event set from the GEM hazard models. Finally, we optimized the
memory consumption in scenario calculations, both conditioned and not.

A detailed summary is given below.

Hazard sources
---------------

We enhanced multifault sources. It is now possible to specify
their composition in faults with a syntax like the following:

  <multiFaultSource id="MF0" name="fault_0">
    <faults>
      <fault tag="tag1" indexes="1280,1281,1282,1283,1264,1265,1266"/>
      <fault tag="tag2" indexes="1024,1025,1026,1027,1028,1029,1030"/>
    </faults>
  </multiFaultSource>

This is used when disaggregating the hazard by source.  The mechanism
works by splitting the multifault source in faults before starting the
calculation. Then in the `source_info` dataset you will see not the
original multifault source ("MF0" in this example), but the two
multifault sources "MF0@tag1" and "MF0@tag2". You can find an example
in classical/case_75.

We reduced the memory consumption in multifault sources by splitting
them in blocks of ruptures, with size determined by the openquake.cfg
parameter `config.memory.max_multi_fault_ruptures`.

We added checks for missing hdf5 files when reading nonparametric and
multifault ruptures, so that the user gets clear error messges.

We added a parsing check in pointlike sources, the depths in the
hypodepth distribution must be within the `upper_seismogenic_depth`
and the `lower_seismogenic_depth`.

We improved the error message for invalid polygons, so that the user
can see which area source causes the infamous error "polygon perimeter
intersects itself".

We extended the `source_id` feature. For instance setting
`source_id=NewMadrid` in the job.ini will keep all the sources
starting with the string "NewMadrid" instead of keeping only the
source with ID "NewMadrid".

Classical calculations
------------------------

Then there was a substantial amount of work to support the USA (2023)
model. While the model is not supported yet - it will require engine
v3.25 - all of the required GMMs have been added to hazardlib.

Moreover, there were multiple improvements in the management of
clusters of sources (like the NewMadrid cluster) that now are a lot
more efficient, both computationally, in terms of memory consumption
and in terms of data transfer. Even estimating their weight in the
preclassical phase is much faster. Most of all, the disk space
consumption has been reduced by one order of magnitude.

We also fixed the "OverflowError: Python integer out of bounds for uint32"
happening when saving the `source_info` table due to the size of the model. 

Far away point sources (as determined by the preclassical phase) and
not transferred anymore, thus improving performance and
reducing data transfer and slow tasks. We also slightly optimized
the preclassical phase in the case of point sources when using
the ps_grid_spacing approximation.

Now we save the source model read times in the datastore, so that it
is possible to determine if a source model is particularly slow to
parse.

We changed slightly the ps_grid_spacing approximation so that the numbers
are slightly different. This will help towards implementing additional
optimizations in future engine releases.

We removed the parameter `reference_backarc` since it was not used.

Event based calculations
------------------------

We added a parameter `max_sites_correl` with default 1000 to stop
users trying to compute correlated GMFs with too many sites, resulting
in serious out of memory situations.  The parameter does not affect
scenario calculations.

We made the job.ini parameters `minimum_intensity` and
`minimum_magnitude` mandatory in the case of event based calculations
with more than `max_sites_disagg=10` sites. This solves the issue of
users forgetting to set such parameters and running calculations
much larger than needed.

We introduced a parameter `config.memory.gmf_data_rows` to make it impossible
to compute hazard curves from excessively large datasets (this happens
when the user forgets to remove `hazard_curves_from_gmfs` which is
meant to be used only for few sites).

We exposed the output `avg_gmf` that before was internal. Moreover, we
extended it to consider secondary IMTs.  `avg_gmf` is computed and
stored only in small calculations.  The controllining parameter in the
`job.ini` file is called `gmf_max_gb`, with a default value of 0.1,
meaning that `avg_gmf` is computed and stored only if `gmf_data`
contains less than 102.4 MB of data. You can raise the parameter but
then the calculation will become slower.

We improved the script `global_ses.py`, which is able to generate a
global (or partial) Stochastic Event Set starting from the hazard
models in the GEM mosaic. In particular it is possible to pass the
models to consider and the effective time parameters.  Moreover, we
documented it. It is not considered experimental anymore.

We also worked at avoiding out of memory errors in calculations
starting from the global SES; the performance, however, is still bad
and further work will be required. Moreover, you cannot run risk
calculations directly from the global SES yet.

Scenario calculations
----------------------

We reduced the memory consumption in scenario calculations by
discarding the sites outside the integration distance from the
rupture.

We futher reduced the memory consumption in conditioned GMFs calculations
by using shared memory to store the distance matrices.

We fixed the issue of small negative damages due to rounding errors
in some scenario damage calculations.

hazardlib
----------

We slightly optimized the generation of context arrays for point sources.

We worked at the Australian GMMs (NGAEastAUS2023GMPE), by introducing a way
to manage variable vs30 values, which is essential for risk calculations.

We adjusted the basin terms in many GMMs for the USA model to
determine the basin parameters from the vs30 via empirical
relationships. Such feature is enabled only if the
`z1pt0` and `z2pt5` parameters in the site model are set to the
sentinel value -999.

We added a BSSA14SiteTerm GMPE for use in the USA model.

Our users at USGS reported a bug with aliases, such that
`valid.gsim("[AbrahamsonGulerce2020SInterAlaska]")` was
returning the generic GMPE and not the regional specialization
for Alaska. This is fixed now.

We fixed `modified_gsim` to work with the NGAEast GMPEs.

We fixed the site term for Abrahamson and Gulerce (2020) to be exactly
consistent with the paper.

We fixed the BA08 site term: the rjb distance was not computed
when needed by the underlying GMPE, thus resulting into an error.

We fixed the issue of NaNs coming from `get_middle_point()` for kite surfaces
by discarding NaNs before computing the middle point.

We extended `ComplexFaultSource.iter_ruptures` to create ruptures
for a range of aspect ratios.

We added a classmethod `from_moment` to the TaperedGRMFD Magnitude Frequency
Distribution.

In the HMTK we extended the `get_completeness_counts` function
to optionally return an empty array (the default is to raise an error).
Moreover we extended the `serialise_to_nrml` method to accept a
mesh spacing parameters, as requested by Francis Jenner Bernales.

We implemented the Taherian et al. (2024) GMM for Western Iberia, both
for inland and offshore scenarios. This is the first GMM in the engine
using Machine Learning techniques, i.e. the onnxruntime library. Such
library at the moment is optional, i.e. if missing you can run everything
else except this GMM.

Graeme Weatherill contributed an implementation of
the MacedoEtAl2019SInter/SSlab conditional GMPE.

Baran Güryuva contributed the EMME24 backbone GMMs for crustal
earthquakes.

Guillermo Aldama-Bustos contributed the Douglas et Al. (2024) GMM.

Valeria Cascone added `get_width` and `get_length methods` to
the Strasser et al. (2010) MSR and then to the
Thingbaijam et al.(2017) MSR.

Chiara Mascandola added a class LanzanoEtAl2019_RJB_OMO_NESS2 to
Lanzano (2019) set of GMPEs and submitted an implementation of
Ambraseys (1996) and Sapetta-Pugliese (1996). She also submitted
Ramadan (2023) GMPEs.

We changed `contexts.get_cmakers` to return a `ContextMakerSequence`
instance, so that it is possible to compute the RateMap generated
by a CompositeSourceModel with a single call. Then we removed
the function `hazard_curve.calc_hazard_curve` since it is now
redundant.

logic trees
------------

We extended the check on number_of_logic_tree_samples to all
calculators and not only to event_based.

We added a new uncertainty `abMaxMagAbsolute` to change three
parameters of the Gutenberg Richter MFD
at the same time (`aValue`, `bValue` and `MaxMax`).

We added a new uncertainty `areaSourceGeometryAbsolute` and then
two seismogenic depth uncertainties (upper and lower) to
pointlike sources.

We extended the check on duplicated branches to the source model
logic tree.

We improved the library to generate logic tree files (`hazardlib.lt.build`).

If the source model logic tree is trivial (i.e. with a single branch)
it is possible to not specify it and just set the
`source_model_file` parameter.

We changed the realization string representation regular, i.e.
the first branch of the source model logic tree regular uses
a single letter abbreviation, all the other branches.

We fixed a couple of bugs in `oq show rlz`: it was not working
for a couple of tests (case_12 and case_68).

Finally, we included in the engine repository a private `_unc` package
containing a prototype implementation of the POINT (Propagation Of
epIstemic uNcerTainty) methodology for managing correlated
uncertainties. This is not ready for general usage yet.

Risk inputs
-------------

We added two new loss types `injured` and `affectedpop`
with their associated vulnerability functions. They are being used
by the OQImpact platform.

We extended the exposure reader to accept .csv.gz files, thus saving
disk space now that the exposure files are getting large.

We made the USA exposure parsing 10x faster by fixing
`get_taxidx` that was performing redundant operations.

Missing columns in the exposure.csv files (with respect to the fields
declared in exposure.xml) are now automatically filled with 'No_tag'.

We added an experimental option to aggregate the exposure: multiple
assets on the same hazard site and with the same taxonomy are
considered as a single aggregated assets. The feature is experimental
and meant to be used in the global risk model as a performance hack.

We saved a bit of memory when reading the asset collection in
the workers in event based risk calculations, by reading the
assets by taxonomy and by setting `max_assets_chunk`. We
also managed to increase the reading speed substantially (6x in an
example for Pakistan).

Infrastructure risk calculations for large networks could easily run
out of memory since the efficiency loss (EFL) calculation is quadratic
in the number of nodes. Now we just raise an error if the number
of nodes exceeds `max_nodes_network`, for the moment hard coded to 1000.

Calculations starting from ShakeMaps required a pre_job.ini file
and then the usual job.ini file. Now everything can be done with
a single file, thus making the user experience simpler and less
error prone. The two-files approach is still supported (it is
useful for instance in sensitivity analysis, when you want to
perform multiple calculations without downloading multiple times
the same ShakeMap) but it is not mandatory anymore.

We removed the obsolete parameter `site_effects` in the job.ini of scenario
from ShakeMaps calculations. It was meant to manage amplification
effects, but such effects are already included in modern ShakeMaps.

Risk outputs
------------

We fixed a bug in `post_risk` when computing the quantiles stored in
`aggrisk_quantiles`.

We reduced substantially the data transfer in `avg_losses` (4x
for the Philippines) by performing a partial aggregation in the
workers.

We changed the risk exporters to export longitude and latitude of the assets
at 5 digits, consistently with the site collection exporter.

We added a method to aggregate the asset collection over a list of
geometries, for internal usage.

We added an extractor for `damages-stats`, similar to the extractor for
`damages-rlzs`, since it was not implemented yet.

There is now an exposure extractor which however is not accessible
from the WebUI for security issues (the exposure can contain
sensitive data).

There is also an exporter for the vulnerability functions and one for
the job.zip file: the latter, however, is still experimental and known
not to work in some cases.

We added an extractor for `losses_by_location`, which is
aggregating the assets of the assets on the same location (NB:
the asset locations are not necessarily the same as the hazard sites,
which are usually on a coarser grid).

We are now gzipping the avg_losses datasets, thus reducing the disk
space occupation by 2-3 times. This is important in large
scenario calculations.

The extractor for aggregated risk and exposure was not supporting
multiple tags, i.e. the semicolon syntax as in
`aggregate_by = NAME_1, OCCUPANCY; NAME_1; OCCUPANCY`. This is now
fixed. Moreover, the exporter `aggexp_tags` exports a file for
each tag combination.

Secondary perils
----------------

The secondary peril implementation is still experimental and this
releases contains a great deal of changes (see
https://github.com/gem/oq-engine/pull/10254) plus a new feature: it is
now possible to generate the equivalent of hazard curves and maps for
secondary IMTs.

Many new models wered added, many were fixed, some model names very
changed. Calculations using the old names will fail with a clear error
message suggesting to the user the new names.

In the case of landslides we renamed the `job.ini` parameter
`crit_accel_threshold` as `accel_ratio_threshold`. Moreover,
we discarded displacement values below 1E-4 to avoid wasting
disk space.

We fixed the unit of measure for the slope parameter (m/m)
when computing the landaslide peril.

There were two important fixes to the TodorovicSilva2022NonParametric
model: first, we solved the `NameError: Missing liquefaction:LiqProb
in gmf_data` that happened in some cases.  Second, we solved a much
trickier issue, overparallelization due to the underlying machine
learning library that could totally hang large calculations.

We changed the `multi_risk` calculator to be more similar to
a scenario_risk calculator with secondary perils; in particular
the special-case syntax

multi_peril_csv = {'ASH': "ash_fall.csv", 'LAHAR': "lahar-geom.csv",
                   'LAVA': "lava-geom.csv", 'PYRO': "pyro-geom.csv"}

has been replaced with

secondary_perils = Volcanic
sec_peril_params = [{"ASH": "ash_fall.csv", "LAHAR": "lahar-geom.csv",
                     "LAVA": "lava-geom.csv", "PYRO": "pyro-geom.csv"}]

The plan for the future is to replace the `multi_risk` calculator with
a regular `scenario_risk`.

We changed the storage of secondary IMTs inside `gmf_data`
to keep the secondary peril class as prefix as prefix in the column name:
this makes it possible to manage multiple perils within a single computation.

Each secondary peril subclass has now a `peril` attribute
pointing to `landslide` or `liquefaction`.

If the risk functions contain IMTs which are not in the
secondary IMTs set a warning is printed, since it means that
such risk functions will be ignored. This is a protection against
typos.

If there are secondary IMTs not covered by the risk function an
error is raised, since it is impossible to compute the secondary peril.

Finally, we added a demo called InfrastructureMultiPeril to showcase
a Multi-Peril risk calculator using a small infrastructure
network with four nodes and four edges.

Bug fixes
---------

In the past users could mistakingly set `max_sites_disagg` to be
(much) larger than the total number of sites, thus resulting in too
many postclassical tasks to be generated, with a terrible
performance. Now the engine takes the total number of sites in
consideration when determining the number of postclassical tasks to
generate.

Extracting the realization specific disaggregation outputs in
traditional format, with a call like
`get("disagg?kind=TRT_Mag_Dist_Eps&imt=SA(0.075)&spec=rlzs-traditional&poe_id=0&site_id=0")`
failed with a numpy error. This is now fixed.

We fixed `getters.get_ebruptures` to work also for scenario calculations.

Some corporate users have no permission to write on their Windows
temporary directory and they could not run the demos. We worked
around this issue by removing the check on the `export_dir`.
You can still export by using the `oq engine --export-outputs`
command and by passing to it the path to a writeable directory.

`hcurves-rlzs` and `hmaps-rlzs` were created in single site calculations
even if `individual-rlzs` was not set. This is now fixed.

oq commands
-----------

The commmand `oq plot rupture` to plot the geometry of a rupture
has been slightly improved and we added a command `oq plot build_rupture`
to plot planar ruptures (see `oq plot examples` for examples of usage).

We added a command `oq plot_h3` accepting a list of h3 codes and
visualizing the hexagons with country borders.

We extended `oq plot_assets` to also plot the stations if available.

We added a command `oq info apply_uncertainty` to display the recognized
uncertainties in the logic tree.

We removed the `--config-file` option from the `oq engine` command
since there is the OQ_CONFIG_FILE environment variable for the
rare cases when it is needed.

We removed the `--reuse-input` flag since it can be replaced with a
cache enabled via the `config.dbserver.cache` flag. The cache
mechanism is still experimental and disabled by default.

We added an utility `utils/find_exposure <dirname>` to find the
largest exposure in a directory.

For single site calculations with disagg_by_src it is possible
to visualize the most relevant sources with the command
`oq show relevant_sources:<IMT>`.

We extended `oq engine --delete-calculation` to remove both
`calc_XXX.hdf5` and `calc_XXX_tmp.hdf5` when deleting a job.

We extended `oq importcalc calc_hdf5` to also import calculation files
outside oqdata by moving them inside oqdata.

WebUI
-----

We added an endpoint `/v1/calc/:calc_id/exposure_by_mmi` to extract
the `exposure_by_mmi` output (in JSON format) for risk calculations
from ShakeMaps.

We added an endpoint `/v1/calc/:calc_id/impact` to extract the
impact results (in JSON format) for scenario risk calculations.

We added an endpoint `/v1/calc/jobs_from_inis` to determine which job.ini
files have been already run (in that case we return the associated job_id)
or not (in that case we return 0). This was required by the PAPERS project.

We added a private endpoint `/v1/calc/run_ini` to run calculations starting
from a remote .ini file, assuming the client knows its full path name.

We made the hidden outputs (i.e. exposure and job_zip) visible and
downloadable only for users of level 2 or when the WebUI
authentication is disabled.

We made it possible to select multiple input files (and not only a
single zip file) when running a job via the WebUI.

Now we do not show in the WebUI the jobs that have the `relevant` flat
set to false. This is a way to hide jobs without removing them.

IT
---

In this release we removed the `pyshp` dependency (since we have
`fiona`) and we added the Uber's package `h3` (version 3.7.7).
This is the last release supporting Python 3.10 and numpy
1.26: in the next release we will upgrade all numpy-dependent
libraries (including the geospatial libraries) and we will require at
least Python 3.11.

We changed the parallelization parameters to try to
ensure at least one GB of RAM per thread, possibly at
the cost of using less threads than available. For instance,
if your machine has 22 threads and 16 GB of RAM only 16 threads will
be used by default.

It is still possible, as always, to
specify the `num_cores` parameter in the `openquake.cfg` file
to explicitly control the number of processes in the process pool.
Users on a laptop with not much memory are recommended to
close the browser and run their calculations from the command line.

AELO and OQImpact
-----------------

Hundreds of pull requests were made in the engine codebase to support
the AELO and OQImpact platforms. However, since those are private
platforms, the related improvements will not be listed here.
