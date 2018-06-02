Release notes for the OpenQuake Engine, version 3.1
===================================================


Over 150 issues were closed. For the complete list of changes, please
see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.1/debian/changelog .

Improvements to the prefiltering mechanism
------------------------------------------------

This release continues the improvements to the source prefiltering
mechanism that started in engine 3.0. As of now, the prefiltering
is performed in parallel and it is so efficient that we can prefilter
millions of sources in a matter of minutes. Moreover now the prefiltering
is done on the controller node only and not duplicated on the workers
nodes. Due to the new approach is was possible to remove the engine
the tiling and still be faster than before.
Also, as a benefic side effect of dropping the old prefiltering mechanism,
at least a very tricky bug over [two year old has disappeared
](https://github.com/gem/oq-engine/issues/1965)

Improvements to the filtering mechanism
---------------------------------------------

While the prefiltering involves sources and it is performed before the
calculation starts, the filtering involves ruptures and is performed
while the calculation runs. The filtering works by computing a lots of
distances from each rupture to each hazard site and it can be slow in
some circumstances. In engine 3.1 we reworked completely the
filtering: now the default distance used for filtering is the
so-called `rrup` distance which is nothing else than the Euclidean
distance, now computated with the `scipy.spatial.distance.cdist`
function which is extremely efficient (in some cases we measured
speedups of over an order of magnitude than the previous approach).
The user can specify the distance used in the filtering by setting the
parameter `filter_distance` in the job.ini. For instance
`filter_distance=rjb` would restore the Joyner-Boore distance that we
used in previous versions of the engine (actually not exactly the same
because now even the `rjb` distance is calling
`scipy.spatial.distance.cdist` internally).  Due to the changes both
to the default filtering distance and to the low level function used
to compute the distance, the numbers produced be engine 3.1 will be
slighly different than in the past. The differences however are minor
and actually the current approach is more accurate than the previous
one.
Use a shorter site collection


Improvements to the data transfer
=================================


In large hazard computations, with hundreds of thousands of sites,
the data transfer was dominated by the site collection object.
Now the engine is able to read the site collection directly
from the datastore, thus saving GB of data transfer.
Refactored the SiteCollection in make_context.

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
Warn the user about optimize_same_id_sources when it looks like he should do that

Hazardlib/HMTK/SMTK
--------------------

Remove the usage of Decimal in hazardlib PMF.

If there are no fault ruptures, there is no need to specify the rupture_mesh_spacing

Added a .serial attribute to the hazardlib ruptures

Simplified the surface classes hierarchy enhancement internal

Removed the mesh_spacing from PlanarSurfaces

20180528 yu et al

Add a polygon property for each source and store it

Removed the .source_typology attribute from the ruptures

Changed the signature of `stochastic_event_set`

Small changes to hazardlib.correlation to support the SMTK

Risk
-----

Performance surprise in ScenarioDamage
Exported the tags in the risk outputs
The risk demos has been updated: now the exposures have tags
Removed any reference to `region_constraint`
Unified `losses_by_event` and `agg_loss_table`

Importing the GMFs from an XML file is broken
Added `dmg_by_event` and `losses_by_event` outputs


WebAPI/WebUI/QGIS plugin
-----------------------------------------------------

Fix groups members filtering

Bug fixes/additional checks
------------------------------

Fixed the latest IDL bug
Added an early check on the GMF correlation model

Added a check on duplicated GSIMs in the logic tree
Check on the Python version

oq commands
-----------

oq celery status
oq celery inspect
Create shapefile for sources with different mfds
Add a db command to show executing jobs

Internals
--------------

Stored the zipped input files

Inhibit multiple CTRL-C to give time Celery to revoke tasks enhancement
Removed most of the Python 2<->3 compatibility layer
More tests
Unskipped several tests on Darwin
Added threadpool distribution mechanism
Turned rtree into an optional dependence again
Replaced Rtree with KDtree when it is easy
Monitored the time spent in iter_ruptures

Support for the Aristotle project
---------------------------------

Added a `cross_correlation` parameter used when working with shakemaps


Packaging
----------

Upgrading Python dependencies.
Added support for Ubuntu 18.04 Bionic

Deprecations/removals
---------------------

Now even hazardlib and the Hazard Modeller Toolkit do not work anymore with
Python 2, as promised.

As usual, exporting the results of a calculation executed with a previous
version of the engine is not supported, except for hazard curves/maps/spectra.
We recommend first to export all of the results you need and then
to upgrade to the latest version of the engine.
