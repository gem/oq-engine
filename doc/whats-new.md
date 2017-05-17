Release notes for the OpenQuake Engine, version 2.4
===================================================

This release introduces several changes and improvements in the
engine calculators.

More than 40 pull requests were closed in oq-hazardlib and more than
200 pull requests were closed in oq-engine. For the complete list of
changes, please see the changelogs:
https://github.com/gem/oq-hazardlib/blob/engine-2.4/debian/changelog
and https://github.com/gem/oq-engine/blob/engine-2.4/debian/changelog.

A summary follows.

New features in the engine
--------------------------
 
The event based exports have been extended and now provides more
information. In particular it is possible to extract the association
between the ruptures and the seismic events. Just export the
`ruptures` output in XML format: for each rupture a list of stochastic
event sets where the rupture occurs as well as the specific event IDs
are exported.  In the past the event IDs were internal indicators,
hidden in the datastore and not exposed to the user: now the event IDs
are directly exported. This is possible because, thanks to a major
refactoring, now the event IDs are unique within a given calculation
and reproducibile - provided the parameter `concurrent_tasks` is
fixed. The event tags (strings) that we had in the past are now gone,
replaced by the event IDs, which are 64 bit integers.

The `asset_loss_table` is back, coupled with a new asset loss table
exporter producing a .hdf5 file.
Renamed the parameter `all_losses` to `asset_loss_table`

New `max_hazard_curves` flag.

UCERF calculators, but they are still officially
marked as experimental and are left undocumented on purpose. There is a
new time-dependent classical calculator, while the old calculators were
substantially improved.

Event based from the GMFs.


Loss maps npz exporter 


It is now possible to split a source model in several files and read
them as if they were a single file. Just specify the file names in the
source_model_logic_tree file. For instance, you could split by tectonic
region and have something like this:

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




New features in hazardlib
--------------------------

The calculator `calc_hazard_curves` now properly supports mutually exclusive
sources.

We extended the Rtree filtering to site parameters.
Also filtered only at sea level.

The sourcewriter.

Performance improvements
------------------------

The postprocessing of hazard curves has been substantially improved:
now it uses order of magnitudes less memory than before and it is
extremely efficient. For instance in our cluster we were able to
compute mean and max hazard curves for all sites in a calculation for
the Canada model with 200,000+ sites, XX+ hazard levels and 13,000+
realizations in 11 minutes, by spawning 3,500 tasks and using ~500 GB
of memory split on four machines. This is orders of magnitude better
than everything we processed before. Technically this has been achieved
by having the workers reading the data directly instead than passing
them via celery/rabbitmq, thus improving the scalability by orders
of magnitude.

A similar approach has been used in the event based risk calculator.
Now the loss curves and maps are produced in postprocessing by reading
directly the asset loss table. As a consequence such a calculation is
now a lot more scalable and efficient than before. We can easily compute
millions of loss curves.

Changes in the hazard exports
-----------------------------

We changed the way we export the hazard curves, maps and uniform
hazard spectra. The old command still work, but now by default the
individual curves/maps/spectra are not exported if there is more than
one realization. The mean curves instead are exported (before the
default was the opposite one). It is still possible to export the
individual curves, but only one realization at the time, and with a
new command:

```bash
$ oq export hcurves/rlz-XXX # export the realization number XXX
$ oq export hmaps/rlz-XXX # export the realization number XXX
$ oq export uhs/rlz-XXX # export the realization number XXX
```

The rationale was to reduce the size of the exported output which can be
huge for large calculations. For a discussion of the problem, see
http://micheles.github.io/2017/05/02/hazard-outputs/

The CSV exporter for the output `ruptures` is slightly different:
the field `serial` has been renamed as `rup_id`, the field `eid`
has been removed and the ordering of the fields is different.

The XML exporter for the output `ruptures` now contains only the
ruptures, without any duplication, and the list of event IDs
associated to the rupture. Before there was a rupture
for each seismic event, with potential duplications.


Changes in the risk exports
-----------------------------

The `loss_curves` output has been removed. You can still export the
loss curves but it requires a different command than before. 


The event loss table exporter is now producing an additional column
`rup_id` containing the rupture ID.

Renamed the `csq_` outputs of the scenario_damage to `losses_`


Deprecations
------------------------------

As of now, all of the risk XML exports are officially deprecated and
will be removed in the next release. The recommend exports to use are
the CSV ones (for small outputs) and the NPZ ones (for large outputs).

Fixes to the Web UI
-------------------

All the engine outputs are now streamed by the WebUI.
Allow the WebUI to bootstrap the DB 

Other
------

Now the npz export for scenario calculations exports even GMFs outside
the maximum distance, which are all zeros. This is convenient when plotting
and consistent with CSV export. The export has also been fixed in the case
of a single event, i.e. `number_of_ground_motion_fields=1` which was broken.

Internal TXT exporters for the ground motion fields, used only for the
testa have been removed.

The .ext5 file has been removed. A great deal of internal refactoring
has been done (no PmapStats)

Raised an error if the user specifies `quantile_loss_curves`
or `conditional_loss_poes` in a classical_damage calculation


Added a CSV exporter for the benefit-cost-ratio calculator enhancement

Changed the classical_risk calculator to read directly the probability maps
 
Raise a clear error message for logic trees invalid for scenario calculations 


