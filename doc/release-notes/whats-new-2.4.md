Release notes v2.4
==================

This release introduces several changes and improvements to the engine
calculators, most notably in the postprocessing of hazard curves and
in the postprocessing of loss curves. Also, several exporters
have been revised and several have been added, since there are new kinds
of outputs. A few important bugs have been fixed and a few spectacular
optimizations have been added.

More than 40 pull requests were closed in oq-hazardlib and more than
200 pull requests were closed in oq-engine. For the complete list of
changes, please see the changelogs:
https://github.com/gem/oq-hazardlib/blob/engine-2.4/debian/changelog
and https://github.com/gem/oq-engine/blob/engine-2.4/debian/changelog.

We have also decided a plan for dropping support to Python 2. We will abandon that
platform in the course of the year 2018. Precise dates have not been
fixed yet - on purpose - but everybody who is using hazardlib and/or the
engine as a library should think about migrating to Python 3. Please
contact us if this is a problem for you: we are keen to provide
advice for the migration.

New features in the engine
--------------------------
 
There are several new outputs/exporters.
 
- There is a new output and a new .hdf5 exporter for the event based risk
  individual asset losses. This is an optional output, generated only when
  you set the flag `asset_loss_table=true` in the job configuration file,
  or when the parameter `loss_ratios` is set.
- There is an equivalent output for the `scenario_risk` calculator, called
  `all_losses-rlzs`, and an `.npz` exporter for it. This is also an optional
  output generated when you set `asset_loss_table=true`.
- There is a new output `losses_by_event` produced by the `scenario_risk`
  calculator, which is similar to the aggregate loss table in the event based
  calculator: it contains the aggregate losses for each simulation of the scenario.
  There is a new CSV exporter for it.
- There are new outputs for the losses aggregated by taxonomy which are
  produced by the calculators `scenario_risk`, `event_based_risk` and
  `ucerf_risk`. There are CSV exporters associated.
- There is a new CSV exporter for the loss curves, while the old one has
  been removed.
- There are two new .npz exporters for the loss maps and the losses by asset.
- There is a new CSV exporter for the benefit-cost-ratio calculator.
- There is a new experimental CSV exporter for the ground motion fields
  produced by the event based calculator.
- The XML exporter for the output `ruptures` now contains only the
  ruptures, without any duplication, and, for each event set, the list of
  events associated to the rupture. Before there was a rupture for
  each seismic event, with potential duplications.

There is a new configuration parameter `max_hazard_curves` in the
job file, which by default is `False`. This parameter controls
the generation of the maximum hazard curves, a new feature.

There is a new configuration parameter `max_site_model_distance` in the
job file, with a default 5 km: before it was hard-coded. This parameter
controls the warnings for site model parameters which are far away from
the hazard sites.
 
There is a new configuration parameter `ses_seed` parameter in the job
file. It is the seed used in the generation of the ruptures in the event based
calculator, which is now distinct from the seed used in the sampling of
the source model, which is controlled by the `random_seed` parameter.

The parallelization library has been improved; now the `task_info` and
`job_info` datasets are automatically stored at the end of a calculation.

It is now possible to split a source model into several files and read
them as if they were a single file. Just specify the file names in the
source_model_logic_tree file. For instance, you could split by
tectonic region and have something like this:

```xml
 <logicTreeBranch branchID="b1">
   <uncertaintyModel>
     active_shallow_sources.xml
     stable_shallow_sources.xml
   </uncertaintyModel>
   <uncertaintyWeight>
     0.3
   </uncertaintyWeight>
 </logicTreeBranch>
```

Optimizations
------------------------

The *postprocessing of hazard curves* has been substantially improved:
now it requires orders of magnitude less memory than before and it is
extremely efficient. For instance in our cluster we were able to
compute mean and max hazard curves in a calculation for a Canada model
with 206,366 sites, 129 hazard levels and 13,122 realizations - spawning
~3,500 tasks and using ~500 GB of memory spread on four machines - in just
11 minutes. This is orders of magnitude better than everything we ever
managed to run before.

There is also a huge improvement in the *storage of the hazard
curves*: the [individual hazard curves are not stored anymore](
http://micheles.github.io/2017/05/02/hazard-outputs/), unless there
is only one realization. This means that in large computations we can
save orders of magnitudes of data storage: for instance for the Canada
computation the saving in space is from 1.27 TB to 5.44 GB (240x
improvement!).

Consequent to the change above, the way we *export the hazard curves,
maps and uniform hazard spectra* has changed. It is still possible to
export the individual curves in a multi-realization calculation, but
it requires a new command:

```bash
$ oq export hcurves/rlz-XXX # export the realization number XXX
$ oq export hmaps/rlz-XXX # export the realization number XXX
$ oq export uhs/rlz-XXX # export the realization number XXX
```

Since the generation of the curves is done at runtime the export will
be slower than before, but this is a good tradeoff. After all, most
users will never want to export the full set of realizations (for those
few users we still have an efficient HDF5 exporter doing exactly that,
please ask for info if you need it).

Most users will be interested just in the statistical hazard curves,
maps and hazard spectra. Such outputs can be exported exactly as in
the past and without any performance penalty, since the statistical
curves are computed and stored in postprocessing. Also, it should be noted
that now by default the *mean hazard curves are computed*.

The *postprocessing of loss curves* has been improved too: now the
loss curves and maps are produced by *reading directly the asset loss
table* from the workers, rather than passing them via the
celery/rabbitmq combo. The same is true for the hazard curves, but in
that case the data transfer issue is less dramatic. This change has
improved the scalability of the engine significantly and now we
can easily compute millions of loss maps. It should be noted that in
a cluster, the new approach requires a shared file system, otherwise
the postprocessing will use only the cores of the controller node.

While the loss maps are stored as before, in the event based
calculator the *loss curves have become a dynamic output*, generated
at runtime from the asset loss table (this is the same approach used
for the hazard curves, generated at runtime from the
ProbabilityMaps). This approach saves a huge amount of disk space. As
a consequence of the change the engine does not show the loss curves
output anymore; however the curves can still can be exported, but with
a new command:

```bash
$ oq export loss_curves/rlz-XXX # export the realization number XXX
```

Notice that CSV format that we are using now is different and a lot
more readable than the one we used in the past which was not even
a proper CSV (it was used for internal purposes only).

Among the huge improvements to the event based calculators one of the
most relevant is the fact that the *ruptures* are being saved and
read from the datastore in HDF5 format: before they were stored in
pickle format, for historical reasons.

The `classical_risk` calculator now reads the ProbabilityMaps
(in the past it read the individual hazard curves that are not stored anymore):
therefore the required data transfer has been significantly reduced 
and the performance of the calculator has improved. This is visible only
for source models with a lot of realizations, though.

The *reading of the Ground Motion Fields* from the datastore in
`scenario_risk` and `scenario_damage` calculators has been optimized:
the effect is small in small computations, but in a realistic calculation
with thousands of sites and GMFs we measured a speedup from 5 hours to
45 seconds.

The performance of the event based calculator has been improved
substantially in the *GMF-generation* phase. We
measured improvements of a factor 2 in speed and a factor 3 in memory
occupation, but they can be larger or smaller, depending on the size of your
computation. The larger the calculation, the more sensible is the improvement.

We are now using `rtree` to get the *nearest site model parameters*: this gives
more than one order of magnitude speedup in calculations that were dominated
by the site model associations. This is more and more important now
that we are able to tackle computations with 100,000+ assets.

User-visibile changes
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
now presents the data in a more readable format. The same has been done
for the aggregate losses exported by the `scenario_risk` calculator.

The CSV exporter for the output `ruptures` is slightly different:
the field `serial` has been renamed as `rup_id`, the field `eid`
has been removed and the ordering of the fields is different.

The event loss table exporter is now producing an additional column
`rup_id` containing the rupture ID.

We renamed the `csq_` outputs of the scenario_damage to `losses_`.

We renamed the datasets `avg_losses-` to `losses_by_asset-`.

We removed the output `rup_data` which was internal and not meant for
the final user.

We changed the .npz export to export even GMFs outside of the maximum distance,
with zero value: this makes it easier to visualize the results.

We removed the CSV exporter for the `all_loss_ratios` output in `scenario_risk`:
now there is an .npz exporter.

We removed the GSIM name from the exported file name for the scenario
calculators.

The .npz export for scenario calculations now exports GMFs outside
the maximum distance, which are all zeros. This is convenient when plotting
and consistent with CSV export.

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
by half.

We fixed a numerical issue involving the square root of small negative numbers,
due to rounding issues.

We have refactored the filtering mechanism and we have now a
single `IntegrationDistance` class in charge of filtering out sites and
ruptures outside of the integration distance. For sake of correctness,
we have disabled the `rtree` filtering if the site collection contains
points which are not at the sea level. In that case the geodetic distance
filtering is used.

There is now a new class `EBRupture` in hazardlib to describe event based
ruptures as a raw rupture object and an array of events: previously this
class was in the engine. The change make it possible to serialize (read
and write) groups of event based ruptures in NRML format.

We fixed an ordering bug in `get_surface_boundaries`: now it returns
the points in clockwise order, i.e. the right order to produce a WKT
bounding box which is used to plot the rupture with our QGIS plugin.

We extended and refactored the `GmfComputer` class which is used by
the engine in scenario and event based calculations.

There is a new constructor for the `Polygon` class which is able 
to parse a WKT polygon string.

We fixed a bug when splitting sources with a
`YoungsCoppersmith1985MFD` magnitude frequence distribution that made
impossible to run such calculations in some cases (depending on the
splitting).

WebUI
-------------------

We added an endpoint `GET /v1/available_gsims` to the REST API underlying
the WebUI. This is used by the OpenQuake platform to extract the list
of available GSIM classes. Now the platform uses the engine as a service
and it does not import directly any code from it.

We changed the Web UI button from "Run Risk" to "Continue", since it
can also be used for postprocessing of hazard calculations.

All the engine outputs are streamed from the WebUI. This saves memory in
the case of large outputs.

We added an output corresponding to the `fullreport` to the WebUI: this
is extremely useful to get information about a given calculation.

The WebUI automatically creates the engine database at startup,
if needed.

The DbServer could not start in MacOS Sierra, due to a change in the
low level libraries used in that platform that made it impossible
to fork sqlite; we worked around it by using a ThreadPoolExecutor instead
of a ProcessPoolExecutor.

We fixed a bug when deleting a calculation from the WebUI: now it is possible
to do so if the user is the owner of that calculation.

The command `oq webui start` now gives a clear error message if it is run
from a multi-user package installation.

We removed a wrong and now useless check about Django 1.5.

We have now a desktop icon for the OpenQuake WebUI both for Linux and Windows
platforms.

The logic about how `local_settings.py` is found has changed: first it
is searched in the folder where the `openquake.dbserver` is started
from; if it does not exist in the folder it will be searched in the
`openquake.server` location itself. If no `local_settings.py` is
provided at all, default settings will be used.

Bugs
----

The was a size limit on the event ID (65,536 events for task) that
could be exceeded in large calculations. We raised that limit to over 4
billion events per task.

We fixed a long standing bug in the event based risk calculation. In some
cases (when the hazard sites were given as a region) it was associating
incorrectly the assets to the sites and produced bogus numbers.

We fixed a couple of bugs affecting exposures with multiple assets of the
same taxonomy on the same site: that made it impossible to run `classical_risk`
and `scenario_risk` calculations for such exposures.

We fixed an annoying encoding bug in the commands `oq engine --lhc` and
`oq engine --lrc` which affected the display of calculations with non-ASCII
characters in the description.

We fixed a bug in `event_based_risk`: it was impossible to use
vulnerability functions with "PM" distribution, i.e. with Probability
Mass Functions. Now they work as expected.

The .npz export for scenario calculations has been fixed in the case
of a single event, i.e. when `number_of_ground_motion_fields=1`, which
was broken.

Additional validations
----------------------

The engine is more picky than before. For instance if an user
specifies `quantile_loss_curves` or `conditional_loss_poes` in a
`classical_damage` calculation she will now get an error, since such
settings make no sense in that context. Before they were silently
ignored.

If an exposure contains assets with taxonomies for which there are no
vulnerability functions available, now the user gets a clear error
before starting the calculation and not in the middle of it.

If an user provides a complex logic tree file which is
invalid for the scenario calculator, now she gets a clear error message.

There are more checks for patological situations, like the user 
providing no intensity measure sites, no GSIMs, no sites: now a clearer
error message will be displayed.

Experimental new features
------------------------------

In this release the work on the UCERF calculators has continued,
even if they are still officially marked as experimental and left
undocumented on purpose.

There `ucerf_classical` calculator has been extended to work with
sampling of the logic tree. The rupture filtering logic has been
refactored and made more consistent with the other calculators.

The `ucerf_rupture` calculator has been extended so that we can
parallelize by number of stochastic event sets. This improvement made
it possible to run mean field calculations in parallel: before such
calculations used a single core.

The data transfer has been hugely reduced in the calculator
`ucerf_risk`: now we do not return the rupture objects from the
workers, but only the event arrays, which are enough for the purposes
of the calculator. This saved around 100 GB of data transfer in large
calculations for California.

We fixed a bug in `ucerf_risk` that prevented the average losses
from being stored. Now this works out of the box, provided you
set `avg_losses=true` in the `job.ini` file.

There is a brand new time-dependent UCERF classical calculator.

We started working on an event based calculator starting from Ground
Motion Fields provided by the user. The current version is still very
preliminary and requires the GMFs to be in NRML format, but we plan
to extend it to read the data from more efficient formats (CSV, HDF5)
in the near future.

We added a facility to serialize `Node` objects into HDF5 files. This is
the base for a future development that will allow to serialize point sources
into HDF5 datasets efficiently (scheduled for engine 2.5).

We introduced some preliminary support for the Grid Engine. This is useful
for people running the engine on big clusters and supercomputers. Unfortunately,
since we do not have a supercomputer, we are not able to really test this 
feature. Interested users should contact us and offer some help, like giving
us access to a Grid Engine cluster.

Internal changes
--------------------

As always, there were several internal changes to the engine. They are invisible
to regular users, so I am not listing all of the changes here. However, I
will list some changes that may be of interests to power users and people
developing with the engine.

The parameters `ses_per_logic_tree_path` and `number_of_logic_tree_samples`
are constrained to a maximum value of 65,536 only in UCERF now.

As usual the layout of the datastore has changed; in particular the way
the GMFs and the events are stored is different.

In the past running the tests littered your file systems with lots of
generated files, both in the current directory and in the /tmp directory.
Now the tests never write on the current directory and they cleanup the
/tmp directory (if they are successful).

There is an internal configuration flag `ignore_covs` which is needed to disable
the use of the coefficients of variations in vulnerability functions, for
debugging purposes. Now this flag works for `scenario_risk` calculations too.
Before it was restricted to `event_based_risk`.

In release 2.3 we introduced temporarily an `ebrisk` calculator. It is
gone now, just use the good old `event_based_risk` calculator.

Internal TXT exporters for the ground motion fields, used only for the
tests, have been removed.

Packaging
-------------------------

[Matplotlib](https://matplotlib.org/) is now a requirement for the
OpenQuake Engine and hazardlib. It's included in the OpenQuake
installers and packages as a Python wheel.
[Basemap](https://matplotlib.org/basemap/) can be installed to
enable some extra plotting features from the Hazard Modeller Toolkit.
Basemap is provided as pre-compiled Python
wheel, it's included in installers and in the
`python-oq-libs-extra` package on Ubuntu and RedHat/CentOS.
`python-oq-libs-extra` isn't required on a headless server setup.

A safety measure has been introduced to check that the OpenQuake
Engine is talking to the proper DbServer instance. This helps debugging
issues in the case of multiple installations of the engine (for instance
a system-wide multi-user installation and a single-user development
installation coexisting on the same machine).

[h5py](http://www.h5py.org/) has been updated to version 2.7.0.

A template for PAM authentication
is now provided. This allows the WebUI to authenticate users against
system users on a Linux server.

The RPM `python-oq-engine` package has been splitted into `python-oq-engine`,
`python-oq-engine-master` and `python-oq-engine-worker`. This reduces
the amount of dependencies needed by `python-oq-engine` when installed on
a single node. Specific configurations for _master_ and _workers_ nodes
are provided by dedicated packages.
This setup will be ported to Ubuntu packages too in the next release.
See the [documentation](cluster) for further information.

Deprecations
------------------------------

As of now, all of the risk XML exports are officially deprecated and
will be removed in the next release. The recommended exports to use are
the CSV ones for small outputs and the .npz/HDF5 ones for large outputs.

Python 2.7 is not officially deprecated yet, but it will be deprecated soon.
The version we use for development and production since the beginning of
2017 is Python 3.5. Here is [our roadmap for the future](https://github.com/gem/oq-engine/issues/2803).
