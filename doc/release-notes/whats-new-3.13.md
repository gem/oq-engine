Release notes v3.13
===================

The release 3.13 is the result of 4 months of work involving over
350 pull requests and touching all aspects of the engine. In particular,
this is the minimal release needed to run the new [2020 Euro-Mediterranean 
Seismic Hazard Model (ESHM20)](http://hazard.efehr.org/en/Documentation/specific-hazard-models/europe/eshm2020-overview/) 
and the new [GEM China model](https://www.globalquakemodel.org/GEMNews/china-earthquake-loss-model-2021).

The complete list of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.13/debian/changelog

## New features

We have a brand new conditional spectrum calculator documented here:

https://docs.openquake.org/oq-engine/advanced/conditional-spectrum.html

For the moment, it should still be considered experimental; we welcome
help from people wanting to test it. This is a functionality implemented as part of the activities GEM is performing within the METIS project (https://metis-h2020.eu).

The event_based_damage calculator introduced in version 3.12 has been
revised, unified with the scenario_damage calculator and documented here:

https://docs.openquake.org/oq-engine/advanced/event-based-damage.html

In particular it is possible to work with discrete damage distributions
by setting the parameter `discrete_damage_distribution=true` (the
default is false, which is much more performant). Moreover, a few bugs
were fixed.

We now support four different strategies for computing risk profiles,
documented here:

https://github.com/gem/oq-engine/blob/engine-3.13/doc/adv-manual/risk-profiles.rst

Global site model parameters (i.e. the site model parameters defined
in the job.ini file) are now used if a column is missing in the site
model file, instead of raising an error. Only the site model
parameters required by the GMPEs are imported in the datastore,
additional columns in the site model file are ignored (previously, they
were imported even unnecessarily).

Finally, the engine now supports cross correlation (i.e. inter-period correlation) when
generating the ground motion fields. Two cross correlation models are
supported at the moment (FullCrossCorrelation and GodaAtkinson2009),
more will likely be added in the future. The feature is documented here:

https://docs.openquake.org/oq-engine/advanced/correlation.html

## Improvements to the classical calculator

In order to support the ESHM20 model, which is too large to run on
most hardware, we had to implement a tiling functionality, so that
a classical calculation can be split into chunks of sites (tiles) that
are then run sequentially. This is slower than the usual strategy of
running everything in a single tile and should be used only as last
resort, in out-of-memory situations. Also, you should use a small
number of tiles to reduce the performance penalty. For instance,
for a calculation with 100,000 sites, setting `max_sites_per_tile=50000`
in the job.ini file will produce two tiles and reduce by half the memory
consumption.

In order to avoid slow tasks in tiling calculations that would completely
kill the performance, enormous efforts was dedicated to improving the task
distribution which is now sensibly better than before, in particular
in the presence of CollapsedPointSources and MultiFaultSources. Slow tasks
are still possible in corner case situations but they can be mitigated
by tweaking the parameters `time_per_task` and `outs_per_task`.

The internals of the datastore have changed significantly, in particular
for the `source_info` dataset; there is now an additional `source_data`
dataset. They are used internally to understand the content of the tasks
in terms of sources and the calculation time per source.

The memory occupation has been significantly reduced, even without tiling, 
and calculations that were previously running out of of memory are now
progressing smoothly. The reduction depends on the model: for instance the
OpenQuake implementation of the USGS model for the United States now
requires half the memory than before, while the NRCan model for Canada
requires the same memory as before. Some small models could possibly require
more memory than before. The memory reduction is particularly sensible in
models with few sites and in disaggregation calculations.

The disk space occupation has been significantly reduced by changing
the ways the PoEs are stored (not storing the zero values).  This was
necessary for the ESHM20 model where the required disk space was
reduced from 256 GB to 110 GB per calculation. Changing the storage
had also a positive effect on performance, since the calculation is
not stuck writing the data anymore. Moreover, thanks to the new
storage format, it is much simpler to perform manual post-processing of the
PoEs by using pandas.

We changed the approach used when computing the hazard curves and the
statistics: it is now several times faster and using a lot less memory.
The improvement has come both from the change in storage (there is less data
to read) and the usage of numba in `get_slices`. The effect is dramatic
in the ESHM20 model, much less so in smaller models.

The documentation of the point source gridding approximation has been
improved, with a section about how to make the Canada model 26x faster:

https://docs.openquake.org/oq-engine/advanced/point-source-gridding.html

We improved the precision of the `pointsource_distance` approximation:
that means the now you can use smaller values for the `pointsource_distance`
parameter and have better performance without loosing precision.

Finally, the preclassical phase of the classical calculator has been
moved to its own independent calculator. That means than one can
run a preclassical analysis only once and then run different classical
calculations starting from the same sources by using the `--hc`
option. This is also useful when debugging, in case the preclassical
phase is expensive, i.e. for large models.

## Changes to the disaggregation calculator

There was a big change in the CSV exporters, with the goal of reducing
the proliferation of outputs. For instance a calculation with N=2
sites, M=10 intensity measure types, P=5 poes_disagg and R=100
realizations and 7 kinds of disaggregation, previously would generate
N * M * P * R * 7 = 70,000 files. Now it only generates N * 7 = 14
files. The trick was to add a column for the IMT, a column for the PoE
and a column for the realization index. People parsing the CSV outputs will
have to update their scripts.

In the single site case, there is now a warning when a realization
does not contribute to the disaggregation. This helps identifying
pathological situations.

We fixed a bug in the `Mag_Lon_Lat` exporter: the order of
the columns was wrong and the fields mag, lon, lat were actually
containing the values of lon, lat, mag.

We added a command `oq info disagg` to print all 7 kinds of supported
disaggregation outputs.

We added a FAQ about how to compute mean disaggregation outputs, since
many uses asked, see 

https://github.com/gem/oq-engine/blob/engine-3.13/doc/faq-hazard.md#how-can-i-compute-mean-disaggregation-outputs

Finally we removed the long deprecated XML exporters.

## Improvements to the event based calculator

We significantly reduced the slow tasks affecting event based calculations,
both for hazard and risk.

We added a check for missing GSIMs in the job_risk.ini file, to
avoid confusing error messages in the middle of the computation.

We extended the mag-dependent filtering to event based calculations; before
it was honored only in classical calculations.

The `custom_site_id` is now exported also by the GMF exporters.

When using the `--hc` option the engine was using the site collection
of the parent calculation and ignoring the site collection of the
child calculation: this is now fixed.

There is a new parameter `gmf_max_gb`, with default value 0.1,
which is used to decide when to store the `avg_gmf` dataset.

We improved the documentation on the rupture sampling mechanism:

https://docs.openquake.org/oq-engine/advanced/rupture-sampling.html

## Logic trees

We improved the support for source specific logic trees (i.e. logic
trees with an `applyToSources` for each source) and documented it
here:

https://docs.openquake.org/oq-engine/advanced/sslt.html

The branch IDs in the gsim logic tree file are now ignored and
the user can skip them altogether. The change was implemented
to fix a subtle bug causing incorrect branch paths to be listed
in the output "Realizations" in case of duplicated branch IDs.

We changed the string representation of logic tree paths and 
added the commands `oq show branches` and `oq show rlz:<no>`
to allow the user to switch easily from the branch path to the
corresponding source model, source parameters and GMPE. They
are documented here:

https://docs.openquake.org/oq-engine/advanced/logic-trees.html

Due to the changes above, the numbering of the realizations can be
different between engine 3.13 and previous versions, and calculations
using sampling can produce slightly different averages since different
realizations may be chosen internally. This is akin to a change of
random seed, i.e. it is not a physically significant change.

There is now a limit on the number of branches per branchset in the
logic tree (94 branches).

We changed the experimental feature `collapse_gsim_logic_tree` to use 
the class `AvgPoeGMPE` instead of `AvgGMPE`: in this way it is possible to
compute exactly the average mean curves in the case of full enumeration,
even when the number of realizations is too large to use the traditional
approach.

We fixed the `extendModel` feature that was not working in presence
of multiple files per source model logic tree branch.

Running a calculation with full enumeration and more than 15,000
realizations now raises an error unless the user raises the
parameters `max_potential_paths` in the job.ini file. This is useful
to avoid out-of-memory issue at the end of the calculation, in
the postclassical phase.

## hazardlib

As usual, many new GMPEs were contributed:

- [Miguel Leonardo-Suárez](https://github.com/mleonardos)
  contributed the GMPEs Arroyo et al. (2010) and
  Jaimes et al. (2020).

- [Chiara Mascandala](https://github.com/mascandola)
  contributed a new GMPE LanzanoEtAl2019_RJB_OMO
  and fixed a bug in the SgobbaEtAl2020 GMPE. She also contributed
  new variations of Lanzano & Luzi (2019), Skarlatoudis et al. (2013),
  and BCHydro GMPEs.

- [Giuseppina Tusa](https://github.com/gtus23) contributed the Tusa-Langer-Azzaro (2019) GMPE.

- Thanks to EDF we added support for the EAS, FAS and DRVT intensity
  measure types, used in the new GMPEs Bora et al. (2019) and Bayless &
  Abrahamson (2018).

- We added the GMPEs of Bahrampouri et al. (2021) for the Arias intensity
  measure type.

- The `backarc` site parameter used to have only two possible values, 0
  for "fore arc" and 1 for "back arc"; now the value 2 for "along arc"
  is accepted too. The change was made to support the GMPE Manea (2021),
  contributed by [Elena Manea](https://github.com/ElenaManea) and 
  [Laurentiu Danciu](https://github.com/danciul).

A few bugs were also fixed:

- We fixed a bug in `recompute_mmax` (returning square meters instead
  of square kilometers) affecting logic trees changing the slipRate.

- We fixed a compatibility bug with the SMTK causing the error
  `'RuptureContext' object has no attribute 'occurrence_rate'`
  when running the SMTK tests.

- We fixed an array<->scalar bug in the GMPE Abrahamson-Gulerce (2020)

- Several essential bug fixes and improvements were made on the new
  MultiFaultSource and KiteSurface classes, needed for the GEM China model
  and others.

- [Riccardo Zaccarelli](https://github.com/rizac) found a typo in the 
  intensity measure type RSD that was fixed.

There were a few other changes and new features:

- We changed `hazardlib.valid.gsim` to return a correctly instantiated
  GSIM or to fail. Before - for GMPETable subclasses - it was
  returning a partially initialized GSIM to be post-initialized later
  on. Thanks to [Bruce Worden](https://github.com/cbworden) for
  pointing this out.

- We changed the API of `get_mean_stds`: there is no need to specify the
  standard deviation anymore, since it always returns all three standard
  deviations ($\sig, \tau, \phi$) on top of the mean ($\mu$). We improved its
  documentation in the advanced manual.

- We added a warning when the mesh size of MultiFaultSources and
  NonParametricSources is over one million points: the goal is to warn
  the user against building sources that are then too big to compute.

- We added a new method `add_between_within_stds` to the modifiable
  GMPE to compute spatially correlated ground-motion fields
  even when the initial GMPE only provides the total standard
  deviation. To be used with care.

- We added a check to the `geo.Line class` to ensure that every Line object
  must have at least two points.

- We improved the error message in ShakeMap calculations failing due to the
  correlation matrix being not positive defined; now we point out to
  the manual: https://docs.openquake.org/oq-engine/advanced/shakemaps.html#correlation

- [Yen-Shin Chen](https://github.com/vup1120) contributed a new scaling 
  relationship Thingbaijam et al. (2017) for strike-slip.

- [Manuela Villani](https://github.com/orgs/gem/people/ManuelaVillani)
  contributed a new method `horiz_comp_to_geom_mean`
  to the ModifiableGMPE class to convert ground-motion between
  different representations of the horizontal component.

Finally there was some refactoring and 15 classes in the module
`hazardlib.gsim.boore_2014` have been replaced with a single parametric GMPE,
so they cannot be called directly anymore, but rather via the
`valid.gsim` factory function, which is the recommended way for all GMPEs.

## Risk fixes and improvements

We renamed the field "conversion" into "risk_id" in the header of the
taxonomy mapping file. The old name is still valid.

We fixed a bug in presence of continuous fragility functions with
`minIML` equal to `noDamageLimit`, causing damages where there should
have been no damage.

We fixed a bug in event based risk calculations with non-trivial taxonomy
mapping producing NaNs in the event loss table.

We added a "reaggregate_by" feature in event based risk calculations,
documented here:

https://github.com/gem/oq-engine/blob/engine-3.13/doc/adv-manual/risk-profiles.rst

We improved the error checking when reading the taxonomy mapping file.

We added a check for invalid consequence files, to get an early error
and not an error in the middle of the risk calculation. Also,
specifying consequence files without fragility files now raises an early .
error.

We added a check for missing investigation_time in classical risk
calculations.

We fixed a serious performance bug when using `ignore_master_seed=true`
that caused a 60x slowdown in the event based risk calculation for China.

We implemented secondary perils in the risk side. This is still an
experimental feature.

When using the `--hc` option there is now a check making sure that the
intensity measure levels are consistent between child calculation
and parent calculation.

We fixed a bug when using `aggregate_by = site_id` in presence of
a parent calculation.

The aggregation of losses in event based risk calculations has been
optimized even more, and unified with the aggregation in event based
calculations.

The damage outputs have been unified with the risk outputs and now we
have only two possibilites, both for risk and damage calculations: an
`aggrisk` output and an `aggcurves` output. Both are pandas-friendly
to help post-processing of the results. As a consequence, also the
exported CSV files are more similar between risk and damage outputs.

Consequence models in XML format have been deprecated: you should use
solely the CSV format.

## Other fixed and changes

We renamed the parameter `individual_curves` into `individual_rlzs`
since it now applies not only to hazard curves but to all kinds of outputs.
The old name is still valid as an alias.

The --log-file option in the command `oq engine` was not honored.

We fixed running a calculation starting from a parent calculation owned
by a different user.

Mixed list-scalar maximum distances (for instance maximum_distance={
'TRT_A': 100, 'TRT_B': [4, 100], [8, 200]}) were previously invalid:
this has been fixed.

The `custom_site_id` site model parameter is now honored in all
calculators, not only in classical calculators. Moreover we
changed it from being a 32-bit integer to a 6-characters ASCII string
and we documented it:

https://docs.openquake.org/oq-engine/advanced/special-features.html

`DataStore.read_df` now returns strings and not bytes for fields stored
as bytes.

`readinput.get_composite_source_model(oqparam, branchID)`
now accepts a `branchID` parameter; this is useful for Hamlet.

`datastore.read` now accepts a flag `read_parent`; by default it is
True, but it can be set to False to avoid reading the parent of a calculation
(if any). This is useful in postprocessing scripts.

`get_oqparam` now does not instantiate a SourceModelLogicTree object
and thus avoids parsing the entire source model every time. For the
Australia model that reduces the instantiation time from 47 seconds to
0.7 seconds. That makes it possible to assess the size of a source model
very quickly.

## oq commands

The logic behind the command `oq check_input job_haz.ini job_risk.ini`
has changed: now the risk files are checked first, so errors are
discovered immediately and not after a slow check of the hazard files.

The command `oq prepare_site_model` has been extended to accept vs30 files
in .csv.gz or .hdf5 format. We also added an utility `vs30tohdf5` to
convert the global vs30 .geotiff map provided by the USGS
(downloadable from https://earthquake.usgs.gov/data/vs30/)
into a compressed HF5 file suitable for use with `oq prepare_site_model`.

The command `oq prepare_site_model` has also been extended to work for exposures
containing assets distant from all site parameters: in that case a warning
is printed. Previously, the site model could not have been generated.

We added a command `oq compare uhs` to compare uniform hazard spectra between
two or more calculations, similar to the old commands
`oq compare hcurves` and `oq compare hmaps`.

We fixed a small bug in `oq zip job_haz.ini -r job_risk.ini`: now it works
even for empty oqdata directories.

We fixed `oq plot uhs` in presence of non-SA intensity measure types.

We added a command `oq plot source_data`.

We added a command `oq info cfg` to show the location of the
engine configuration file.

We extended the command `oq plot avg_gmf` so it can plot the differences
between two average GMFs.

## IT and WebUI changes

We upgraded a few libraries: numpy to version 1.20, scipy to version
1.7, h5py to version 3.1 and GDAL to version 3.3.3. This allowed us
to support Python 3.9.  Python 3.7 and 3.8 are also supported, while
Python 3.6 is deprecated since it has reached its end of life and it
is not supported by python.org.  The engine will probably stop working
with Python 3.6 in the next release.  Python 3.10 is not officially
supported yet.

We removed the dependency from python-prctl which was not needed anymore.

We removed all upper bounds on the dependencies to make it possible
for people to install the engine with newer libraries. Thanks to that
the engine now unofficially works on macOS with an M1 processor by
using Python 3.9 and the latest libraries. However, that requires
manual tweaking and it is not officially supported by GEM. We cannot
support the M1 processor until GitHub provides support for automatic
testing on this platform.

Some infrastructure work for dynamically deploying the engine on a
cluster of kubernetes has been started, and the WebUI changed to
support such an environment. In particular now invalid input files
raise an error *before* spawning a new machine. Also, small calculations
are recognized and executed on the master machine, without spawning
anything.

The WebUI has been changed to store the input files in the
temporary directory determined by the `custom_tmp` parameter in the
file `openquake.cfg`. Moreover we added a parameter `mosaic_dir`
in `openquake.cfg` that allows the engine to read (big) files from
a predefined global directory, so that we can avoid uploading huge files
to the WebUI.

We also extended the WebUI to run sensitivity analysis calculations.

An annoying warning about not having the latest engine release has
been removed.

We extended the systemd services to work on multiple linux distributions
and not only on Ubuntu.

We extended and improved the installation script `install.py` in
various ways. For instance now it is mandatory to pass the kind of
installation to perform. Optionally, it is also possible to pass a
port for the DBServer.

When using `install.py --version <branch>`
the latest commit of a branch is downloaded and stored so that
`oq engine --version` prints the git hash.

We removed the `multi_user` flag from the file `openquake.cfg`:
now an installation is automatically considered to be of kind multi
user if the engine was installed with root permissions. Multi users
installations are meant for Linux servers only.

We removed Celery from requirements files, since it has been deprecated
and not used for years.

We added experimental support for ipyparallel and for Ray.
