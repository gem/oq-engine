Release notes for the OpenQuake Engine, version 3.1
===================================================

This release features several improvements to the engine calculators and
a few important bug fixes. Over 150 issues were closed. For the complete list
of changes, please see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.1/debian/changelog .
Here is a summary.

Bug fixes
-----------------------

We discovered a performance regression in engine 2.9 and 3.0. The
regression affects large hazard calculations and makes to compute the
statistics within the main calculation at best slow and at worse
impossible because of out-of-memory errors. If you have engine 2.9 and
3.0 you can still compute the statistics - even for large calculations -
but only in post-processing, i.e. with the `--hc` option.
This is not needed anymore and actually the calculation
within the main calculation is as fast as in postprocessing and much
faster than it was in engine 2.8 and previous versions.

The user [Parisa on the mailing list](https://groups.google.com/d/msg/openquake-users/oxbWg7lRgbI/xrxa9FhYCAAJ) discovered a regression in the GMF importer
from XML: it was not working anmores, unless a sites.csv file was specified.
This has been fixed. The XML importer is still deprecated, though, the
recommendation is to import GMFs in .csv format an with an explicit
sites.csv file.

Our Canadian users discovered a bug in the hazard curves computed from
nonparametric sources, causing the hazard curves to saturate at high
intensities. It turns out the source of the bug was a numeric rounding
issue that we fixed.

We discovered a subtle bug when reading ruptures from the datastore. Due
to numeric errors in the conversion from 64 bits to 32 bits in the geometries,
ruptures barely within the integration instance, could be read as outside the
integration distance, thus causing an error. This is a very rare case,
but it may happen, especially in calculation with millions of ruptures.

We discovered a subtle bug in event based risk calculations when storing
the GMFs and using vulnerability functions with PMF: the results were depending
on the order of the tasks storing the ground motion fields. This has been
fixed by speciying the order in which the GMFs are read (they are
read by event ID). In general this makes it easier to debug risk calculations
reading directly the GMFs from the datastore.

We discovered a subtle bug affecting calculations with sites and/or sources
crossing the international date line. The bug has been there for years.
In some cases, some sources could be incorrectly discarded, thus producing
a hazard lower than reality. The solution of this bug involved completely
discarding our old prefiltering mechanism.

Improvements to the prefiltering mechanism
------------------------------------------------

We began improving the source prefiltering mechanism in engine 3.0 and
we kept working on that. Now the prefiltering is performed in parallel
and it is so efficient that we can prefilter millions of sources in a
matter of minutes. Moreover the prefiltering is done only on the
controller node and not duplicated on the workers nodes.  The change
improved the performance of the calculators but also increased the
data transfer. So we changed the engine to make it able to read the
site collection directly from the datastore, thus saving GB of data
transfer. Due to the new approach is was possible to remove from the
classical calculator the tiling mechanism, which was very complex and
fragile, and still be faster than before. As a consequence, the data
transfer is lower than it ever was. Also, as a side effect of dropping
the old prefiltering mechanism, a very tricky bug
[over two year old has disappeared ](https://github.com/gem/oq-engine/issues/1965)

Improvements to the filtering mechanism
---------------------------------------------

While the prefiltering involves sources and it is performed before the
calculation starts, the filtering involves ruptures and is performed
while the calculation runs. The filtering works by computing a lots of
distances from each rupture to each hazard site and it can be slow.
In engine 3.1 we reworked completely the
filtering: now the default distance used for filtering is the
so-called `rrup` distance which is nothing else than the Euclidean
distance. Such distance can be computated with the
`scipy.spatial.distance.cdist` function which is extremely efficient: 
in some cases we measured speedups of over an order of magnitude with
respect to the previous approach.
The user can specify the distance used in the filtering by setting the
parameter `filter_distance` in the `job.ini` file. For instance
`filter_distance=rjb` would restore the Joyner-Boore distance that we
used in previous versions of the engine (actually not exactly the same
because now even the `rjb` distance is calling
`scipy.spatial.distance.cdist` internally).  Due to the changes both
to the default filter distance and to the low level function
to compute the distance, the numbers produced be engine 3.1 will be
slighly different from the numbers generated by previous versions.
The differences however are minor and actually the current approach is
more accurate than the previous one.
Also a refactoring of the site collection object made it faster the
computation of the distances not only for ruptures with complex
geometries but also for ruptures coming from point sources. The
net effect can be very significant if your computation was dominated
by distance calculations. This in practice happens if you have a single
GSIM. In complex calculations with dozens of GSIMs the dominating
factor is the time spent in the GSIM calculations and so you will not
see any significant speedup due to the improvements in the filtering
mechanism, even if you should still see some speedup to to the
prefiltering improvements.

Hazardlib
--------------------

A new GMPE was added, a version of the Yu et al. (2013) GMPE supporting Mw,
contributed by M. Pagani and Changlong Li.

This release involved a substantial refactoring of hazardlib, needed to
implement the improvements in the filtering and prefiltering procedures.

There were several changes to the [Surface classes](https://docs.openquake.org/oq-engine/3.1/openquake.hazardlib.geo.surface.html). In particular, now `PlanarSurfaces` do not require anymore the `rupture_mesh_spacing` to be instantiated
(it was not used anyway). Moreover the class hierarchy has been simplified
and one method have been removed. The [ContextMaker.make_contexts](https://groups.google.com/forum/#!forum/openquake-users) method now returns two
values instead of three, and ruptures now have more attributes that
they used to have. On the other hand, the attribute `.source_typology` was
removed from Rupture classes, since it was not used. A `.polygon` property
was added to each source class, to make the plotting of sources easier.

We fixed the serialization of griddedRuptures in the datastore.

The signature of [stochastic_event_set](https://docs.openquake.org/oq-engine/3.1/openquake.hazardlib.calc.html#module-openquake.hazardlib.calc.stochastic) was
slightly changed, by removing the redundant `sites` parameter. The API
of the [correlation module](https://docs.openquake.org/oq-engine/3.1/openquake.hazardlib.html#module-openquake.hazardlib.correlation) was slightly changed.

The most visibile change is in the
[Probability Mass Function module](https://docs.openquake.org/oq-engine/3.1/openquake.hazardlib.html#module-openquake.hazardlib.pmf).
In order to instantiate a PMF object a list of pairs (probability, object)
is required. The change is that before the probability had to be expressed
as a Python `Decimal` instance, while now a simple float can be used.
Before the sum of the probabilities was checked to be exactly equal to 1,
now it must be equal to 1 up to a tolerance of 1E-12. Since the Decimals
at the end were converted into floats anyway, it felt easier and more
honest to work with floats from the beginning.

It should be noticed that in spite of the major refactoring (over
1,000 lines of Python code were removed) the changes to client code
are next to non-existent: the HMTK was unaffected by the change and in
the SMTK only two lines had to big fixed. So the changes should not be
a problems for users of hazardlib. If you run into problem, please ask
on our [mailing list](https://groups.google.com/forum/#!forum/openquake-users).

Other Hazard
--------------

Reduced the data transfer in the UCERF calculators and fixed hanging
Stored ProbabilityMap.sids as an HDF5 dataset, not an attribute
Computing the hazard statistics appears to be ultra-slow
Reduced data transfer when computing the hazard statistics
Fixed the GmfGetter in a corner case with FarAwayRupture errors
Small changes to the hazard curves export (IMT in comment)

Added a PreClassical calculator

Renamed sitemesh-_xxx.csv -> sitemesh_xxx.csv
Added an XML exporter for the site model
Renamed 'fake' -> 'scenario' inside the realizations.csv output

Risk
-----

We fixed a long standing performance bug in scenario calculations. The
filtering of the sites according to the integration distance was done
too late. Now it is done *before* starting the calculation. If you
have 1 million sites with only 1 thousand within the integration
distance, then 990,000 sites are discarded up front. This makes it
convenient to run scenarios with large exposures because only the
sites and assets close to the rupture will be considered, even without
requiring the user to specify a `region` in the `job.ini` file.

We unified the `region` and `region_constraint` parameters of the `job.ini`.
Old calculations with a `region_constraint` will keep working, but you
will see a deprecation warning telling to replace `region_constraint`
with `region`. This is what the engine is doing internally.

We kept improving the risk exporters. In particular if the exposure has
tags (a concept introduced in engine 2.9) now the exported CSV files
(like averages losses and such) will contain the tag information.
This makes it possible to aggregate the outputs by tag.

The risk demos has been updated so that the exposures have tags.

We added two new scenario outputs `dmg_by_event` and `losses_by_event`
and we changed slightly the format of the `realizations` output.
Unified `losses_by_event` and `agg_loss_table`

The procedure associating the assets to the hazard sites, or associating
the site parameters to the hazard sites, or associating a shakemap to
an exposure has been refactored to use KDTree instead of rtree.
This means that the dependency on rtree is fully optional.

WebUI
-----------------------------------------------------

There was a bug with the groups in the WebUI, a features used only if
the authentication is enabled, which is not the default. Due to the bug,
users of a given group could not see calculations belonging to their
group, unless they were admin users. This has been fixed.

When a job dies abruptly, it status in the WebUI can remain
`is_running`.  Now restarting the WebUI or just the DbServer fixes the status
of jobs which are not really running. Also, now a job that did not
start because there were no live celery nodes is properly marked as
`failed`.

The input files used to perform a calculation are now automatically zipped,
saved in the datastore, and made accessible to the WebUI and the QGIS plugin.
This is very useful if you need to repeat a calculation performed by
another user on a different machine.

New checks and warnings
------------------------------

The engine always had a check between the provided GMPEs and the
GMF correlation model, since not all of the GMPEs supports correlation.
However, the check was done in the middle of the computation. Now the check
is done before starting the calculation, and the error message is more clear.

We added a warning in the case of a logic tree with more than 10,000
realizations, suggesting the user to sample it because otherwise the
calculation will likely run out of memory.

We earn the user when the source model contains duplicated source IDs,
suggesting to set the `optimize_same_id_sources` flag if the sources
are really duplicated (the ID could be duplicated without the sources being so).

For scenario calculations, we added a che that the number of realizations
must equal the number of distinct GMPEs.

Added a check against duplicated GSIMs in the logic tree.

We added an early theck on the Python version (>= 3.5).

oq commands
-----------

We added two new commands, which are useful in a cluster environment:

`oq celery status` prints the number of active tasks
`oq celery inspect` prints some information on the active tasks

We fixed a bug in `oq db get_executing_jobs`, which now returns only
the jobs which are actually running, by checking their PIDs. This required
fixing the engine that was not storing the PIDs.

We fixed the command `oq to_shapefile` by adding "YoungsCoppersmithMFD" and
"arbitraryMFD" to the list of supported magnitude-frequency distributions.

Internals
--------------
Inhibit multiple CTRL-C to give time Celery to revoke tasks enhancement
Removed most of the Python 2<->3 compatibility layer
More tests
Unskipped several tests on Darwin
Added threadpool distribution mechanism
Monitored the time spent in iter_ruptures
Turbo mode to run the hazard models fast in the engine

Integration with USGS shakemaps
---------------------------------

Engine 3.1 features a new experimental integration with USGS shakemaps.
Essentially, when running a scenario risk or scenario damage calculation,
you can specify in the `job.ini` the ID of an USGS shakemap. The engine
will automatically

- download the shakemap (the grid.xml and uncertainty.xml files)
- associate the GMFs from the shakemap to the exposure sites
- consider only the IMTs required by the risk model
- create a distribution of GMFs with the right standard deviation, i.e.
  the standard deviation provided by the shakemap
- perform the desired risk calculation, considering also the
  cross correlation effect for multiple IMTs.

The feature is highly experimented and provided only for the purpose of
beta testing by external users.

Packaging
----------

For the first time we provide packages for Ubuntu 18.04 (Bionic).
Old versions of Ubuntu (16.04 and 14.04) are still supported, and we
keep providing packages for Red Hat distribution, as well as installers
for Windows and macOS, docker containers, virtual machines and more.
We also updated our Python dependencies, in particular we included
numpy 1.14.2, scipy 1.0.1, h5py 2.8, shapely 1.6.4, rtree 0.8.3,
pyzmq-17.0.0, psutil-5.4.3 and Django 2.0.4.
