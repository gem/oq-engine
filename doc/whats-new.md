Release notes for the OpenQuake Engine, version 2.4
===================================================

This release introduces several changes and improvements to the
engine calculators, most notably in the postprocessing of
hazard curves in classical PSHA calculations and in the postprocessing of
loss curves in event based risk calculations. Also, the exporters
have been revised and extended.

More than 40 pull requests were closed in oq-hazardlib and more than
200 pull requests were closed in oq-engine. For the complete list of
changes, please see the changelogs:
https://github.com/gem/oq-hazardlib/blob/engine-2.4/debian/changelog
and https://github.com/gem/oq-engine/blob/engine-2.4/debian/changelog.

A summary follows.

New features in the engine
--------------------------
 
There are several new outputs/exporters.
 
- There are new .csv exporters for the aggregated losses by taxonomy which are
  computed by the calculators `scenario_risk`, `event_based_risk` and
  `ucerf_risk`.
- There is a new output and an .hdf5 exporter for the `asset_loss_table`, i.e.
  the full table of losses for each asset. This is an optional output of
  the `event_based_risk` calculator, generated when you set the flag
  `asset_loss_table=true` in the `job.ini` configuration file.
- There is an equivalent output for the `scenario_risk` calculator, called
  `all_losses-rlzs`, an an `.npz` exporter for it. This is also an optional
  output generated when you set `asset_loss_table=true`.
- There is a new output `losses by event` produced by the `scenario_risk`
  calculator, which is similar to the event loss table in the event based
  calculator: it contains the aggregate losses for each seismic event.
  There is a also new CSV exporter for it.
- We are now exporting the loss maps and the losses by asset in .npz format.
- We have a new CSV exporter for the Benefit-Cost-Ratio calculator.
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

Optimizations
------------------------

The *postprocessing of hazard curves* has been substantially improved:
now it uses orders of magnitude less memory than before and it is
extremely efficient. For instance in our cluster we were able to
compute mean and max hazard curves in a calculation for the Canada
model with 206,366 sites, 129 hazard levels and 13,122 realizations in
11 minutes, by spawning ~3,500 tasks and using ~500 GB of memory among
four machines. This is orders of magnitude better than everything we
ever managed to run before. Technically this has been achieved by
having the workers reading the data directly instead than passing them
via the celery/rabbitmq combo, thus improving the scalability of the
engine very significantly.

A similar approach has been used in the event based risk calculator.
Now the loss curves and maps are produced in postprocessing by reading
directly the asset loss table. As a consequence such a calculation is
a lot more scalable and efficient than before. We can easily compute
millions of loss maps.

While loss maps are stored as before, *loss curves have become a dynamic
output*, generated at runtime from the loss ratios (this is the same
approach used for the hazard curves, generated from the ProbabilityMaps).
This saves a huge amount of disk space.

The performance of the event based
calculator has been improved substantially in the *GMF-generation*
phase, but this is visible only in very large calculations. We measured
improvements of a factor 2 in speed and a factor 3 in memory occupation.

We have a huge improvement in the *storage of the hazard curves*:
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

Most users will just be interested the statistical hazard curves, maps
and hazard spectra. Such outputs can be exported exactly as in the
past and without any performance penalty, since the statistical curves
are computed and stored in postprocessing very efficiently. Also, now
by default the *mean hazard curves* are computed, whereas in the past
their were not computed.

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

We are now using `rtree` to get the *nearest site model parameters*: this gives
more than one order of magnitude speedup in calculations that were dominate
by the site model associations.


Changes
-----------------------------

The event tags (strings) that we had in the past are now
gone, replaced by the event IDs, which are 64 bit integers. In the
past the event IDs were internal indicators, hidden in the datastore
and not exposed to the user: now the event IDs are directly
exported. This is possible because, thanks to a major refactoring, now
the event IDs are unique within a given calculation and reproducibile,
provided the parameter `concurrent_tasks` is fixed.

The CSV exporter for the output `ruptures` is slightly different:
the field `serial` has been renamed as `rup_id`, the field `eid`
has been removed and the ordering of the fields is different.

The event loss table exporter is now producing an additional column
`rup_id` containing the rupture ID.

The `loss_curves` output has been removed. You can still export the
loss curves but it requires a different command than before. 

We renamed the `csq_` outputs of the scenario_damage to `losses_`

We removed the output `rup_data` which was internal.

Improvements in hazardlib
--------------------------

The Hazard Modeller Toolkit (HMTK) has been merged into oq-hazardlib. The
[old repository](https://github.com/GEMScienceTools/hmtk) is still there,
for historical purposes, but it is in read-only mode and has been
deprecated. All development has to be made in oq-hazardlib now. If you
have scripts depending on the HMTK you will have to change your imports:
`import hmtk` will become `from openquake import hmtk`.

All the routines to read/write hazard sources and ruptures and their tests
have been moved from the engine into hazardlib, which is now self-consistent
in that respected.

We have extended the XML serializer to fully support
mutually exclusive sources and the calculator `calc_hazard_curves` has
been fixed to manage this case correctly.
 
We added a facility to serialize `Node` objects into HDF5 files. This is
the base for a future development that will allow to serialize point sources
into HDF5 datasets efficiently (scheduled for engine 2.5).
 
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

Bugs
----

We fixed a bug when splitting sources with a `YoungsCoppersmith1985MFD`
magnitude frequence distribution: that made impossible to run such calculations
in some cases (depending on the splitting).

We fixed a long standing bug in the event based risk calculation. In some
cases (when the hazard sites were given as a region) it was associating
incorrectly the assets to the sites and produced bogus numbers.

We fixed a couple of bugs affecting exposures with multiple assets of the
same taxonomy on the same site: that made it impossible to run `classical_risk`
and `scenario_risk` calculations for such exposures.

Fixed the .npz exporter for the GMFs in the case of a single event

Remove an old, wrong check about Django
Use a ThreadPoolExecutor instead of a ProcessPoolExecutor in dbserver.py
for MacOS Sierra.

Fixed the CSV SES exporter: now the bounding box of the ruptures is using the
correct WKT ordering convention
Fixed encoding bug in the commands `oq engine --lhc` and `oq engine --lrc`
The avg_losses could not be stored in UCERF event based risk
Fixed bug in event_based_risk: it was impossible to use vulnerability
functions with "PM" distribution

Deprecations
------------------------------

As of now, all of the risk XML exports are officially deprecated and
will be removed in the next release. The recommend exports to use are
the CSV ones (for small outputs) and the NPZ/HDF5 ones (for large outputs).

Fixes to the Web UI
-------------------

All the engine outputs are now streamed by the WebUI.
Allow the WebUI to bootstrap the DB 

Experimental new features
------------------------------

UCERF calculators, but they are still officially
marked as experimental and are left undocumented on purpose. There is a
new time-dependent classical calculator, while the old calculators were
substantially improved. Now we can parallelize UCERF event based by SES.
Do not return the ruptures in ucerf_risk, only the events
 
Event based from the GMFs.

Other
------

Now the npz export for scenario calculations exports even GMFs outside
the maximum distance, which are all zeros. This is convenient when plotting
and consistent with CSV export. The export has also been fixed in the case
of a single event, i.e. `number_of_ground_motion_fields=1` which was broken.

Internal TXT exporters for the ground motion fields, used only for the
tests have been removed.

The .ext5 file has been removed. A great deal of internal refactoring
has been done (no PmapStats)

Raised an error if the user specifies `quantile_loss_curves`
or `conditional_loss_poes` in a classical_damage calculation

Added a CSV exporter for the benefit-cost-ratio calculator enhancement

Changed the classical_risk calculator to read directly the probability maps
 
Raise a clear error message for logic trees invalid for scenario calculations 


