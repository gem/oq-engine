Release notes for the OpenQuake Engine, version 3.6
===================================================

This release features several major new features (including completely
revised disaggregation, automatic optimization of duplicated sources,
fast exposure importer and taxonomy mapping) and lots of improvements,
new checks and bug fixes. Nearly 200 pull requests were merged.
For the complete list of changes, see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.6/debian/changelog

Disaggregation
--------------

The most relevant development on the hazard side was the work on the
disaggregation calculator. We changed substantially the business
logic. While in previous versions of the engine we were disaggregating
for all possible realizations in order to compute disaggregation
statistics, in this version we gave up on statistics. Instead, we
disaggregate only for a specific realization. The realization can be
specified by the user with the `rlz_index` parameter in the job.ini
file, or it can be determined automatically by the engine as the
realization closest to the mean curve for the given disaggregation
site.

Moreover, now the disaggregation calculation works like a post-calculator
(i.e. with the ``--hc`` option) and it is able to reuse information
computed in its parent calculation: the net effect is that it is
always faster than the corresponding classical calculation while in
the past it was several times slower. We also fixed a couple of
performance bugs: there was a slow operation ``truncnorm.cdf``
in an inner loop and ruptures outside the integration distance
were not discarded.
Finally, we changed the file names of the disaggregation outputs.

For models with thousands of realizations, the disaggregation can easily be
thousands of times faster than before.

Classical PSHA calculator
-------------------------

The engine is now smart enough to recognize duplicated sources
appearing in different branches of the composite source model and to
avoid redundant computations. Because this optimization is always on, 
the flag `optimize_same_id_sources` has been removed, as it has now 
been rendered useless. There are several models in the
hazard mosaic with duplicates sources and the new optimization has a
significant impact on those. Moreover the demo `LogicTreeCase2ClassicalPSHA`
has become an order of magnitude faster than before thanks to the reduction
of the duplicated sources.

There was a big improvement in the computation of the statistical hazard
curves which now is not only faster, but uses a lot less memory than
before.
The trick was to consider one site at the time, instead of
a block of sites. As a consequence it is now possible to consider
tens of thousands of realizations for hundreds of thousands of sites
without requiring terabytes of RAM. Moreover the data transfer has been
reduced by storing some auxiliary information in the datastore and reading
it from the workers instead of transferring it via celery/rabbitmq.

There was a substantial change in the way the tasks are distributed for a 
classical calculation. The engine has acquired the ability to estimate the
runtime of each task and if the estimated time exceeds a `task_duration`
parameter, the engine is able to split the task in subtasks that run
in less than `task_duration` seconds. The user can set the `task_duration`
manually in the `job.ini`, or she can leave it empty; in that case the
engine will figure out a reasonable value for it.

The approach is not perfect since there are non-splittable sources, so
there is a minimum size for a given subtask and  sometimes subtasks taking
much longer that the `task_duration` parameter may still appear: however,
the new approach is a drastic improvement and the situation was never better
than it is now.

We added a check on sources with a suspiciously large spatial extent
(more than 5,000 km) so that a warning is printed. Usually this means
that there was a bug in the generation of the source model.

We added a check on sources with suspicious hypo-depths and nodal plane
distributions (i.e. distributions with duplicated values) since they
make the calculation slower.

In extra-large models saving some debugging information (eg. the number of sites
affected by each source) was exceedingly slow, so now the information is
stored only if there are fewer than 100,000 relevant sources.

Logic trees
-----------

There was a tricky bug with the `minimum_distance` feature
in presence of multiple GSIMs in a logic tree branchset. Now
each GSIMs keeps its own minimum distance; before they were all
getting the same minimum distance, causing wrong results to be computed.
Fortunaly the `minimum_distance` feature is rarely used (and only for
internal purposes) so the bug is minor. The feature is documented here:
https://github.com/gem/oq-engine/blob/engine-3.6/doc/adv-manual/special-features.rst#gmpe-logic-trees-with-minimum_distance

We implemented zero weights for intensity measure types that should be
discarded in the GSIM logic tree. You can see the relevant documentation here:
https://github.com/gem/oq-engine/blob/engine-3.6/doc/adv-manual/special-features.rst#gmpe-logic-trees-with-weighted-imts

We implemented risk logic trees, a.k.a. the *taxonomy mapping* feature.
The idea is that users can map the taxonomy strings in their exposure to one or
more vulnerability/fragility functions, with corresponding weights for each
function assignment, to take into account the epistemic uncertainty in the 
exposure ⟷ vulnerability domain. The feature is
documented here:
https://github.com/gem/oq-engine/blob/engine-3.6/doc/adv-manual/risk-features.rst

A big conceptual change (but with no impact on the user) was
the simplification of the source model logic tree XML file. Before it
was necessary to specify a `logicTreeBranchingLevel` node that was
not used internally, now that node is optional. Old
files will keep working, as long as the `logicTreeBranchingLevel`
contains only a single subnode. The case of multiple subnodes is now
correctly flagged as an error. Thanks to the change,
source model logic trees, gsim logic tree, and risk logic trees
are now stored in the same way internally.

Lastly, we fixed a bug in source model logic trees with the options
`applyToSources` and `applyToBranches` on; in some times a fake error
about the source not being in the source model - even if it actually was -
was raised.

Event based hazard
------------------

We introduced a parameter `max_sites_per_gmf` in the job.ini
(only for `event_based` calculations that are trying to store
ground motion fields), with a default of 65,536 sites. 
A user trying to run an `event_based` calculation that has
`ground_motion_fields = true`, with more than the number of
sites permitted by `max_sites_per_gmf` will now get an early 
validation error instead of running out of memory after 
several hours of calculations. The `max_sites_per_gmf` limit can 
be raised beyond the default of 65,536 sites, at the user's own
responsibility.

We also added a limit of ``2**32`` events in event based calculations: this is
a hard limit that cannot be raised. If your calculation produces more than
4 billion events, it will need to be be split into smaller calculations. 
Such calculations involving billions of ruptures would likely never work anyway, 
because it would eventually run out of memory.

We added a check for missing ``intensity_measure_types``: this avoids
cryptic errors in the middle of the computation of the ground motion fields.

We optimized the rupture sampling procedure for point sources (which
includes multi point sources and area sources). The improvement can be
quite significant, for instance the generation of ruptures for a large
multipoint source for Colombia became 30x faster using 12x less memory.

We changed the way ruptures are stored internally: the
`code` field in the `ruptures` dataset is now a unique checksum
depending on the kind of rupture. Before it was an incremental
number depending on the order of the Python module imports which
was making debugging difficult.

The rupture CSV exporter has been enhanced, and now it exports the rupture
surface boundaries as 3D multipolygons instead of 2D multipolygons.

We fixed a small bug in the rupture XML exporter, which was failing
if the user did not specify the hazard sites.

We added the ability to generate hazard curves without storing the GMFs,
simply by setting the flags
```
  hazard_curves_from_gmfs = true
  ground_motion_fields = false
```
This is useful when one is interested in the hazard curves generated
by an `event_based` calculation but not in the ground motion fields
themselves. Not storing the GMFs reduces the data transfer and the
memory occupation.

In engine 3.5 we changed the `gmf_data` CSV exporter to export a file
``sitemodel.csv`` instead of the file ``sitemesh.csv``. That change has
been reverted because it was generating confusion. The right way to
to export the site model information for the most recently completed 
calculation - which works for all calculators,
not only for event based -  is to use the command
``oq show sitecol > sitecol.csv``

Importing GMFs from CSV has been enhanced and now it does not require
anymore the field `rlzi`: previously, this was a required field, 
but it was assumed to contain always the value `0`. On the other hand, 
now the GMF exporter to CSV does not export the field `rlzi`, because 
it is redundant: the association between events and realizations can 
be found in the events table and it is exported in the 
file `sigma_epsilon.csv`.

In the `sigma_epsilon.csv` file, we renamed the field `eid` to
`event_id` in order to avoid confusion with the naming used in the
`gmf_data.csv` file (`event_id` is the 64 bit event ID in the `events`
table in the datastore, `eid` is the 32 bit index to the event ID
record).

Event based risk
----------------

There was a huge refactoring of all risk calculators. As a consequence
the `event_based_risk` calculator has become simpler and faster than before
(twice as fast in some cases).

In the `ebrisk` calculator it is now possible to aggregate by `asset_id`
and therefore to produce individual loss curves and maps for each asset.
Needless to mention, this is only viable for exposures of manageable size.

There was some work to make the ``losses_by_event`` exporter for the
``ebrisk`` calculator more similar to the ones for ``event_based_risk``
and for ``scenario_risk``.

We fixed a bug in the `agg_curves-rlzs` and `agg_curves-stats` outputs
in ``ebrisk``: they were missing the ``units`` compared to the same outputs
coming from the ``event_based_risk`` calculator. This was breaking the QGIS
plugin.

We changed the ``agglosses`` exporter in
``scenario_risk`` calculations, by adding a column with the realization index.

The `agg_curves` exporter for event based risk was broken if the exposure
was imported in the parent calculation and not in the child calculation.

We fixed a bug in the exporter of the aggregate loss curves coming
from an ``ebrisk`` calculation: now the loss ratios are computed
correctly even in presence of occupants. Before the exporter was
writing incorrect loss ratios to the output file.

Hazardlib
---------

Graeme Weatherill (@g-weatherill) contributed a finite rupture option to the
Germany-adjusted Cauzzi and Derras GMPEs. Moreover, he contributed
the Tromans et al. (2019) adjustable GMPE, used for a nuclear
power plant in the UK.

Chris van Houtte (@cvanhoutte) contributed the Van Houtte et al. (2018)
Significant duration model for New Zealand.

Robin Gee (@rcgee) fixed a bug in the  GMPE Sharma (2009): there was
a key error if the intensity measure level specified in the job.ini included
periods that required interpolation.

Marco Pagani (@mmpagani) discovered a bug in `calc_hazard_curves`
which was failing with a cryptic 
`AttributeError: 'NoneType' object has no attribute 'within_bbox'`
when used in parallel mode. It has been fixed.


Risk
----

The CSV importer for the exposure has been optimized. Before, for
legacy reasons, the importer was converting the CSV records into node
objects similar to the ones coming from the XML importer and then it
was reusing the XML logic. Now we are doing the opposite: the XML
importer is producing records and reusing the logic of the CSV
importer. Thanks to this change for large CSV exposure the new
importer is 4-5 times faster and uses over 10 times less memory than
before.

Since a long time ago the engine has the ability to reduce the hazard
site collection (which can be large, think of a fine grid) only to the
locations where there are assets. Such feature has been optimized in
this release, up to a spectacular extent in some cases: we measured a
speedup from 2h to 0.1s for Canada.

We changed how zipped exposures are managed by the engine. In version
3.5 a zipped exposure was expected to contain an XML file with the
same name of the archive, apart from the extension. Because of that
the `job.ini` file had to contain a line ``exposure_file =
<exposure_path>.xml`` while now it requires a line ``exposure_file =
<exposure_path>.zip``, which is clearer.  The change was requested by
the risk team in the context of the CRAVE project because it
simplifies the unzipping of the exposure. Unzipping will overwrite
files of the same name already present, but a warning will be printed
and the original files will be not lost, but renamed with a ``.bak``
extension.

We added a consistency check between statistics for calculations
leveraging the ``--hc`` option, because some users were making mistakes
like trying to compute means in the child calculation without having them
in the parent calculation. Now one gets a clear error message.

We fixed a bug in ``classical_damage`` from CSV with discrete
fragility functions: for hazard intensity measure levels different
from the fragility levels, the engine was giving incorrect results.

Vulnerability functions with the beta distribution must satisfy some
consistency requirements if the coefficients of variation are nonzero.
Unfortunately the consistency check were missing and it was possible
to accept invalid functions raising and error in the middle of the
computation. Now the error will be raised much early, at the time
of the instantiating the vulnerability functions. See #4841 for more
details.

Hyeuk Ryu (@dynaryu) discovered a bug in the `agg_loss-curves` outputs 
for the `event_based_risk` calculators, which has been fixed.

Finally there were some improvements to the ``multi_risk`` calculator in the
context of the CRAVE project. In particular now the engine is able
to manage the geometries of volcanic perils like lava, lahar and pyroclastic
flow and it is also able to manage other binary perils without requiring
the introduction of new intensity measure types.

General changes
---------------

The CSV exporters have been enhanced: now there is an additional line
before the header, starting with a ``#`` character, containing some
metadata, like the date when the file the generated, the version of
the engine that generated it, and some relevant parameters, like the
investigation time in the case of the hazard outputs. In the future
we may add even more metadata and extend the approach to other outputs.

Before release 3.3, the engine had the ability to associate site
model parameters to hazard sites on a grid. This feature was sometimes
buggy and removed, by recommending to the users the command `oq
prepare_site_model` instead. `oq prepare_site_model` is able to
produce a `site_model.csv` file with sites on the grid and it performs the
associations explicitly, once and for all.

In this release, we restored the ability to perform the association
directly in the engine. This is less efficient than using `oq
prepare_site_model`, since the same associations will be recomputed during
each run. It is still useful for people wanting to experiment with the
grid spacing: they can run several calculations and when they are
happy with the grid spacing, run `oq prepare_site_model` and fix the
site model once and for all with the preferred grid spacing.

We fixed a performance regression in the `ucerf_classical` calculator,
due to a change of logic in engine 3.5, which was trying to filter
thousands of sources in the controller node instead than in the
workers, thus becoming extra-slow.

We decided to change the `realizations.csv` output for scenario calculations,
by replacing the `branch_path` field with the GSIM representation. This is
more informative for the users and more convenient for the QGIS plugin too.

IT
--

The job queue first introduced in engine-3.5 is now enabled by default.
This means than only on job can run at a given time for a given engine
instance.

The progress report has been improved: before in large classical calculations
the progress started to be printed too late, even days after the start of
the calculation.

We improved the `oq abort` command to remove submitted jobs too.

Deleting a calculation in the engine has always been tricky in the case
of multiple users. In this release we fixed several issues and now an
user can delete all of her calculations with the command `oq reset`.
The engine will look inside the database and correctly remove the
calculations of the user, including all the relevant .hdf5 files.

We improved the `oq plot` command by adding several new kinds of plot.
They are still for internal use only (i.e. introspection and debugging).

We extended the command `oq db` to run generic queries for the
`openquake` user. Other users can only run ``SELECT`` queries.

There was a bug in `oq webui start` not supplying the `--noreload`
argument that has been fixed (the reload functionality of the Django
development server interferes with SIGCHLD and causes zombies).

We fixed another bug with the `--hc` functionality in a multi-user
situation, due to the fact that the engine was searching the the datastore
of the parent calculation in the wrong directory.

There is now a better error message if the shared directory is not mounted.

Source models can now be serialized in TOML format, which is useful for
debugging purposes.

Libraries and Python 3.7
------------------------

In this releases we updated some of our libraries (numpy from version
1.14 to 1.16 and scipy from version 1.0.1 to 1.3.0) to make it
possible to use the engine with Python 3.7. We actually have a cluster
using Python 3.7 in production.

In the future we may distribute installers for Windows and macOS based
on Python 3.7, but for the moment Python 3.6 is still the only
officially supported version and we not plan to abandon Python 3.6 any
time soon.

We raised the minimum version for h5py from 2.8.0 to 2.9.0, fixed
some compatibility issue with Django 2.1 and 2.2 and fixed several
Python 3.7 deprecation warnings.  Finally we removed the external
dependency from the mock module since it is included in the standard
library since Python 3.3.

Deprecations/removals
---------------------

For years the engine has been able to import ground motion fields and
hazard curves in CSV format and NRML format, with the NRML format
deprecated. Now finally the NRML importers have been removed.

There was an old deprecated GMF exporter in NRML format for scenario
calculations. It has been finally deprecated. You should use the CSV
exporter thas has been available for years instead.

We deprecated the XML disaggregation exporters in favor
of the CSV exporters.

We removed the long time deprecated `agg_loss_table` exporter since
now all the needed information is in the `losses_by_event` exporter.

We switched officially the testing framework from nosetests to pytest.
