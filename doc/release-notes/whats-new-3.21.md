Release notes v3.21
===================

Version 3.21 is the culmination of 4 months of work involving over 240 pull requests.
It is the release featuring the greatest performance improvements of the last few years.
It is aimed at users wanting the latest features, bug fixes and maximum performance.
Users valuing stability may want to stay with the LTS release instead
(currently at version 3.16.8).

The complete set of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.21/debian/changelog

A summary is given below.

Classical calculations
----------------------

We significantly reduced the memory consumption in classical calculations:
now all the models in the GEM mosaic run with less than 2 GB per core
(previously we required 4 GB per core). This result was mostly achieved by reducing
the precision of the PoEs to 32 bit instead of 64 bit, which required a
major refactoring and working in terms of rates, since rates are much less
subject to numerical errors than PoEs.

The other mechanism to reduce the memory consumption was changing the
implementation of CollapsedPointSources to use arrays rather than
plain source objects. To give a concrete example, in the case of the
USA model that reduced the memory consumption (when using the tiling strategy)
from about 3 GB per core to just 1.2 GB per core.

Moreover, CollapsedPointSources have been extended to collect
sources with different magnitude-scaling-relationships, which also makes
the engine faster, however the change affects only a few models with minor differences.

Thanks to the memory reduction and other optimizations, like refining the size
of the arrays when computing the mean and standard deviations from the
GMPEs, or optimizing the procedure updating the probabilities of no
exceedency, now 3x faster, the performance of classical calculations
improved substantially. For instance, the model for EUR is nearly 2x
faster than before, the model for Canada is 1.4x faster, while the
model for USA is 1.25x faster on a machine with 128 cores.

We added a `tiling` flag in the job.ini file to make it possible to specify
which version of the classical calculator to use (tiling or regular);
if the flag is not specified, the engine will continue to autonomously
select the most appropriate calculator, however with a different logic
than in the past.

We optimized the logic tree processor so that it is now possible
to compute mean rates exactly (if `use_rates` is set) even with
millions of realizations. In particular we managed to run the EUR model
with 302,990,625 realizations, but it required over 100 GB of RAM.

The splitting of the sources in groups now works slightly differently and more
groups can be generated sometimes, but there is an additional guarantee: the sources in a
same group will all have the same temporal occurrence model. This allowed some
internal simplification.

The --sample-sources feature now works differently (by tiling)
and it is faster (measured 4x faster for the USA model) and more reliable than before.

Finally, logging the progress of the calculation now works much better (previously
often the progress went from 0 to 50% abruptly and then from 50% to 100%
equally abruptly).

Event based/scenario calculations
---------------------------------

In event based calculations we were able to spectacularly reduce the
memory consumption in situations with millions of sites. For instance,
whereas previously a calculation with 6 million sites required over 80 GB per
core and it inevitable ran out of memory, now it requires less than 2 GB per core
and it completes correctly.

Moreover, the performance improved tremendously in the case of many GMPEs, like
for EUR, where there are up to 19 GMPEs per tectonic region type. The
reason is that some calculations were needlessly repeated in the GmfComputer.
Now generating the GMFs in the EUR model is 13 times faster than
before. In models with only 2 or 3 GMPEs the improvement is
less visible, but still there.

We decided to make the parameters `minimum_magnitude` and `minimum_intensity` mandatory,
except in toy calculations. The reason is that users often forget to set such parameters
and as a consequence their calculations become extremely slow or run out of memory after
many hours. Now they will get a clear error message even before starting the calculation.

If the `custom_site_id` field is missing in the site model, 
we are now generating it automatically as a geohash,
since it is extremely useful when comparing and debugging GMFs.

Some users wanted to be able to access intermediate results (in
particular the GMPE-computed mean and the standard deviations tau and
phi) for each site, rupture, GMPE and intensity measure type. This is now
possible by setting the flag

mea_tau_phi = true

in the job.ini file. Please notice that setting the flag will double
the disk space occupation and make the calculation slower, so you are
advised to enable this feature only for small calculations for
debugging purposes. It will work both for scenarios and event based
calculations.

We changed the scenario calculator to discard sites over the integration
distance from the rupture, for consistency with the event based calculator
and for consistency with the algorithm used in Aristotle calculations.

hazardlib
---------

Enrico Abcede and Francis Bernales extended the Campbell and Bozorgnia (2014)
GMPEs to work with the intensity measure types IA and CAV.

Fatemeh Alishahiha contributed a couple of GMPEs: one
with the Zafarani et al (2018) and one with the Ambraseys (2005),
relevant for Iran.

Chris di Caprio contributed a bug fix for the Kuehn (2020) GMPE, in
the RegularGridInterpolator, that must use extrapolation to handle
floating point edge cases.

Eric Thompson pointed a typo in the aliases for the Kuehn et al GMPE
("KuehnEtAl2021SInter" in place of "KuehnEtAl2020SInter") and missing
aliases for "KuehnEtAl2020SSlab". It has been fixed now.

Kyle Smith contributed the Arias Intensity and Cumulative Absolute
Velocity ground motion models from Sandikkaya and Akkar (2017).

Nicolas Schmid fixed an incorrect formula used in ShakeMap calculations
(see https://github.com/gem/oq-engine/pull/9890).

Marco Pagani extended the Chiou Youngs (2014) GMPEs to optionally
include the modifications by Boore Et Al. (2022).

We added a helper function `valid.modified_gsim` to instantiate ModifiableGMPE
objects with less effort, for usage in the GEESE project, You can see an example in
https://docs.openquake.org/oq-engine/master/manual/user-guide/inputs/ground-motion-models-inputs.html#modifiablegmpe.

Since the beginning hazardlib has been affected by a rather annoying
issue: pollution by large CSV files. CSV files are required
by the GMPE tests to store the expected mean and standard deviations
computed from a set of input parameters like magnitude, distance and vs30.

Unfortunately people tended to be liberal with the size of the CSV
files, including files larger than needed, and we ended up with 480 MB
of expected data. The sheer amount of data slows down the download of
the repository, even with the shallow clone, and makes the tests
slower than needed.

We were able to cut down the CSV files by two thirds without losing
any test coverage. Moreover, we added a check forbidding CSV files
larger than 600k to keep the problem from reappearing in the near
future.

AELO project
------------

Work on the [AELO project](https://www.globalquakemodel.org/proj/aelo)
continued with various AELO year 3 updates. We can now
run all available IMTs (before we considered only 3 IMTs) and use
the ASCE7-22 parameters (see https://github.com/gem/oq-engine/pull/9648).

At the level of the Web Interface it is now possible to choose
the desired `asce_version` between ASCE 16 and ASCE 41. The version
used to perform the calculation is then displayed in the outputs page.

We began the work for supporting vs30 values different from 760 m/s by implementing
the ASCE soil classes.

We added exporters for the Maximum Considered Earthquake and for the
ASCE07 and ASCE41 results.

The `geolocate` functionality has been extended to support
multipolygons, which are used to model geometries crossing the
International Date Line.

As a consequence, a point exactly in the middle of two mosaic models
can be associated differently than before.

Aristotle project
-----------------

We continued the work on the
[Aristotle project](https://www.globalquakemodel.org/proj/aristotle).

Given a single file `exposure.hdf5` containing the global exposure,
global vulnerability functions, global taxonomy mappings and global site
model, and a rupture file or ShakeMap event id, an Aristotle calculation 
is able to compute the seismic risk in any place in the world, apart from the oceans.

In this release, the procedure to generate the `exposure.hdf5` file
from the global risk mosaic has been improved and the taxonomy
mappings for Canada and USA, which were missing, have been added.

Moreover the Aristotle web interface has been much improved. It is
possible for the user to download from the USGS site not only rupture
files but also station files, thus taking advantage of the Conditioned
GMFs calculator. Custom rupture files or station files can also be uploaded if the user
has them locally. Errors in the station files are properly notified,
just as errors in the rupture geometries (not all USGS ruptures can be
converted to OpenQuake ruptures yet).

When the rupture.json file is not available on the USGS page for an event,
the software checks if the finite-fault rupture is available and it loads
the relevant information from it instead. Note that this fallback approach may
also fail, especially in the early stage right after an event,
when not enough information has been uploaded to the USGS website yet.
In this case, in order to proceed, the user needs to upload the rupture
data via the corresponding web form.

We improved the procedure for generating hazardlib ruptures, automatically setting
the `dip` and `strike` parameters when possible. In case of errors in
the geometry a planar rupture with the given magnitude, hypocenter dip
and strike is automatically generated.

The visualization of the input form and the output tables has improved.

It is now possible to specify the parameter `maximum_distance_stations`,
either from command line or from the WebUi. The `maximum_distance` was
already there, but now has a default of 100 km to ensure faster calculations.

We added a dropdown menu so that the user can override the
`time_event` parameter, which by default is automatically set
depending on the local time of occurrence of the earthquake.

The page displaying the outputs of a calculation now includes some additional
information. On top of the page, the local time of the event is displayed,
together with the indication of how much time passed between the event itself
and the moment the calculation was started. This is useful for instance to
compare results obtained before and after rupture or station data become
available in the USGS site.

The plots showing the average ground motion fields and the assets have been
improved. In particular, the latter now also display the boundaries of the
rupture.

We added a method `GsimLogicTree.to_node`, useful to produce an XML
representation of the gsim logic tree used by an Aristotle calculation.

Secondary perils
----------------

Lana Torodović implemented the Nowicki Jessee et al. (2018) landslide
model, which is part of the USGS Ground Failure Product. It is documented here: 
https://docs.openquake.org/oq-engine/3.21/manual/underlying-science/secondary-perils.html#nowicki-jessee-et-al-2018

When exporting the `gmf_data` table, we decided to include the secondary peril
values, if present. Technically they are not GMFs, just fields induced by the GMFs,
but it is convenient to keep them in the `gmf_data` table, also for visualization
purposes via the QGIS plugin.

Bug fixes
---------

There were various fixes to the conditioned GMFs calculator:

- we changed the Cholesky decomposition algorithm to reduce the issue of
  small negative eigenvalues
- we fixed an error when using a `region_grid_spacing` by extending the site
  collection to include the stations
- we fixed a couple of bugs in the association of the site parameters to the sites
- we added an uniqueness check for the station coordinates

We fixed a bug with the conditional spectrum calculator in the case of calculations
with non-contributing tectonic region types, i.e. when all the sources of a
given tectonic region type are outside the integration distance.

Running a scenario or event based calculation starting from a CSV file of ruptures raised
a KeyError: "No 'source_mags/*' found in <DataStore>"
when exporting the ruptures. It has been fixed now.

The new Japan model was failing with an error in event based calculations due
to an excessive check (a leftover from the past). It has been fixed now.

The `avg_gmf` was failing sometimes in the presence of a filtered site collection.
It has been fixed now.

In situations with more than ~90 realizations, exporting the realizations CSV
was causing an encoding error. It has been fixed now.

In presence of multi-fault sources far away from the sites (i.e. over the integration
distance) an error "object has no attribute msparams" was raised. It has been fixed now.

We improved the error message displayed when the user forgets to specify the exposure file
in a risk calculation.

We removed the exporter for the output `disagg-stats-traditional` since it was
incorrect, with no easy way to fix it. We kept the exporter for
`disagg-rlzs-traditional`, which was correct.

Using half the memory on Windows
--------------------------------

Recent processors have significantly more threads than in the past,
however the typical amount of RAM on consumer machines has not
increased much. Moreover, often a significant amount of RAM is reserved to
the GPU and a huge amount of memory is eaten by the browser.

Therefore, if the engine kept spawning a process for each thread
as in the past, it would likely run out of memory or degrade the performance
to the so-called "slow mode", with a single thread being used.

To cope with this situation, now the engine on Windows uses by default
only half of the available threads. You can change this default by
setting the parameter `num_cores` in the `[distribution]` section of
the file `openquake.cfg` in your home directory. Be warned that
increasing `num_cores` will increase the memory consumption but not
necessarily the performance.

On non-Windows platforms nothing changes, i.e. the default is still to
use all available threads. The reason is that Apple silicon does not
use hyperthreading (i.e. it uses half the memory compared to
processors with hyperthreading) while Linux is mostly used for servers
that typically have more memory than a consumer machine, so there is no
pressing need to save memory.

HPC support via SLURM
---------------------

Since version 3.18 the engine has experimental support for HPC clusters
using the SLURM scheduler. However, the original logic required spawning a SLURM
job for each engine task, meaning that we immediately run into the limit of 300
SLURM jobs when the CEA institute graciously gave us access to their cluster.

To overcome this limitation, the approach used in engine 3.18 has been
abandoned and the code completely rewritten. With the current approach there is a single
SLURM job for each engine job and we can easily scale to thousand of cores by simply
passing the number of desired nodes to the `oq engine --run` command (see
https://docs.openquake.org/oq-engine/3.21/manual/getting-started/installation-instructions/slurm.html)

Notice that supporting thousands of cores required substantial work on the calculators too.

For instance, now classical calculations make use of the `custom_tmp`
directory in `openquake.cfg` (mandatory in SLURM mode) to store the
PoEs in small temporary files, one per task. In tiling calculations
that reduces the data transfer effectively to zero, while in
non-tiling calculations it only reduce it, more or less depending on
the calculation. That required to change the postclassical phase of
the calculation to be able to read the PoEs from the `custom_tmp` and
only from the `calc_XXX.hdf5` file.

Moreover we had to invent a mechanism to limit the data transfer
in non-tiling calculations, otherwise we would still run out of memory on the
master node in large HPC clusters simply by adding new nodes.

The tiling feature is now less used than before.
For instance, prior to engine 3.21 the USA hazard model was executed by using the tiling
strategy. While this is acceptable if you have say 128 cores, it is extremely inefficient
if you have 1024 cores or more. Thus in engine 3.21 we went through great effort to avoid
the tiling approach when it is inefficient: in particular the USA model with 1024 cores is
5x faster by not using tiling.

Be warned that the more cores you have, the more you are in uncharted
territory and it is entirely possible that adding nodes will slow down your calculation.
We recommend not to exaggerate with the number of nodes, 8-16 nodes with 128 cores each
have been tested, using more nodes comes at your risk.

The SLURM support is still considered experimental and we know that there
are still a few issues, like the fact that the SLURM job may not be
killed automatically in case of hard out-of-memory situations and
therefore must be killed manually, or the presence of slow tasks in
some calculations, however it is good enough to run all the hazard models
in the GEM mosaic.

Commands like `oq show performance`, `oq workers status` and `oq
sensitivity_analysis` now work correctly in SLURM mode: the first will
show the total memory used on all nodes, and not only the master
node. The second will show how many workers are active for each
node. The third will generate a script that will launch a SLURM job
for each combination of parameters in the sensitivity analysis.

Other `oq` commands
-------------------

After a major effort we were able to extend the command
`oq plot sources?` to work with all kinds of sources.

We fixed `oq prepare_site_model` to compute `z1pt0` and `z2pt5` correctly
for sites in Japan, i.e. by using the regionalized NGAWest2 basin effect
equations.

We fixed `oq reduce_sm` for calculations with nonparametric sources, which
was raising an error.

We fixed `oq plot_avg_gmf` to work remotely.

We extended `oq info` to .csv files, for pretty-printing purposes.

We improved the command `oq plot_assets`.

We added the commands `oq plot "rupture?"` and `oq plot "rupture_3d?"`.

We added add command `oq compare oqparam` and we improved `oq compare sitecol`
and `oq compare assetcol`.

We added a debugging command `oq compare rates` and a `oq compare asce` functionality.

We changed `oq run` to automatically generate the db in single user mode.

Other
-----

There were a few cosmetic improvements to the WebUI and we added
a cookie consent functionality for compliance with the European law.

For usage in the GEESE model, we added a method `OqParam.to_ini` which can be
used to generate an `.ini` file equivalent to the original input file. This is
useful when the calculation parameters are dynamically generated. Currently it
works only for hazard calculations.

As usual we improved the documentation, in particular about how to run calculations
programmatically using the pair [create_jobs/run_jobs]
(https://docs.openquake.org/oq-engine/3.21/manual/contributing/developing-with-the-engine.html#running-calculations-programmatically)
