Release notes for the OpenQuake Engine, version 2.9
===================================================

Several improvements entered in this release, most notably about the
event based calculator. Over 150 issues were closed. For the complete
list of changes, please see the changelog:
https://github.com/gem/oq-engine/blob/engine-2.9/debian/changelog .

Hazard
-----------

The problem of slow tasks has been an issue with the engine from the
very beginning. This release does not solve the problem, but features
the biggest improvement ever made. The task distribution has been
improved so much that we can afford to generate 40% fewer tasks
than in the previous release and yet have fewer slow tasks. 
This is very important in large scale computations, where data
transfer is an issue and producing fewer tasks improves the performance.

Moreover, we solved the issue of the engine not producing adequate tasks
in some situations, for instance classical PSHA calculations with few sites,
or event based hazard calculations with few sources. The "inadequate number of
tasks" issue meant wasting of computation power, i.e. not using all of the
available cores.

The improvement of the task distribution was made possible by refining 
the source weighting algorithm and by splitting the area sources before
the prefiltering, thus getting better upfront estimates of the
computational size of a task.

The prefiltering mechanism itself has been improved and we fixed a bug
affecting sites around the international date line: the prefiltering
with [rtree](http://toblerity.org/rtree/) was incorrectly discarding
relevant sources. The bug was introduced several releases ago and
discovered by our users from New Zealand.

We substantially reduced (in a SHARE calculation by a factor of 170!)
the data transfer when calculating hazard statistics in postprocessing.
Thanks to that, it is now possible to compute mean/max/quantile hazard
curves in calculations as large as the 5th Generation Seismic Hazard Model 
of Canada (SHMC) (with over 200,000 sites and 13,122 realizations).

We fixed a few bugs in the disaggregation calculator breaking some corner cases
and we paved the way for implementing disaggregation by source.

We improved the support for nonparametric sources with gridded
surfaces, a feature introduced several releases ago. Now nonparametric
sources can be split properly, thus producing a good task distribution
and they can be used in a disaggregation calculation. The support is
still not complete, for instance you cannot export ruptures with gridded
surfaces, but we are working on it.

We introduced a minimum distance concept for Ground Motion Prediction
Equations. The GMPEs have a range of validity, and you cannot trust
them on sites too close to the seismic source. By specifying the
minimum distance it is possible to cut off the value of the generated
ground motion field: for sites below the minimum distance the GMF is
cut off at the maximum value. It is possible to specify a minimum
distance (in km) for each GSIM by updating the gsim logic tree file. Here is
an example of how it would look like:

```xml
              <logicTreeBranch branchID="b1">
                <uncertaintyModel minimum_distance="10">
                  LinLee2008SSlab
                </uncertaintyModel>
                <uncertaintyWeight>0.60</uncertaintyWeight>
              </logicTreeBranch>
                
              <logicTreeBranch branchID="b2">
                <uncertaintyModel minimum_distance="5">
                  YoungsEtAl1997SSlab
                </uncertaintyModel>
                <uncertaintyWeight>0.40</uncertaintyWeight>
              </logicTreeBranch>
```

Hazardlib/HMTK
---------------

[Graeme Weatherill](https://github.com/g-weatherill) contributed the GMPEs of 
[Bommer et al. (2009) and Afshari & Stewart (2016)](
https://github.com/gem/oq-engine/pull/3379)
as well as a [fix to the ASK14 GMPE](https://github.com/gem/oq-engine/pull/3316),
which was failing in the case of small magnitudes (< 4.4) and long periods
(> 5). The fix is the same used by the original authors of the GMPE.

Graeme also contributed a comprehensive suite of 
[NGA East ground motion models](https://github.com/gem/oq-engine/pull/3130)
for central and eastern United States.

There is a small fix for the Derras 2014 GMPR, for distances below 0.1 km.

We added the [Yu et al. (2013) GMPEs](
https://github.com/gem/oq-engine/pull/3428) for China
together with Changlong Li.

The visualization capabilities of the Hazard Modeller Toolkit (HMTK) have
been enhanced thanks to a contribution by Nick Ackerley.

We changed the ordering of the IMTs in hazardlib: before it was purely
lexicographic, now it is lexicographic for non-SA IMTs, while SA IMTs
are ordered according to their period, as requested by Mike Hearne of USGS.

The hazardlib classes `FilteredSiteCollection` and `SiteCollection` have
been unified. This should not affect users, except people calling the
internals of the SiteCollection class.

Risk
-----

The biggest improvement on the risk side is in the event based
calculator, which is now able to use precomputed ground motion fields,
a feature that before was available only in the experimental
`gmf_ebrisk` calculator. The net effect is a huge improvement in the
performance of the calculator, so much that now the suggested strategy
to run large event based risk calculation is to precompute the ground
motion fields, provided you have enough disk space. There were also a
few fixes, in particular in the management of the epsilons, now controlled
by the `master_seed` parameter in all situations, and in the
generation of the aggregate loss curves, which is now a lot faster.

It is now possible to read the ruptures directly from the
workers without sending them through the wire. This is relevant for
large calculations producing millions of events, since it reduces
substantially the data transfer. Also, the way the ruptures are stored
in the datastore has been optimized. The consequence is that you
cannot read ruptures stored with engine 2.8 with engine 2.9.

On the other hand, hazard curves, hazard maps, and uniform hazard
spectra produced with older versions of the engine are still readable
by this version of the engine and are viewable by the latest QGIS
plugin. We will make any effort to maintain this feature even in
future releases.

The other big improvement on the risk side was the support for CSV
exposures. The support is not complete yet, and we are not supporting all
the features of XML exposures, however we already support the most
common cases. The performance is of course better than for XML and we
were able to import 3 million assets for an exposure in California in just 4
minutes. We had to change the internal storage of the exposure to work
around a bug in h5py/HDF5 making it impossible to store such large
exposures. We are now able to run full risk calculations for exposures of this
size in a couple of hours on a workstation, a feat previously impossible.

We fixed a bug in vulnerability functions with PMFs: the random seed
for the sampling method of the discrete probability distribution was
set uncorrectly and in some cases the same value of the loss ratio
could be sampled multiple times.

We improved the display names for the risk outputs, i.e. the names of
the outputs as seen from the engine, the WebUI, and the QGIS plugin.

WebAPI/WebUI/QGIS plugin
-----------------------------------------------------

We enhanced significantly the `/extract/` web API, allowing more data
to be extracted from the datastore in a proper way, "proper" meaning
future proofed against changes in the internal structure of the datastore.

The `/extract/` API is based on an underlying `extract` Python API, that
can be used directly in scripts, with the same guarantees of portability
across engine versions.

There is now an `abort` WebAPI and an `abort` button in the WebUI and
QGIS plugin, using which it is possible to cleanly kill a running
calculation.

We fixed a small issue: now when the WebUI is stopped all calculations
started by it are automatically killed.

The integration between the plugin and the web tools (in particular
the Input Preparation Toolkit) has been improved as well; for the new
features of the plugin please read its release notes.

Bug fixes/additional checks
------------------------------

We fixed a minor bug with the .npz exports: the command
`oq engine --run job.ini --exports npz` now works as expected.

We raise a clear error when the parameter `risk_investigation_time`
is missing in the `job_risk.ini` file.

There is a better error message when the user wants to compute
loss maps and the parameter `asset_loss_table` is missing.

There is a clear warning when the engine produces no output, usually
because `mean_hazard_curves` is set to `false`. Also, in that case, no
output rows are incorrectly added to the database.

There is a check on the path names used in the source model logic
tree file: they must be relative paths, not absolute paths, to make it
possible to port the input files across different machines and operating
systems.

There is a check on calculations starting from precomputed hazard results: if
job.ini file contains a site model or logic tree files, the user is warned
that they will not used for the subsequent calculation and should be removed.

We improved the error message in the case of source models in format
nrml/0.4 uncorrectly marked as nrml/0.5.

The CSV rupture exporter now also exports the parameter
`ses_per_logic_tree_path` in the header of the CSV file.

A lot of work went into the .rst reports which are now more reliable than
ever.

oq commands
-----------

There is a new command `oq shell` that starts an IPython shell (or Python
shell, if IPython is not available) in the engine virtual environment.
This is very useful to explore interactively the results of a computation.

There is a new command `oq abort <job_id>` that allows to kill
properly running calculations.

The command `oq engine
--delete-calculation <job_id>` has been extended to abort running calculations
before removing them from the database and the file system.

The command `oq zip` has been extended and now works for all kind of
calculations.

The command `oq extract` has now a signature consistent with `oq export`
and has grown the ability to connect to a remote engine server.

The `oq dump` command has been extended so that it is possible to extract
a single calculation, if so desired.

IT
---

We have specialized packages for clusters even for Ubuntu. The
packages meant for the controller node includes rabbitmq and celery,
which are missing in the packages meant for the worker
nodes. Previously, we were installing rabbitmq and celery even when
not needed.

Docker containers can be used to deploy a multi-node installation of
the Engine on a Docker cluster with dynamic scaling.

It is possible to specify a `custom_tmp` variable in the openquake.cfg file
to configure a custom path for the temporary directory. This is useful in
situations when the system /tmp directory is in a partition which is
too small (this happened to users with a machine in the Azure cloud).

The version of numpy officially supported by the engine is 1.11 however
we made some work to ensure that the tests run also with the most recent
versions. In the near future we will probably migrate to numpy 1.14.

Since we added a field with the process ID in the job table in order to
implement the abort functionality, upgrading to engine 2.9 requires a
database migration if you have an older version of the engine and you want
to keep your old calculations. You will just need to say yes the first time you
run a calculation, when the engine will ask you to upgrade the database.
The migration is immediate and safe.

Deprecations/removals
---------------------

Since the GMF-reading feature has been incorporated into
the core `event_based_risk` calculator, the experimental `gmf_ebrisk`
calculator is gone.

Reading the GMFs from a NRML file has been deprecated. The suggested
approach is to use the CSV format, as documented in the manual.

The obsolete hazard GeoJSON exporters, deprecated months ago,
have been removed. The right way to convert hazard outputs
into geospatial data is to use the QGIS plugin.

We deprecated the function `openquake.hazardlib.nrml.parse`, now superseded
by the function `openquake.hazardlib.nrml.to_python`. This is of interest
only to people using `hazardlib` from Python.

The ability to run two .ini files together (with the command
`oq engine --run job_h.ini,job_r.ini`) has been removed, since it could
produce issues in some cases and was never documented anyway.

Python 3 migration
------------------

All the installers provided by GEM (for Linux, Windows, macOS), all
the virtual machines, all the Linux packages (CentOS, Ubuntu) and the
docker containers are now based on Python 3.5. All use of Python 2.7 has been
discontinued internally at GEM. You can still install the engine 
manually with Python 2.7 and it will work, but this is the last
version to guarantee compatibility with Python 2. Starting with the
next version (3.0) the engine will require at least Python 3.5 to
work. The change has no effect on people using the engine as a tool
since the right version of Python is already included in our installers/packages,
but power users developing their own tools/libraries based on the
engine will have to migrate their scripts to Python 3. If your scripts
do not import engine libraries directly but they only perform calls to
the WebAPI they will keep working of course. This is why the QGIS
plugin is still working with engine, even if the plugin itself is
using Python 2.7.
