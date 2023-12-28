Release notes v3.16
===================

Version 3.16 is the second Long Term Support (LTS) release of the engine,
replacing version 3.11 after a gap of two years. It is the result of five
months of work involving over 320 pull requests, featuring major
optimizations and new features.

The complete list of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.16/debian/changelog

A summary is given below.

Memory optimizations in classical PSHA
--------------------------------------

Later this year GEM will release an updated version of the Global
Hazard Mosaic using a finer grid (with ~3 times more sites) and more
intensity measure types and levels (7x25 instead of 6x20). Therefore
the new models will be roughly 5 times more computational intensive,
requiring 5 times more memory and disk space.

Special care was taken to reduce the memory consumption of classical
calculations. For instance, the ESHM20 model for Europe, which before
ran on our server with 512 GB of RAM, with version 3.15
would require over 2 TB and it would just run out of memory.

With version 3.16 the engine automatically splits the sites in tiles
to keep the memory below a limit of around 2 GB per core and runs
the tiles in parallel. For even larger calculations, that would not be
enough, since the logic of the classical calculators requires
keeping a huge array of PoEs (~160 GB for the updated European model)
in the master node that would ran out of memory. In that case
the engine runs the tiles sequentially: for instance, by splitting in 4 tiles,
only 40 GB would be required on the master node for Europe.

All that is done automatically: previously the user had to painfully
determine the right `max_sites_per_tile` parameter, which is not
needed anymore. There is instead a parameter `pmap_max_gb` with a
default value 1 which can be used to control the memory used on the
workers, but regular users will never have to touch it.

We improved the point source grid approximation to keep the runtime of
the models reasonable. On top of a performance improvement (up to a 2x
speedup by keeping the same precision) we fixed a memory issue with
models containing point sources with very large magnitudes (such
practice is arguably incorrect, but common in some of the models of the
GEM mosaic). In such situations, the magnitude-scaling relationship can
produce rupture lengths of thousands of kilometers, causing the point
source gridding approximation to keep in memory huge amount of data
and thus sending the system out of memory. We have solved the problem
by limiting the rupture radius to the integration distance; moreover
the engine prints a warning when point sources with magnitude >= 8 are
found, so that new models can avoid the issue altogether.

Finally, we notice that for small calculations the improvements
will be less visible or even not visible at all, depending on the
parameters and the optimizations used.

Other improvements in classical PSHA and disaggregation
-------------------------------------------------------

We optimized the parsing of the sources in XML format (with a 35x speedup for
the Alaska model) since for some models it was the dominating factor
in single-site calculations.

We optimized the preclassical phase of a calculation in presence of
large complex fault sources (this was affecting the South America
model and others) since slow tasks were the dominating factor in
single-site calculations.

We improved substantially the preclassical runtime in calculations
with multifault sources (relevant for the UCERF model and others) by
splitting the sources upfront.

As usual the source weighting algorithm has been refined to reduce the slow
tasks in the classical phase of the calculation.

The postclassical calculator has been optimized to reduce the PoEs
reading time, which could become substantial in extra-large
calculations, expecially on clusters with a large number of
cores. This has become relevant now that the calculations are becoming
5 times larger; for instance for the European model the number of PoEs
to read will increase from ~32 GB to ~160 GB.

As part of the future Global Hazard Model update the models have changed
to convert the Intensity Measure Component of the GMPEs to "Geometric Mean"
when possible; when not possible, a warning is printed. To enable this
feature you just need to add a line

`horiz_comp_to_geom_mean = true`

to your job.ini file.

In the context of the [METIS project](https://metis-h2020.eu/) we
added a way to include the aftershock contribution to the hazard by
reading a file of corrected occurrence rates for the ruptures of a
model.

The `disagg_by_src` feature has been changed to store only the mean
PoEs across the realizations for models using sampling. The user can
customize what happens by setting the flag `collect_rlzs` ("true"
means store the mean, "false" mean store all realizations). Thanks to
this change now large models like EUR do not run out of memory when using
the flag `disagg_by_src=true`. 

There was a major optimization in the disaggregation calculator (we measured
speedups of over 76 times in the disaggregation part) obtained by replacing
the `scipy.truncnorm.sf` function with our own function. Also, our own
`truncnorm_sf` function has been simplified and truncation levels close
to zero (<= 1E-9) are now as treated as zero.

We added the possibility to define the edges of the bins explicitly,
which is useful when comparing disaggregations coming from different
calculations.

When using `num_disagg_rlzs=0` the engine was logging the nonsensical
message `Total output size: 0 B`. Now you get the correct output size.

In the context of the new release of the Global Hazard Mosaic we are
adding some feature to make the engine aware of the mosaic, like a utility
to determine which mosaic model to use given a longitude and latitude.

The header of the UHS files changed slightly, using fewer digits, to make the
test run across different platforms in spite of minor numeric differences.

Additions to hazardlib
----------------------

[Prajakta Jadhav](https://github.com/Prajakta-Jadhav-25) and Dharma
Wijewickreme contributed a new GMPE for Zhang and Zhao (2005) (see
https://github.com/gem/oq-engine/pull/7766).

[Trevor Allen](https://github.com/treviallen) contributed some enhancements 
to Australian GMPEs (see https://github.com/gem/oq-engine/pull/8205).

[Guillaume Daniel](https://github.com/guyomd) contributed a bug-fix to
the HMTK, in the function used for the Stepp (1972) completeness
analysis (see https://github.com/gem/oq-engine/pull/8127).

[Graeme Weatherill](https://github.com/g-weatherill) contributed some aliases 
for the GSIMs used in the ESHM20 model for Europe.

[C. Bruce Wprden](https://github.com/cbworden) asked to change the 
AbrahamsonEtAl2014 GMPE to extrapolate the Vs30 so that it could be used 
with the official J-SHIS Vs30 model of Japan 
(see https://github.com/gem/oq-engine/pull/8171).

We implemented the correction of Lanzano et al. (2019) as described in
Lanzano et al. (2022).

We introduced a new GMPE KothaEtAl2020regional where the site-specific
(`delta_c3` and its standard error) and source-specific (`delta_l2l` and
its standard error) values are automatically selected.  Since the
procedure is slow it is meant to be used solely for single-site
calculations. It is also likely to change in the future.

Since a few versions ago, the engine has the ability to modify the magnitude
frequency distribution from the logic tree with code like the following:
```xml
     <uncertaintyModel>
        <faultActivityData slipRate="20.0" rigidity="32" />
     </uncertaintyModel>
```
Now it is also possible to specify a `constant_term`; before it was hard
coded to 9.1.

ModifiableGMPEs with underlying GMPETables were not receiving a
single magnitude when calling the `compute` method, thus resulting
into an error. This has been fixed.

The AtkinsonBoore2006 GMPE was giving an error when used with stress drop
adjustment, a regression caused by the vectorization work performed
months ago. This has been fixed.

Source groups with sources producing mutually exclusive ruptures have
been extended to include the concept of `grp_probability` (before it
was hard-coded to 1); this is relevant for the new Japan model.

Risk
----

We have two major new features, which for the moment are to be considered
experimental: ground motion fields conditioned on station data, as
discussed in https://github.com/gem/oq-engine/issues/8317, and reinsurance
calculations, as described in https://github.com/gem/oq-engine/issues/7886.

We welcome users wanting to try the new features and understanding that
usage and implementation details may change in future versions of the engine.
We also welcome feedback on these experimental features.

We optimized the rupture sampling for MultiFaultSources and now the
UCERF model is usable, even if still slow in the sampling part.

We implemented a major optimization in `event_based_risk` starting from
precomputed ground motion fields. As a matter of fact, it is now
possible to compute GMFs at continental scale, producing hundreds
of gigabytes of data, and then run risk calculations country-by-country
without running out of memory. This case was previously intractable.

As part of this work, we removed the limit of 4 billion rows for the
`gmf_data` table and we added a parameter `max_gmvs_per_task` in the
job.ini that can be used to regulate the memory consumption (the
default is 1,000,000).

We added a parameter `max_aggregations` in the job.ini: its purpose is
to make it possible to increase the number of risk aggregations that was 
previously hard-coded to 65,536. The default is now 100,000 aggregations.

As a convenience, we changed the risk calculators to reuse the
hazard exposure when running with the `--hc` flag: before the exposure
had to be read every time, even if it was already saved in the hazard
datastore, which was annoying and slow for large exposures with millions
of assets.

We added an early consistency check on the taxonomy mapping in case of
consequences, so that now you get a clear error before starting the
calculation and not a confusing error in the middle of it.

For large exposures and many realizations now the engine raises an early
error forcing the user to set the parameter `collect_rlzs`.
This is preferable to going out of memory in the middle of a computation. 

Finally, we changed the logic in the calculation of loss curves and
averages in `classical_risk/classical_bcr` calculations, by taking
into consideration the `risk_investigation_time` parameter (see
https://github.com/gem/oq-engine/pull/8046). As a consequence, the
numbers generated are slightly different than before. We now also raise an
error when a loss curve is computed starting from a flat hazard
curve, since in that case numeric errors make the results
unreliable. The solution is to reduce the hazard investigation time to
have a less flat curve.

Bug fixes and new checks
------------------------

We fixed a long standing a bug which entered in engine 3.9 and was 
affecting the USA model, specifically the area around the New Madrid 
cluster, producing incorrect hazard curves and maps.

We fixed a bug in models using the `reqv` feature to collapse point sources:
all point sources were collapsed, and not only the ones with the
tectonic region types specified in the `reqv` dictionary.

We raised the recursion limit to work around an error
`maximum recursion depth exceeded while pickling an object` happening in
classical calculations with extra-large logic trees.

We fixed a bug breaking the fullreport.rst output for NGAEast GMPEs.

`min_mag` and `max_mag` were not honored when using a
magnitude-dependent maximum distance: this is now fixed.

We fixed a bug when running a classical calculation starting from a
preclassical one, appearing only in the case of tabular GMPEs, like in
the Canada model.

We fixed a bug such that using the ``--hc`` option caused the site model of
the child calculation to be associated incorrectly.

We removed the conditional spectrum calculator which was giving incorrect
results. You should use a later versions of the engine (>=3.17) if you
want it to work reliably.

We fixed a bug in the `classical_risk` calculator, where the `avg_losses`
output was not stored and therefore not exportable
(see https://github.com/gem/oq-engine/pull/8267).

We fixed a bug in vulnerability functions using the Beta distribution:
the case of zero coefficients of variation was not treated correctly
(see https://github.com/gem/oq-engine/pull/8060).

We fixed a few bugs affecting the visualization of risk curves and
aggregated risk via the QGIS plugin.

oq commands
-----------

For years the engine has had a command `oq nrml_to` to convert source
model in NRML format to CSV or geopackage format, but we were missing
a command `oq nrml_from` to convert back to NRML. This has been
finally implemented, therefore it is now possible to read a source model,
convert it into .gpkg, modify it with QGIS and covert it back to NRML,
a feature users wanted for years.

However, not all source models are convertible since not all source
typologies are convertible, nor there are plan to make them
convertible in the future. For instance multi-fault sources have an efficient
HDF5 storage and it would make little sense to convert them into .gpkg,
because they are so large that they would simply send QGIS out of memory,
not the mention the fact that it would be impossible to edit millions of
surfaces by hand. The feature instead is very useful for area sources,
simple fault sources and complex fault sources which are fully supported.

We fixed a small bug in the command `oq shakemap2gmfs` that was not
accepting fractional truncation levels, only integer ones.

We added a command `oq purge failed` to remove old calculations that
ended up in status 'failed'; it can be run periodically to save
disk space.

We added a command `oq workers debug` to test the correctness of
a cluster installation.

IT
--

There were a couple of major changes in the zmq distribution mechanism
in cluster environments. The first change was to move the task queue
to the worker nodes: as a consequence, calculations that before were
running out of memory on the master node now run without issues. The
second change was to implement a partial load balancing of the tasks,
resulting in huge improvements in calculations affected by slow tasks.

At user request, we added to the WebUI the ability
to specify a non-standard prefix path by setting the environment
variable WEBUI_PATHPREFIX. This is documented here:
https://github.com/gem/oq-engine/blob/engine-3.16/docker/README.md

We fully removed the celery support that has been deprecated for 5 years.

We removed support for Python <= 3.7 and added support for Python 3.10
on all platforms (Linux, Windows, macOS).

We added support for the geospatial library fiona on all platforms.

We produced RPM and debian packages, as well as an .exe installer
for Windows.

The universal installer has grown a `--venv` option so that you can
chose where to create the virtual environmente (the default is still
$HOME/openquake).

We revamped the docs site and now both the regular manual and the 
advanced manual are versioned (see https://docs.openquake.org/oq-engine/master/).

We now distribute a test calculation
https://downloads.openquake.org/jobs/performance.zip which can be used
to measure the performance of a server. It runs in ~30 minutes on a
recent MacBook with the M1 processor or a recent 18 core Xeon processor.
