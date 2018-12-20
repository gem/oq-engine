Release notes for the OpenQuake Engine, version 3.3
===================================================

This is a major release featuring substantial improvements, especially
to the event based calculators. Over 300 pull requests were merged,
making this release twice as big as usual, as a result of the Global
Hazard/Risk Model effort. For the complete list of changes, see the
changelog: https://github.com/gem/oq-engine/blob/engine-3.3/debian/changelog

General improvements on all calculators
---------------------------------------

1. The command `oq engine --run` has now an option `--reuse-hazard` that
can be used to run a risk calculation without having to regenerate the
hazard, or to regenerate the hazard curves/hazard maps/uniform hazard spectra
without having to regenerate the underlying probabilities of exceedence.

2. The feature works because now the engine stores in the database a
checksum for the hazard parameters, so it is able to retrieve a
pre-existing hazard calculation with the same checksum, if available.

3. The engine can now run multiple job.ini files at once, with the syntax
`oq engine --run job1.ini ... jobN.ini`. The calculation ID of the
first job will be used as input for the other jobs.

4. We improved the `minimum_magnitude` feature that allows ruptures of
magnitude below a given threshould to be discarded. The first improvement is
that now the discarding is done *before* sampling the ruptures,
while in the past it was done after sampling the ruptures, so it
is more efficient. The second improvements is that the feature works for
all calculators while before worked only for the event based calculators.
The third improvement is that you can specify different `minimum_magnitudes`
for different tectonic region types, as in this example:
```
minimum_magnitude = {
  "Subduction Interface": 6.5,
  "Subduction Interface LAN": 6.5,
  "Subduction IntraSlab": 6.5,
  "Subduction IntraSlab LAN": 6.5,
  "Active Shallow Crust": 5.0,
  "Active Shallow Crust LAN": 5.0,
  "Stable Shallow Crust": 5.0}
```

5. We extended the [equivalent epicenter distance feature](
adv-manual/equivalent_distance_approximation.rst) to multiple
tectonic region types. While before a single lookup table was
supported, now you can specify a different lookup table for each
tectonic region type in the job.ini file, as in this example
(notice that the name of the section *must* be [reqv]):

```
[reqv]
active shallow crust = lookup_asc.hdf5
stable shallow crust = lookup_sta.hdf5
```

6. Since engine 3.1 the input files of every calculation are zipped and
saved in the datastore. This is very useful in order to reproduce a
given calculation. In this release, due to a bug in `silx view` that
make it impossible to view datastores with large inputs, we moved the
top level dataset `input_zip` into the folder `input/zip`. Moreover
we zip the inputs only when there is no `hazard_calculation_id`,
to avoid storing redundant information.

7. We implemented transparent support for zipped source models and
exposures.  The engine now can automatically unzip source models and
exposures, if any.  The support is transparent in the sense that you
do not need to change the job.ini file. If you have a configuration
file with the line `source_model_logic_tree_file = ssmLT.xml` and you
zip the file `ssmLT.xml` together with all the related source models
into an archive `ssmLT.zip` the engine will automatically look for the
.zip file if the .xml file is missing. Same for zipped exposures.

8. We support site models in .csv format. The old .xml format is not
deprecated and will keep working for the foreseeable
future, but we suggest you to switch to the .csv format anyway, since it is
more convenient to use and faster to parse. You can use any number of
fields: fields not used by the GMPEs will simply be ignored. Here is an
example:

```
$ cat site_model.csv
lon,lat,vs30,z1pt0,z2pt5
6.94712,44.98426,7.452224E+02,4.590022E+01,6.206095E-01
7.10778,45.53722,7.452224E+02,4.590022E+01,6.206095E-01
7.19698,44.82533,2.291181E+02,4.997379E+02,2.392246E+00
7.30266,45.75058,7.452224E+02,4.590022E+01,6.206095E-01
```

9. The engine has been extended to be able to read multiple site
models and/or multiple exposures at once. The multiple site
models/exposures are automatically merged and stored in the datastore
as a single site model/asset collection. This is very useful in
conjunction with the new `aggregate_by` parameter of the
event_based_risk calculator, since it is possible to automatically
compute and export results aggregate by country and other tags
(occupancy, taxonomy, etc). Here is an example of use:

```
[site_params]
site_model_file =
 ../Vs30/Site_model_Argentina.csv
 ../Vs30/Site_model_Colombia.csv
 ../Vs30/Site_model_Paraguay.csv
 ../Vs30/Site_model_Venezuela.csv
 
[exposure]
exposure_file =
  ../Exposure/Exposure_Argentina.xml
  ../Exposure/Exposure_Colombia.xml
  ../Exposure/Exposure_Paraguay.xml
  ../Exposure/Exposure_Venezuela.xml
```

10. We parallelized the splitting/filtering of the sources.
This make the preprocessing phase of the engine a lot faster in
large models (i.e. the Australia model, the EMME models and others).
Also we avoided a needless deepcopy of the source models, thus increasing
the preprocessing performance even more in cases were `applyToSources`
was specified in the source model logic tree file.
The temporary pickled files generated by engine 3.2 have been
removed since now the pickled sources are stored in the `cache_XXX.hdf5`
file, which paves the way for future improvements. Finally, the source
geometries are now saved in the datastore.

11. Now the engine extracts the tectonic region types from the source model
as soon as possible and use this information to reduce the GMPE logic tree
upfront. This is used to log a more reliable estimate about the number of
potential logic tree paths in the model.

12. The `individual_curves` flag is back. By default it is false, but if you
set it to true in the job.ini file then the engine will store the individual
curves for each realization: specifically, the hazard curves and maps for
classical calculations and the loss curves and average losses for event based
calculations. Clearly the data transfer will increase substantially in
the case of thousands of realizations and the calculation may fail: this
is why by default the flag is not set.

Event based: rupture generation
-------------------------------

There was a huge amount of work on the event based calculators. For
what concerns the generation of ruptures, there have been several
improvements.

1. There is a fast mode to manage the case of a large number of
stochastic event sets and/or a large number of samples.  To use that,
you must set `fast_sampling=true` in the job.ini file.  The rupture
generation phase can be more than one order of magnitude faster than
before, as seen in the South America model.

2. We changed the calculator so that the ruptures are returned back in
blocks of at most 1000 elements: this avoids running into the 4 GB
limit for Python pickled objects.

3. We changed approach and converted the ruptures into numpy arrays
(one array for the rupture parameters, one for the rupture geometries)
in the workers and not in the controller node: this avoids the
ruptures piling up in the controller node and running out of memory
for large calculations.

4. Now the ruptures are stored incrementally as they arrive from the workers,
removing the need to keep all of them in memory at the same time, which
was a showstopper for continental scale calculations.

5. The `ruptures` table now contains a field `srcidx` that contains the
association between the rupture and the source that generated it, a
feature that was much desired and requested by multiple users. From
the `srcidx` field one can extract the source information, which is
stored in the `source_info` table in the datastore with the formula
```
src_record = dstore['source_info'][rup_record['srcidx']]
```

6. The `ruptures` table is reordered by rupture ID (also called
rupture serial number) at the end of the rupture generation
phase. This makes it easier to compare different calculations.

7. Since the ruptures are saved in the datastore always, the
parameter `save_ruptures` has been removed; in practice, it is always
true now.

8. It is possible to compute the ruptures without specifying the
sites, thus avoiding the limit on the number of sites. Alternatively,
it is possible to raise the limit by setting the parameter
`max_num_sites` in the job.ini.

9. We restored the phase separation between the computation of the ruptures
and the computation of the ground motion fields - in engine 3.2 they were
intermingled. This has the advantage that the logic tree reduction can be
performed at the end of the rupture generation phase, while before it had
to be performed before, so a slow prefiltering of the sources was necessary.

10. You can disable the prefiltering of the sources by setting
`prefilter_sources=no` in the job.ini. This is recommended for
continental scale computations in which all the sources in the hazard
model are contributing anyway.

11. There was a lot of work also to improve the task distribution and to
avoid slow tasks, which however can be still an issue, unless you use
`fast_sampling=true` or `prefilter_sources=no`.

12. Among the other changes, we changed also the seed algorithm, so you
should not expect to get exactly the same numbers as before. Also, the
`fast_sampling=true` and `prefilter_sources=no` options use a different
algorithm to generate the seeds than the default approach, so you will
stochastically equivalent but not identical results.

Event based: events generation
----------------------------------------

There was also a lot of work on the relation between ruptures and events.

1. For the first time since the beginning of GEM the event ID is an
unique key (finally!). Before it was an unique key only for event based
calculations with sampling, while in the case of full enumeration the
same event could affect different realizations, so the unique key
was the pair (event ID, realization ID). This was very inconvenient
for Cat Risk purposes and has been finally fixed. Now an event belongs
to a realization and cannot affect more than one realization, even
in the case of full enumeration.

2. There is a now a clear relation between event IDs (which are 64 bit
unsigned integers) and rupture IDs (which are 32 bit unsigned
integers): `rupture_ID = event_ID // 2 ** 32` where `//` denotes the
integer division. We are committed to keep this
relation valid forever in the future. This answers the requests of several
users who wanted to know which rupture generated a given event.

2. Now the `events` table in the datastore is generated at the end of the
rupture generation phase and it is ordered by event ID.

3. The `events` table in the datastore is completely different than in
previous versions of the engine and now contains the relation between
events and realizations: by looking there one can see which event belongs
to which realization.

4. The building of the `events` table as well of the associations between
events and realizations has been heavily optimized, so that the engine
can store tens of millions of events in minutes.

5. In order to get the performance, we changed the association between events
and stochastic event sets, which is visible in the XML exporter for the
ruptures. Now the performance is so good that such association is dynamically
computed at export time and not stored anymore in the `events` table, which
is simpler than in the past.

Event based: GMFs generation
---------------------------------

For what concerns the generation of ground motion fields.

1. We changed the calculator to read the rupture geometries in the
workers directly from the datastore, thus avoiding a lot of data
transfer and improving the performance.

2. We optimized the filtering of the ruptures during the ground motion
field generation phase. It is now perfectly possible to pregenerate the
ruptures for an entire continent and then run computations on small
regions, having the non-interesting ruptures filtered out efficiently.

3. There was a big memory optimization effort, so that now the engine
can generate hundreds of GBs of ground motion fields without running
out of memory in the workers nor in the controller node. However,
there are limits on the size of the `gmf_data` table, so it is still
possible to run into errors and also memory errors. In that case you
must check carefully parameters like the `minimum_magnitude` and
the `minimum_intensity`, as well as the number of sites and the
effective investigation time.

4. There was a lot of work on the `ucerf_event_based` calculator, to
make it more similar to the regular one. We fixed some bug, changed the
seed algorithm and removed the `ucerf_risk` calculator, which was a
special case. The regular `ucerf_event_based` calculator is so
efficient now, that in can be used in conjunction with the regular
`event_based_risk` calculation to do the job that was done by the
`ucerf_risk` calculator.

5. We finally removed the GMF XML exporter, which has been deprecated
for years and was too slow to be usable. You should use the CSV exporter
instead. Notice that the GMF XML exporter for scenario calculations
is still there, unchanged, but deprecated.

Event based: risk
---------------------------------

There was also a lot of work on the risk calculator.

1. We introduced a smart single file mode:
while in the past the recommendation was to use two files, a `job_hazard.ini`
for hazard and `job_risk.ini` for risk, now the engine can work with a single
`job.ini` file containing all the required information. It will automatically
start two computations, one for hazard and one for risk. This is the
recommended way to work now, because it plays well with the `--reuse-hazard`
feature.

2. We return from the workers only the statistical loss_curves unless
the parameter `individual_curves` is set to `true` in the `job.ini`
file.

3. We reduced the memory consumption by considering only one site at
the time.

4. The saving of the average losses in the datastore has been optimized.

5. There was a bug in event based with sampling causing incorrect GMFs
to be generated. This affected the South Africa model and it is now fixed.

6. There is now a generic a multi-tag aggregation facility, so it is
possible to aggregate the loss curves and average losses by any combination
of tags. The aggregation is performed entirely at export time with the
command `oq export aggregate_by`; here is an example of usage for the
tags taxonomy and occupancy:

```
$ oq export aggregate_by/taxonomy,occupancy/avg_losses <calc_id>
$ oq export aggregate_by/taxonomy,occupancy/curves <calc_id>
```

Classical/disaggregation calculators
------------------------------------

While most of the work in this release was on the event based calculators,
various features were added to the classical hazard calculators too.

1. We extended the GSIM logic tree XML syntax to allow for
IMT-dependent weights for each GSIM, as requested by our Canadian
users.  Now there can be more than one `<uncertaintyWeight>` inside an
`<uncertaintyModel>` node.  The first `<uncertaintyWeight>` must not
have and "imt" attribute; it is the default weight that applies to all
IMTs. The other `<uncertaintyWeights>` must have an "imt" attribute;
they apply to specific IMTs by overriding the default weight. The
weights are used in the computation of means and quantiles: a nice
thing is that you can run a calculation, save the calculation ID,
change the logic tree file and recompute the statistics without having
to recompute everything from scratch by using the `--hc` flag: `$ oq
engine --run job.ini --hc CALC_ID`. Here is an example of the new
syntax:

```xml
<logicTreeBranch branchID="b11">
  <uncertaintyModel gmpe_table="ngae_usgs_hdf5_tables/NGA-East_Model_01_AA13_sigma.vs450.hdf5">
    GMPETable
  </uncertaintyModel>
  <uncertaintyWeight>
    0.6
  </uncertaintyWeight>
  <uncertaintyWeight imt="SA(10.0)">
    0.5
  </uncertaintyWeight>
</logicTreeBranch>
<logicTreeBranch branchID="b12">
  <uncertaintyModel gmpe_table="ngae_usgs_hdf5_tables/NGA-East_Model_02_AA13_sigma.vs450.hdf5">
    GMPETable
  </uncertaintyModel>
  <uncertaintyWeight>
    0.4
  </uncertaintyWeight>
  <uncertaintyWeight imt="SA(10.0)">
    0.5
  </uncertaintyWeight>
</logicTreeBranch>
```
2. We added the job checksum to the hazard CSV outputs: it means that an
user can check if a given output was really produced with the input
parameters in the current job.ini or not.

3. We replaced the `nodal_dist_collapsing_distance` and
`hypo_dist_collapsing_distance` parameters with a `pointsource_distance`
parameter, documented [here](
adv-manual/common-mistakes.rst#pointsource_distance) and the algorithm used
to collapse the ruptures been optimized.

4. The combination `uniform_hazard_spectra=true` and `mean_hazard_curves=false`
is allowed again, as requested by Laurentiu Danciu. It was made invalid a
few releases ago.

5. The name of the disaggregation output files have changed. Before they
contained the lon, lat of the location, now the contain the site index
(sid). For instance the file named `mean-PGA--3.0--3.0_Mag_XXX.csv` is now
named `mean-PGA-sid-0_Mag_XXX.csv`.

6. We fixed a bug in the disaggregation calculation due to wrong binning
of magnitudes.

7. The speed of the uniform hazard spectra exporter has increased
by an order of magnitude.

General improvements on the risk calculators
-----------------------------------------

1. We now reduce the full risk model to the taxonomies present in
the exposure before saving in the datastore. Risk models are often
huge - valid for an entire continent - but usually we are interested in a
single country, where only a small subset of the possible building taxonomies
are present. This trick reduces quite a lot the data transfer and makes
the risk calculation faster.

2. It is now possible to import hazard curves in CSV format as in the
following example:

```
 hazard_curves_csv = hcurves_PGA.csv hcurves_SA(0.1).csv
```
The XML importer is still working but it has been deprecated.

3. There was a lot of work on the procedure associating the assets to
the hazard sites and the procedure associating the site model
parameters to the hazard sites. Now the hazard sites are extracted
from the site model sites if present, and not from the exposure sites.
In scenario calculations starting from
a rupture, assets outside the `maximum_distance` are automatically
discarded, since the hazard and risk would be zero there.

4. In event based and classical calculations assets are never
discarded unless `discard_assets=true` is set in the `job.ini`. In that
case discarding far away assets is allowed. The feature is risky but
has its use cases: for instance, in the exposure for France there may
be assets in French Polynesia and you will probably want to discard those.

5. There was a bug in the gridding of the exposure feature (new in
engine 3.2) causing an incorrect site collection to be produced in some
cases. As a consequence sources that should have been filtered were
not filtered, thus causing the numbers produced by the engine to be
incorrect.

Scenario from ShakeMap
----------------------

There was a lot of work on the "Scenario from ShakeMap" feature, introduced
ine engine 3.1 and documented here: https://github.com/gem/oq-engine/blob/engine-3.2/doc/scenario-from-shakemap.md

1. The USGS site changed the layout of the pages, thus breaking the
feature.  Now we extract the download URL from the official JSON feed instead
of scraping the Web Page, so the problem is solved for good.

2. We fixed a ShakeMap unzipping bug that was affecting old ShakeMaps
in which the archive did not contain the expected file at top level but
inside a directory hierarchy.

3. We added a good error message when the standard deviations as extracted
from the ShakeMaps are all zeros.

4. We added a way to disable spatial correlation by setting
`spatial_correlation=no correlation` in the job.ini.
We disabled it by default, to avoid getting non-positive defined
matrices - due to numeric errors - in some circumstances.

5. ShakeMaps contain four intensity measure types: PGA, SA(0.3),
SA(1.0) and SA(3.0). If your vulnerability/fragility model contains
additional IMTs which are not in the ShakeMap the calculation will
fail. But, if you really want, you can set `discard_assets=true`
and the engine will discard the assets with taxonomies associated to 
the missing IMTs and perform the calculation anyway. This is clearly
dangerous: use the feature at your own risk!

6. The ShakeMap feature works by building a distribution of GMFs with
mean and standard deviations compatible with the ones in the
downloaded ShakeMap. Due to the stochasticity of the procedure, one
can produce particularly large GMFs, especially if site
amplification is included.  Now, if the ground motion
values or the standard deviations are particularly large the user will
get a warning about suspicious GMFs; moreover GMFs larger than 5g will
be automatically discarded. You should take the results with care in
such circumstances. Actually, you should take the results with care in
any circumstance, since there are many poorly understood effects in
such calculations.

7. We fixed a bug in the GMF export, that was broken; now you can inspect
the GMFs that were generated by the engine.

8. We updated the relevant documentation.

Bug fixes
---------

1. There was a bug when the spectral accelations were specified in a different
way between hazard and risk (i.e. `SA(1)` in the vulnerability functions and
`SA(1.0)` in the job_hazard.ini file). Now they are normalized to a common
format, thus avoiding rounding issues.

3. The option `--config-file` of the `oq engine` command was ignored
and has been so for many releases. Thanks to Nick Ackerley for
noticing. It has been fixed now.

4. The generation of GMFs from ruptures was broken in the case of a filtered
site collection. This has been fixed.

5. There was a long standing bug in some `oq` commands, like `oq export` and
`oq show` that made it impossible to export or view the results of a
calculation ran by another user. This has been solved.
The engine looks in the database first and from there it retrieves the path
to the right datastore to use. This strategy also manages correctly the
case when there is a custom $OQ_DATADIR.

6. The engine automatically creates the `export_dir` if it has the
permissions to do so. From this release the feature works recursively and
allows to create also a tree of nested directories. Moreover now a
relative export_dir is relative to the directory where the job.ini
file is, and no more to the current working directory.

7. For historical reasons the hazard exporters were littering the export
directory with hidden files like `.hcurves.zip`. This has been fixed now.

8. Warnings when parsing the job.ini file were displayed only on stderr,
but not logged. This has been fixed and now we begin logging on the database
even before starting the calculation.

Validity checks
---------------

1. We restored an important check in the source model logic tree parser:
now if the user lists in `applyToSources` a source ID that does not exist
in the source model an error is raised. Before it was silently ignored
and the users ended up with a calculations with duplicated results in
different realizations.

2. We fixed the check on missing hazard IMTs: now if some IMTs are missing, the
error is correctly raised before starting the calculation, not in the middle
of it.

3. Sometimes users forget to include an exposure, both in job_hazard.ini and
job_risk.ini files. Now a clear error message is displayed.

4. Sometimes users forget to specify the IMTs in an event based calculation:
now an error is raise before starting the calculation and not in the
middle of it.

5. We added a check for empty risk model files, since an user was able to
elicit this situation.

6. We fixed the uniqueness check for the vulnerability function IDs, which was
working only for files in format NRML/0.4 and not NRML/0.5.

7. We added a check on large logic trees for event based risk calculations.
Now if your logic tree has more than 100 potential paths an error will be
raised, suggesting to switch to logic tree sampling. It is still
possible to use full enumeration by raising the parameter `max_potential_paths`.
Notice that due to logic tree reduction the real number of realizations
can be a lot less than the number of potential paths.

8. We added a check in the source model parser to make sure that the tectonic
region type declared in the <SourceGroup> node is consistent with the
tectonic region type declared in the underlying source nodes.

9. There is now a better error message when there are too many tags in
an exposure.  This usually happens when the user makes a mistake and
uses an unique field as a tag.

10. We removed the PlanarSurface check when unneeded.

hazardlib/HMTK
---------------

1. The most important new feature in hazardlib is the introduction of
a `NRCan15SiteTerm` GMPE class that can be used to account for local
soil conditions in the estimation of ground motion. While the site term
was developed for the 2015 Canada model (hence the name) it can be
applied in more general situations. The usage in the gsim logic tree
file is simple; for instance to apply the site term to the BooreAtkinson2008
GMPE just write

```xml
                  <uncertaintyModel gmpe_name="BooreAtkinson2008">
                    NRCan15SiteTerm
                  </uncertaintyModel>
```

2. Another important change was in the GMPE Pezeshk et al 2011. We found
a bug in the implementation and fixed it, so now if your model uses this
GMPE you will get slightly different numbers.

3. Chris van Houtte from GNS Science contributed a new site_class site
parameter, which is a single-letter used in the GMPE McVerry2006 for
New Zealand.

4. We added a modified version of the Atkinson and Macias (2009) GMPE for
subduction interface earthquakes. This GMPE is modified following what
proposed in Atkinson and Adams (2013).

5. It is now possible to specify an "undefined" rake value.  This is
needed to support cases admitted by some GMPEs such as, for example,
the Boore and Atkinson (2008). In the XML source model you can just
write `<rake>undefined</rake>`.

6. We added two versions of the Silva et al. (2002) GMPE as described in
the report "Development of Regional Hard Rock Attenuation Relations
For Central And Eastern North America", available
at http://www.pacificengineering.org/.

7. We optimized the splitting of complex fault ruptures and fixed a bug
in the splitting of simple fault rupture with nodes
<hypo_list> or <slip_list>.

8. We added a line `DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}`
to the `ChiouYoungs2008SWISS01` class, thus making it possible to use this
GMPE in event based calculations.

9. Graeme Weatherill contributed a fix in the HMTK plotting completeness
functionality.

10. Stéphane Drouet contributed several Drouet & Cotton (2015) GMPEs,
including the 2017 erratum.

11. We fixed a few bugs in the GMPEs for Canada affecting the event based
calculator.

oq commands
-----------

1. There is a new command `oq prepare_site_model` that allows to prepare
a site_model.csv file starting from an exposure and an USGS vs30 file.
It is documented here: https://github.com/gem/oq-engine/blob/engine-3.3/doc/oq-commands.md#prepare_site_model

2. There is a new command `oq compare` to compare the hazard curves and maps
of different calculations. It is meant to be used for sensitivity analysis.
It is undocumented, since it is still experimental, but you use the help
to see how it works:
```
$ oq compare --help
usage: oq compare [-h] [-f] [-s 100] [-r 0.1] [-a 0.0001]
                  {hmaps,hcurves} imt calc_ids [calc_ids ...]

Compare the hazard curves or maps of two or more calculations

positional arguments:
  {hmaps,hcurves}       hmaps or hcurves
  imt                   intensity measure type to compare
  calc_ids              calculation IDs

optional arguments:
  -h, --help            show this help message and exit
  -f, --files           write the results in multiple files
  -s 100, --samplesites 100
                        number of sites to sample
  -r 0.1, --rtol 0.1    relative tolerance
  -a 0.0001, --atol 0.0001
                        absolute tolerance
```
3. The `oq zip` command has been substantially enhanced and it can be used
also to zip exposures and source models.

4. The command `oq shell` now can also be used to run scripts in the
Python environment of the engine.

5. The command `oq plot_assets` now also plots the discarded assets, if any.
Moreover it plots the site model, if any.

IT changes
-------------------

1. As promised in the last release, the engine does not work with Python
3.5 anymore. Python >= 3.6 is required. Python 3.7 is not officially
supported but we know that the engine works with it.

2. The support for the operating system Ubuntu 14.04 has ceased ad we do not
release packages for it anymore. You can still run the engine on Ubuntu
14.04 but you have to install from sources or with the self-installing
file that we provide for generic Linux systems.

3. In the Linux installation from packages.We dropped supervisord and now
we use only native systemd inits.

4. A cluster installation now officially requires to set up a shared
filesystem and to configure the `shared_dir` parameter in the file
`openquake.cfg`. Without that, classical calculations will fail during
the calculation of statistics and event based calculations will fail
during the computations of GMFs, with some kind of "File not found"
error. The documentation is [here](installing/cluster.md).

5. We now have a mechanism to emulate a cluster on a single machine
by using docker containers.

6. Now we check if the engine is running out of memory also in the workers
nodes, and if this is the case a warning is logged in the main log, a
feature that we desired for years.

7. There were several changes in the parallelization library and now
all the traffic back from the workers goes through ZeroMQ, not
RabbitMQ.  As a consequence, it is easier to support backends
different from celery and we did some experiments with dask.

Other
-----

We have now in place a mechanism to run the global hazard mosaic
calculations nightly so to avoid regressions in the models and the
code.

We have started to work on a [Manual for Advanced Users](
adv-manual/introduction.rst) and we have added two new FAQ pages,
one for [hazard](faq-hazard.md) and one for [risk](faq-risk.md).
