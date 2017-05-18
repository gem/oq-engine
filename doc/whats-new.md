Release notes for the OpenQuake Engine, version 2.4
===================================================

This release introduces several changes and improvements to the
engine calculators, most notably in the postprocessing of
hazard curves in classical PSHA calculations and in the postprocessing of
loss curves in event based risk calculations. Also, both hazard and
risk exporters have been revised and extended. Several bugs have
been fixed and several optimizations added.

More than 40 pull requests were closed in oq-hazardlib and more than
200 pull requests were closed in oq-engine. For the complete list of
changes, please see the changelogs:
https://github.com/gem/oq-hazardlib/blob/engine-2.4/debian/changelog
and https://github.com/gem/oq-engine/blob/engine-2.4/debian/changelog.

We have also decided a plan for
[dropping support to Python 2](dropping-python-2.md). We will abandon that
platform in the course of the year 2018. Precise dates have not been
fixed (on purpose) but everybody who is using hazardlib and/or the
engine as a library has to think about migrating to Python 3. Please
contact us if this is a problem for you: we are keen to provide
advice for the migration.

New features in the engine
--------------------------
 
There are several new outputs/exporters.
 
- There are new .csv exporters for the losses aggregated by taxonomy which are
  computed by the calculators `scenario_risk`, `event_based_risk` and
  `ucerf_risk`.
- There is a new output and a new .hdf5 exporter for the `asset_loss_table`,
  i.e. the full table of losses for each asset. This is an optional output of
  the `event_based_risk` calculator, generated when you set the flag
  `asset_loss_table=true` in the `job.ini` configuration file.
- There is an equivalent output for the `scenario_risk` calculator, called
  `all_losses-rlzs`, an an `.npz` exporter for it. This is also an optional
  output generated when you set `asset_loss_table=true`.
- There is a new output `losses by event` produced by the `scenario_risk`
  calculator, which is similar to the event loss table in the event based
  calculator: it contains the aggregate losses for each seismic event.
  There is a also new CSV exporter for it.
- There two new .npz exporters for the loss maps and the losses by asset
  outputs.
- There is a new CSV exporter for the Benefit-Cost-Ratio calculator.
- There is a new experimental CSV exporter for the ground motion fields
  produced by the event based calculator.
- The XML exporter for the output `ruptures` now contains only the
  ruptures, without any duplication, and for each event set the list of
  event IDs associated to the rupture. Before there was a rupture for
  each seismic event, with potential duplications.

It is now possible to split a source model in several files and read
them as if they were a single file. Just specify the file names in the
source_model_logic_tree file. For instance, you could split by
tectonic region and have something like this:

```
 <logicTreeBranch branchID="b1">
   <uncertaintyModel>
     active_shallow_sources.xml
     stable_shallow_sources.xml
   </uncertaintyModel>
   <uncertaintyWeight>
     1.0
   </uncertaintyWeight>
 </logicTreeBranch>
```

The parallelization library has been improved; now the `task_info` and
`job_info` datasets are automatically stored at the end of a calculation.

There is a new configuration parameter `max_hazard_curves` in the
`job.ini` file, which by default is `False`. This parameter controls
the generation of the maximum hazard curves, a new feature.

There is a new configuration parameter `max_site_model_distance` in the
`job.ini` file, with a default 5 km: before it was hard-coded. This parameter
controls the warnings for site model parameters which are far away from
the hazard sites.

Introduced a `ses_seed` parameter in the `job.ini`

Optimizations
------------------------

The *postprocessing of hazard curves* has been substantially improved:
now it uses orders of magnitude less memory than before and it is
extremely efficient. For instance in our cluster we were able to
compute mean and max hazard curves in a calculation for a Canada
model with 206,366 sites, 129 hazard levels and 13,122 realizations in
11 minutes, by spawning ~3,500 tasks and using ~500 GB of memory among
four machines. This is orders of magnitude better than everything we
ever managed to run before. Technically this has been achieved by
having the workers reading the data directly instead than passing them
via the celery/rabbitmq combo, thus improving the scalability of the
engine very significantly.

A similar approach has been used in the event based risk calculator.
Now the loss curves and maps are produced in postprocessing by
*reading directly the asset loss table*. As a consequence the
postprocessing is a lot more scalable than before. We can easily
compute millions of loss maps.

While loss maps are stored as before, *loss curves have become a dynamic
output*, generated at runtime from the loss ratios (this is the same
approach used for the hazard curves, generated at runtime from the
ProbabilityMaps). This saves a huge amount of disk space. As a consequence
of the change the engine does not show the loss curves anymore; however
they still can be exported, but with a new command:

```
$ oq export loss_curves/rlz-XXX
```

There is a huge improvement in the *storage of the hazard curves*:
the [individual hazard curves are not stored anymore]
(http://micheles.github.io/2017/05/02/hazard-outputs/), unless there is
only one realization. This means that in large computations we can
save orders of magnitudes of data storage: for instance for a big
computation we have for Canada the saving in space is from 1.27 TB
to 5.44 GB (240x improvement).

Consequently to the change above, the way we *export the hazard curves,
maps and uniform hazard spectra* has changed. It is still possible to
export the individual curves in a multi-realization calculation, but
only one realization at the time, and with a new command:

```bash
$ oq export hcurves/rlz-XXX # export the realization number XXX
$ oq export hmaps/rlz-XXX # export the realization number XXX
$ oq export uhs/rlz-XXX # export the realization number XXX
```

Since the generation of the curves is done at runtime the export will
be slower than before, but this is a good tradeoff. After all, most
users will never want to export the full set of realizations (NB: for those
few users we still have an efficient .hfd5 exporter doing exactly that).

Most users will be interested just in the statistical hazard curves,
maps and hazard spectra. Such outputs can be exported exactly as in
the past and without any performance penalty, since the statistical
curves are computed and stored in postprocessing. Also, now by default
the *mean hazard curves* are computed, whereas in the past their were
not computed.

The `classical_risk` calculator now reads directly the ProbabilityMaps
(in the past it read the individual hazard curves that are not stored anymore):
therefore the required data transfer has been reduced very significantly
and the performance of the calculator has improved. This is visible only
for source models with a lot of realizations.

The procedure *reading the Ground Motion Fields* from the datastore in
`scenario_risk` and `scenario_damage` calculators has been optimized:
the effect is small in small computations, but in a large calculation
with thousands of sites and GMFs we measured a speedup from 5 hours to
45 seconds.

The performance of the event based calculator has been improved
substantially in the *GMF-generation* phase, but the improvement is
sensible only in very large calculations. We measured improvements of a
factor 2 in speed and a factor 3 in memory occupation, but they can
be larger, depending on the size of your computation.

We are now using `rtree` to get the *nearest site model parameters*: this gives
more than one order of magnitude speedup in calculations that were dominate
by the site model associations.


Changes
-----------------------------

The *event tags* (strings) that we had in the past, visible to the
users in the rupture exporter and event loss table exporter are now
gone, replaced by the event IDs, which are 64 bit integers. In the
past the event IDs were internal indicators, hidden in the datastore
and not exposed to the user. Now they are exported because, thanks to
a major refactoring, the event IDs have become unique within a given
calculation and reproducibile, provided the parameter
`concurrent_tasks` is fixed.  This makes it possible to connect
directly the data saved in the datastore with the exported data, a
feature wanted by several power users for years.

The CSV exporter for the output `dmg_total` in damage calculators
now presents the data in a more readable format. The has been done
for the aggregate losses exported by the `scenario_risk` calculator.

The CSV exporter for the output `ruptures` is slightly different:
the field `serial` has been renamed as `rup_id`, the field `eid`
has been removed and the ordering of the fields is different.

The event loss table exporter is now producing an additional column
`rup_id` containing the rupture ID.

The `loss_curves` output has been removed. You can still export the
loss curves but it requires a different command than before. 

We renamed the `csq_` outputs of the scenario_damage to `losses_`

We removed the output `rup_data` which was internal.

Changed the npz export to export even GMFs outside of the maximum distance

Raised the limit on the event IDs
Changed the CSV exporter for classical_risk loss curves

Removed the csv exporter for all_loss_ratios
Removed the GSIM from the exported file name for the risk calculators
`ses_per_logic_tree_path` and `number_of_logic_tree_samples`
are constrained to 2 bytes only in UCERF now


Removed the .txt exporter for the GMF
Removed the .ext5 file
Renamed the datasets `avg_losses-` to `losses_by_asset-` enhancement
Added a command `utils/extract_sites` to generate good sites.csv files
Removed `rup_data` output
64 bit <-> 32 bit mismatch
Use a temporary `export_dir` in the tests
Made the slow classical tests fast by increasing the mesh spacing
Changed the storage of the events
Changed the way the GMFs are stored 
Stored the site IDs in a better way
Fixed `ignore_covs` for `scenario_risk`
Removed `ebrisk` calculator


hazardlib
--------------------------

The Hazard Modeller Toolkit (HMTK) has been merged into the
`oq-hazardlib` repository. The
[old repository](https://github.com/GEMScienceTools/hmtk) is still
there, for historical purposes, but it is in read-only mode and has
been deprecated. All development has to be made in oq-hazardlib
now. If you have scripts depending on the HMTK you will have to change
your imports: `import hmtk` will become `from openquake import hmtk`.

All the routines to read/write hazard sources and ruptures (and their tests)
have been moved from the engine into hazardlib, which is now self-consistent
in that respect.

We have extended the XML serializer to fully support
mutually exclusive sources and the calculator `calc_hazard_curves` has
been fixed to manage this case correctly.
 
We added an utility `openquake.hazardlib.stats.max_curve` to compute
the maximum of a set of hazard curves. This is a lot more efficient
than computing the quantile with value 1.0.

The mesh of a rupture is now stored as 32 bit array of floats instead of
a 64 bit array: this reduces the memory consumption and data storage
by half. Moreover, we have now an efficient way to realize ruptures
into HDF5 format.

We fixed a numerical issue involving the square root of small negative numbers,
due to rounding issues.

We have refactored the filtering mechanism and we have now a
single `IntegrationDistance` class in charge of filtering out sites and
ruptures outside of the integration distance. For safe of correctness,
we have disabled the `rtree` filtering if the site collection contains
points which are not at the sea level. In that case the geodetic distance
filtering is used.

There is now a new class `EBRupture` in hazardlib to describe event based
ruptures as a raw rupture object and an array of events: previously this
logic was in the engine. The change make it possible to serialize (read
and write) groups of event based ruptures in XML.

We fixed an ordering bug in `get_surface_boundaries`: now it returns the points
in clockwise order, i.e. the right order to produce a WKT string which used
to display the rupture.

We extended and refactored the `GmfComputer` class which is used by
the engine in scenario and event based calculations.

There is a new constructor for the `Polygon` class which is able 
to parse a WKT polygon string.

We fixed a bug when splitting sources with a `YoungsCoppersmith1985MFD`
magnitude frequence distribution: that made impossible to run such calculations
in some cases (depending on the splitting).

WebUI
-------------------

Add an icon for the OpenQuake WebUI

All the engine outputs are now streamed, in order to save memory.

The WebUI automatically creates the engine database at startup,
if needed.

The DbServer could not start in MacOS Sierra due to a change in the
low level libraries used in that platform that made it impossible
to fork sqlite; we worked around it by using a ThreadPoolExecutor instead
of a ProcessPoolExecutor.

Fix a bug when deleting a calculation from the WebUI
Added a view `get_available_gsims` to the WebUI
Changed the Web UI button from "Run Risk" to "Continue"
Made the full report exportable
Force hazard_calculation_id from POST to be an int
Improve the WebUI command

Bugs
----

We fixed a long standing bug in the event based risk calculation. In some
cases (when the hazard sites were given as a region) it was associating
incorrectly the assets to the sites and produced bogus numbers.

We fixed a couple of bugs affecting exposures with multiple assets of the
same taxonomy on the same site: that made it impossible to run `classical_risk`
and `scenario_risk` calculations for such exposures.

We fixed the .npz exporter for the GMFs in the case of a single event.

Remove an old, wrong check about Django

Fixed the CSV SES exporter: now the bounding box of the ruptures is using the
correct WKT ordering convention
Fixed encoding bug in the commands `oq engine --lhc` and `oq engine --lrc`
The avg_losses could not be stored in UCERF event based risk
Fixed bug in event_based_risk: it was impossible to use vulnerability
functions with "PM" distribution

Now the npz export for scenario calculations exports even GMFs outside
the maximum distance, which are all zeros. This is convenient when plotting
and consistent with CSV export. The export has also been fixed in the case
of a single event, i.e. `number_of_ground_motion_fields=1` which was broken.

Internal TXT exporters for the ground motion fields, used only for the
tests have been removed.

The .ext5 file has been removed. A great deal of internal refactoring
has been done (no PmapStats)

Additional validations
----------------------

We engine is more picky than before.

For instance if the user specifies `quantile_loss_curves`
or `conditional_loss_poes` in a `classical_damage` calculation he will now
get an error, since such features make no sense in that context (before
they were silently ignored).

If an exposure contains assets with taxonomies for which there are no
vulnerability functions available, now the user gets an early error
before starting the calculation and not in the middle of it.

Also, if an user provides a complex logic tree file which is
invalid for the scenario calculator, now she gets a clear error message.

There also checks for patological situations, like the user 
providing no intensity measure sites, no GSIMs, no sites: now a clearer
error message will be displayed.

Experimental new features
------------------------------

In this release the work on the UCERF calculators has continued,
even if they are still officially marked as experimental and left
undocumented on purpose.

There old time-independent classical calculator has been extended
to work with sampling of the logic tree.

The rupture filtering logic has been refactored and improved. 

We can parallelize the UCERF event based calculator by number of
stochastic event sets. This made it possible to run mean field
calculations in parallel (before they used a single core, since there
is a single branch in such models).

The data transfer has been hugely reduced in the calculator
`ucerf_risk`: now we do not return the rupture objects from the
workers, but only the event arrays, which are enough for the purposes
of the calculator. This saved around 100 GB of data transfer in large
calculations for California.
 
There is a brand new time-dependent classical calculator.

We started working on an event based calculator starting from Ground
Motion Fields provided by the user. The current version is still very
preliminary and requires the GMFs to be in NRML format, but we plan
to extend it to read the data from more efficient formats (CSV, HDF5)
in the near future.

We added a facility to serialize `Node` objects into HDF5 files. This is
the base for a future development that will allow to serialize point sources
into HDF5 datasets efficiently (scheduled for engine 2.5).

We introduced some preliminary support for the Grid Engine. This is useful
for people running the engine on big clusters and supercomputers. Unfortunately
since we do not have a supercomputer we are not able to really test this 
feature. Interested users should contact us and offer some help, like giving
us access to a Grid Engine cluster.

Deprecations
------------------------------

As of now, all of the risk XML exports are officially deprecated and
will be removed in the next release. The recommend exports to use are
the CSV ones for small outputs and the NPZ/HDF5 ones for large outputs.
