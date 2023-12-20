Release notes v3.14
===================

The release 3.14 is the result of 3 months of work involving nearly
200 pull requests. The major highlight is the complete vectorization of
hazardlib.

The complete list of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.14/debian/changelog

## Work on hazardlib

One year ago we started a vectorization program for the GMPEs in hazardlib,
described here:

https://github.com/gem/oq-engine/blob/engine-3.14/doc/breaking-hazardlib.md

As of engine 3.14 all of the ~700 GMPEs in hazardlib are vectorized,
i.e. they use the new API in terms of numpy arrays and not Python
objects. The new and better way to work with GMPEs is documented here:

https://docs.openquake.org/oq-engine/advanced/developing.html#working-with-gmpes-directly-the-contextmaker

As a consequence of the vectorization, classical calculations can be
much faster than before (of the order of 2-10 times faster)
in the case of few sites. Models with GMPEs based on HDF5 tables -
like the Canada and USA models - have been specially optimized, so
that you can have significant speedups - in the order of 3-5 times for
the Canada 2015 model - even in the many-sites case.

There was also a substantial amount of work for collapsing
the context objects, even for nonparametric sources: that
will give significant speedups in future versions of the engine.

Also, numba is used in a few more hotspots, giving significant speedups
in some classical calculations.

There were some improvements to `KiteSurfaces` and to
`MultiFaultSources`. In particular the performance of
MultiFaultSources in the engine was disastrous: all the time was
spent in computing the bounding box and the encircling polygon. This is
now fixed.

The magnitudes in multiFaultSources have been rounded to two digits
after the decimal point.

We added a check on `geo.Line` forbidden degenerate lines with less than
two points.

We extended the ModifiableGMPE to work with GMPETable subclasses,
with  the NRCan15 site term and with the Al Atik Sigma model.

We introduced the concept of computed rupture parameters, which was used to
vectorize the McVerry GMPEs.

Prajacta Jadhav and Dharma Wijewickreme contributed the GMPE Youd et
al. (2002) and the corresponding site parameters.

Tom Son contributed a few bug fixes to the GMPE Kuehn et al. (2020).

Finally, we raise an error when the total standard deviation is zero and the
truncation level is not zero (currently this may happen only with the 
GMPE YenierAtkinson2015BSSA).

## New hazard features

The UCERF calculator has been removed. Now you can run an UCERF
calculation by using the regular classical calculator, provided you
have the UCERF model in a new format using multiFaultSources. The new
format has substantial advantages, for instance it is possible to
combine the UCERF model with other models.

We implemented a cache for the distances that speedups
substantially the calculation (we are talking about a 2x
speedup). Since the distance calculation algorithm has changed
internally, the numbers are expected to be slightly different than
in past versions.

At user request, it is now possible to disaggregate by all realizations
by setting in the job.ini file

`num_rlzs_disagg = 0`

Naturally, if you have a large number of realizations that can cause
your calculation to run out of memory or to become extra-slow. Use
this feature with care.

## New risk features

At user request, we implemented [multi-tag
aggregation](https://github.com/gem/oq-engine/issues/7663): it is now
possible to aggregate across different tag combinations within a
single calculation. The exporters have been changed accordingly to
export a file for each tag combination.  For instance setting in the
job.ini something like

`aggregate_by = NAME_1, taxonomy; NAME_1; taxonomy`

would perform four different kinds of aggregations (by "NAME_1 &
taxonomy", by "NAME_1", by "taxonomy" and total aggregation) and the
aggregate risk and aggregate curves exporters would export four files
each. The export format is the same, however while before the totals
were exported in the same file, now they are exported in a separate
file.

We also changed how the [Aggregate Risk
output](https://github.com/gem/oq-engine/pull/7708) is computed,
reverting back to the definition of previous versions of the engine,
directly related to the average annual losses.

## Bug fixes

We discovered a bug in the check on unique section IDs for
multiFaultSources, such that non-unique sections IDs were
possible. Also, section IDs were incorrectly recognized as source
IDs. Both issues are now fixed.

`job.ini` files containing a Byte Order Mark (BOM) where not read
correctly, causing issues particularly on the Windows platform.

There was a small bug with discard_trts, such that in some cases too many
TRTs were discarded. This is now fixed.

Some `event_based_damage` calculations could fail in a cluster environment
due to the `parent_dir` parameter being passed incorrectly.

The web API /v1/calc/run was failing when uploading files due to a
sorting issue.

We changed the web API `/extract/events` to return events sorted by ID:
this avoids an error with the QGIS plugin when visualizing GMFs.

There was an error in the aggrisk exporter not considering the realizations
generating zero losses and therefore computing incorrectly the means.

There was a bug when exporting Asset Loss Maps in some situations, due
to a 32 bit/64 bit mismatch in the `conditional_loss_ratio` parameter.

We improved the error checking for calculations with site amplification.

We fixed the `--hc` feature that was failing when starting from a
preclassical calculation.

## oq commands

We removed the obsolete commands `oq to_shapefile` and `oq from_shapefile`
and the explicit dependency from pyshp.

We changed `oq zip <directory>` to generate a single big archive instead
of an archive for each job.ini.

We extended `oq postzip` to post multiple files at once.

We extended `oq reduce_sm` to work with multiFaultSources.

We made `oq engine --multi --run` more robust against out-of-memory errors.

## IT changes

The support for Python 3.6, deprecated in version 3.13, has been
removed. The engine should still work with it but we do not test Python 3.6
anymore and can stop working at any moment without warnings.
On the other hand, Python 3.9 is now officially supported.

We upgraded Shapely to version 1.8.0. This is a big change, since
the new version is incompatible with the past and produces different
numbers: as a consequence the engine produces slightly different
results than in previous versions.

We updated Django to release 3.2.12 to avoid security bugs.

We changed some internals to make it easier to run the engine in
cluster environments with a shared database.

We made it possible to set a default `pointsource_distance` in
the global configuration file `openquake.cfg`.

Finally the install.py script has been improved:

- the server installation correctly installs the systemctl files both on
  Debian-based and RedHat-based distributions.

- we added a missing `[directory]` section in the `openquake.cfg` file
  generated by install.py.

- we now raise a helpful error message when ensurepip is missing.

## Other

The classical calculator now stores unique rupture IDs in the `rup` DataFrame.
There are some limitations, and in particular you cannot expect the same
calculation on different machine to produce the same IDs unless you fix
the parameter `concurrent_tasks` too.

We removed the `applyToSourceType` functionality of the logic tree, since it
was not used and broken anyway.

We raised the limit to 94 GMPEs per tectonic region type and 94
branches per source model logic tree.

In the ruptures dataset for event based calculations we now store the
occurrence rate multiplied by the source model weight, to simplify some
consistency checks.

Finally, as usual, we worked at improving the documentation.
