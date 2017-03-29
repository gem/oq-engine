Release notes for the OpenQuake Engine, version 2.3
===================================================

This release introduces several new features and improvements of the
engine calculators. Moreover, our packaging strategy has been
revolutionized and now we provide packages for [most operating
systems](faq.md#supported-operating-systems) - including previously
abandoned systems such as Ubuntu 12.04 - by using the exact same
versions of the libraries on every supported platform (Linux, Windows, Mac).

More than 20 pull requests were closed in oq-hazardlib and more than
70 pull requests were closed in oq-engine. For the complete list of
changes, please see the changelogs:
https://github.com/gem/oq-hazardlib/blob/engine-2.3/debian/changelog
and https://github.com/gem/oq-engine/blob/engine-2.3/debian/changelog.

A summary follows.

New features in the engine
--------------------------

From this release it is possible to take into account the *topography
of the region of interest*. It is enough to write the elevation of the
hazard sites in the sites file or in the site model file, as a
negative depth, and the engine will compute the ground shaking
correctly. Before there was no way to specify the elevation of the hazard sites
and the ground shaking was computed only at the sea level.

From this release it is also possible to use *magnitude-dependent
integration distances*. This is expected to have a substantial impact on the
calculation time, since small magnitude ruptures will affects a lot
less sites than before. In order to use the feature the user has to
specify in the `job.ini` file a list of pairs (magnitude, distance) for each
tectonic region type. In the past the user would write

`maximum_distance = {'Active Shallow Crust': 200}`

and the engine would use an integration distance of 200 km for all
ruptures of the given tectonic region type, disregarding the magnitude.
Now, the user can write

`maximum_distance = {'Active Shallow Crust': [(8, 200), (7, 100), (5, 20)]}`

and the engine will use an integration distance of 200 km for ruptures
of magnitude 8, of 100 km for ruptures of magnitude 7, and of 20 km
for ruptures of magnitude 5. Intermediate magnitudes will use a
linearly interpolated distance. It is up to the user to provide a
sound magnitude-distance function. For the future, we plan to release
tools to help the users in the task of inferring magnitude-distance functions.
If in doubt, you can always use the old syntax, equivalent to a
constant maximum distance for all magnitudes, and the engine will keep
working as in the past.

A lot of work went into the UCERF calculators, but they are still officially
marked as experimental and are left undocumented on purpose. There is a
new time-dependent classical calculator, while the old calculators were
substantially improved.

There is an experimental command `run_tiles` to split a `sites.csv`
file in tiles and run multiple calculations at once. This is meant for
power users only.

There is a new command `oq reset` that will remove all calculations of
the current user from the database and the filesystem. It is meant for
cleaning up a testing machine were there are no important calculations.
Use it with care.

New features in hazardlib
--------------------------

New GMPEs - site adjusted Pezeshk et al. 2011, plus a few modified GMPEs
for Armenia - were added.

The new `GriddedSurface` object introduced in engine 2.2 can now be
serialized in the NRML 0.5 format properly.

The calculator `calc_hazard_curves` now supports mutually exclusive
sources and ruptures too.

Performance improvements
------------------------

The calculation of ground motion fields is a lot faster than before in
situations with a large amount of hazard sites. The reason is that now
the distances are computed in the workers, whereas before they were
computed in the controller node. This has a significant impact on
users with a cluster.

Changes
------------

There are two new limits in the event based calculators:

1. it is impossible to run calculations with more than 65536 tasks
2. it is impossible to have tasks generating more than 65536 events each

These limits have been added to prevent users from running impossibly
large calculations: an error message will be displayed early rather
than causing machines to crash.

The event loss table exporter is now faster than in
release 2.2. It does not export the tectonic region type string
anymore, however you can infer it from the `event_tag` field which
contains the source group ID. The association between the source group
ID and the tectonic region type is contained in the new export
`sourcegroups.csv`.  The `source_id` has been stripped from the `event
tag` since it was taking a lot of memory in the case of extra-large
calculations (UCERF).

The calculation of quantiles hazard curves used different algorithms
in the case of logic tree full enumeration and logic tree sampling.
For the sake of consistency, we now use always the same algorithm, the
one of full enumeration. This change may produce small differences in
the quantile curves if you were doing computations with sampling of
the logic tree.

The separator for the exported file `ruptures.csv` has changed from comma
to tab, since this file now contains MULTIPOLYGON geometries containing commas.

We do not compute the mean anymore if there is a single realization, even
if the user has set `mean_hazard_curves=true`.

We changed the DbServer port from port 1999 to port 1908. The
reason is that some anti-viruses were blocking port 1999.

Fixes to the Web UI
-------------------

The "Remove" button now actually removes the calculation. Before
it was only hiding it from the Web UI. Be careful with it, since it is
final. If you remove a calculation, the only way to restore it is
to repeat the computation.

We fixed the names of the files downloaded from the Web UI.  The names
of files downloaded from the Web UI previously contained slash ('/')
characters that were then replaced with dashes or underscores by the
browser. We no longer include slash characters in file names.

The named of the zipped outputs contained a spurious ".". This has been
fixed.

Other
------

We removed a warning about missing the `rtree` library that was too noisy.

A bug in the logic tree storage was fixed. Now it possible to run a
computation on a machine, copy the datastore on a different machine
and to export the results from there.

The was a bug in scenario_risk calculations in the case of exposures
featuring multiple assets of the same taxonomy on the same point
without insured losses. This is now fixed.

There was a bug when combining hazard curves happening in rare situations,
when a source group was generating probabilities of exceedence all zeros.
This has been fixed.

Configuration files with empty `conditional_loss_poes` and non-empty
`loss_ratios` were giving an ugly error message at export
time. Now the non-existing loss maps are simply not exported.

The parallelization library is now more robust against unexpected
exceptions.

Calculations in which a single task is generated are now executed in core,
i.e. no subprocess is spawned.

As usual the internal representation of several data structures has
changed in the datastore. In particular, we removed several usages of
variable-length strings, since they were buggy in the case of large
arrays. As always, users should not rely on the stability of the
internal datastore formats.

UCERF calculations (and more generally any calculations requiring a
shared directory) now work even on clusters without a shared
directory: they will only use the controller node, but at least they
will not fail.

The header of the exported losses for scenario calculations with
occupants was the ugly string `occupants:float32`: now it is just
`occupants`.

The command `oq engine --make-html-report` now works with Python 3 too.

The commands `oq info` and `oq info --report` have been fixed and improved; in
particular, now the report contains the correct number of effective ruptures
(i.e. ruptures within the integration distance) even for classical
calculations.

The `openquake.cfg` file is included in the installation, so users that
installed the engine via `pip install openquake.engine` will not get
any complain about the missing configuration file.

The repository with the latex manual has been merged into the oq-engine
repository, to help reducing disalignement between the code and the
documentation.

We fixed an issue with rabbitmq on Ubuntu 16.04 by updating our configuration
file `openquake.cfg` to not use the `guest` account.
