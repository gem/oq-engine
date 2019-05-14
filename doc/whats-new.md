Release notes for the OpenQuake Engine, version 3.4
===================================================

This is a major release featuring a new calculator for event based risk and
several improvements and bug fixes. Over 190 pull requests were merged. For the complete list of changes, see the changelog: https://github.com/gem/oq-engine/blob/engine-3.4/debian/changelog

The ebrisk calculator
---------------------

The experience with the Global Risk Model made the scalability limits
of the event based calculators clear. The approach of computing the
GMFs, storing them on an HDF5 file during the hazard calculation and
read them again during the risk calculation, scales up to ~100 GB of
data.  Over that limit - and most global risk calculations are over
that limit - it is more convenient to compute the GMFs directly in the
risk phase, without ever storing them, because recomputing the GMFs
can be faster and memory efficient than reading them.
This is the approach taken by the new `ebrisk` calculator.

Moreover, since in all global risk calculation we ignored asset
correlation - the vulnerability functions had zeros for the coefficients of
variation - the `ebrisk` calculator has been optimized for that case. As
a result in large calculations it is a lot faster than the previous
`event_based_risk` calculator, and it requires a lot less memory too.
You should use it in preference to the old calculator except in two
situations:

1. if you are interested in asset correlation
2. the calculation is of middle size and you need to reuse the GMFs

For instance, if you are interested in GMFs correlation, computing the
GMFs is so slow that it makes sense to store them in the hazard phase.
However GMF correlation is viable only if you have few sites (say 1000)
because of memory and computational resources constraints.

The `ebrisk` calculator has two more features with respect to the
`event_based_risk` calculator:

1. it allows to compute aggregate loss curves and maps
2. it allows to store the asset loss table

In order to compute the aggregate loss curves and maps you need to specify in
the job.ini file the `aggregate_by` parameter. For instance, if you
want to aggregate by the tags taxonomy and occupancy you can specify

`aggregate_by = taxonomy, occupancy`

There is no limit on the number of tags that can be used for aggregation,
you can list any tag present in the exposure.

Storing the asset loss table - an array of 32 bit floats of
shape ``(A, E, L)`` where ``A`` is the number of assets, ``E`` the
number of events and ``L`` the number of loss types - is disabled by
default, because it is likely to cause the engine to run out of
memory: for instance one of our typical risk calculation with 1.25
million assets, 10 million events and 2 loss types would produce an
array of ~91 TB, which is way too big to be stored. Still, for
debugging purposes in small calculations you may set

`asset_loss_table=true`

and have it saved in the datastore. There are no export facilities for
it on purpose. This feature is only meant for power users that know their
way around the datastore.

Thanks to the power of the `ebrisk` calculator we were able to remove
the limit on the number of sites in event based calculations. Before
it was set to 65,536 hazard sites, now it is at 4,294,967,296 sites,
which is more than enough for the foreseeable future.
We managed to run calculations with 500,000 sites without any issue.

The implementation of the `ebrisk` calculator required extending our
parallelization infrastructure. In particular, now each task can
produce (indirectly) subtasks, which is major feat, because it means
that a task can decide how many subtasks to generate. Before only
the master node could do that, which was inconvenient because sometimes
knowing how many tasks to generate is an expensive operation. Before that
operation was effectively serialized on the master node, while now it can
be parallelized as well.

If you want to try the `ebrisk` calculator, please check the demo in
`demos/risk/EventBasedRisk/job_eb.ini` and the documentation in
https://github.com/gem/oq-engine/blob/engine-3.4/doc/adv-manual/risk.rst

Improvements on the other calculators
-------------------------------------------------

There was a lot of work on the old calculators too.

1. We discovered that saving the source information was causing an
out of memory issue in the case of large models like Australia and
Italy. The solution was to call the procedure `store_source_info` only
once - at the end of the calculation - and not once per task. The
change improved tremendously the saving speed, so that the
tasks results did not have time to queue up in memory.

2. We changed the source filtering approach: now it is performed in the
worker nodes, not in the controller node. The new approach saved a lot of
memory. It is also more efficient because it makes use of all available
cores in the worker nodes.

3. We parallelized the reading of the exposures: that makes a
difference in continental scale risk calculations that can have dozens of
exposures (one per country).

4. We now save more information in the case of site specific
calculations: in particular for classical calculations we store
complete information about the ruptures. This will help in future
optimizations of the disaggregation calculator. Moreover, we save
information the "best" realization, i.e. the realization closest to the
mean hazard curve.

5. When running a classical calculation we now save a dataset
`disagg_by_grp` that contains the highest PoE for the highest
intensity produced by each source group among all sites, IMTs and
GMPEs: this is useful to see which are the source groups producing the
highest hazard, and also to see if the are source groups giving zero
contribution to the highest hazard.

6. We worked also on the GMPE logic tree: now it is possible to serialize
a `GsimLogicTree` object in TOML format, which is the format used inside
the datastore. Previously the GMPE logic tree was stored in XML format.

7. The logic used in the event based risk calculator - read the hazard
sites in preference from the site model, not from the exposure - has
been extended to all calculators.

8. We changed the algorithm used in all kinds of event based calculations
and now by default the sources are not split anymore. This makes the
generation of ruptures a lot faster. Before this behavior was not the
default, because we wanted to keep compatibility with the past.
With the new algorithm the Montecarlo seeds are generated
differently, so the sampled ruptures are different than before but
statistically equivalent.

9. We also improved the saving of the ruptures: now they are filtered
before saving them, thus avoiding saving irrelevant ruptures.
For speed, the filtering is done with a bounding box filter, which is
not precise: most ruptures which are far away are removed, but not
all of them. This is not a problem because during the ground motion
filter calculator the precise filter is used and they are correctly
discarded. The bounding box filter is enough to save disk space and
storing time.

Experimental new features
-------------------------

There is now an experimental support for cluster of sources, in the
sense of the famous New Madrid cluster, both for classical and event
based calculations. This is a major new feature that required
substantial changes to the internals of hazardlib. In particular now
it is possible to define *non-poissonian temporal occurrence
models*. Moreover, now there is a a precise definition of atomic source
groups, i.e. source groups  that cannot be split across tasks. A source
group is considered atomic if at least one of the following three things
is true:

1. the source group is a cluster (cluster == 'true')
2. the sources are mutually exclusive (src_interdep == 'mutex')
3. the ruptures are mutually exclusive (rup_interdep == 'mutex')

These features are not documented yet, since we are in an experimental
phase, but we have tests and examples in the engine code base; users
wanting to play with these features should contact us and we will be
keen to help.

The GMF exporter now also export informations about the inter event
residuals and inter event standard deviations for each event. Here is an
example of the file that could be generated:
```
$ cat sigma_epsilon.csv
eid,sig_PGA,sig_SA(0.1),eps_PGA,eps_SA(0.1)
12884901888,2.600000E-01,3.180000E-01,1.887697E+00,-7.447188E-01
12884901889,2.600000E-01,3.180000E-01,-3.726182E-01,1.771590E-01
12884901890,2.600000E-01,3.180000E-01,-8.312525E-01,5.412349E-01
```

hazardlib/HMTK
-----------------------------

As usual there was a lot of work on hazardlib. At the infrastructural
level the most relevant change is that now we have a serialization
procedure from GMPE objects into TOML and viceversa, working also for
GMPEs with arguments. Moreover, there is now a two step initialization
protocol for all GMPEs: if you need to do some special initialization
(say a slow initialization, or an initialization requiring access to
the filesystem) do it in the ``init()`` method, not in
``__init__``. The engine will call automatically the ``init()`` method
at the right time, i.e. while reading the GMPE logic tree file.

A couple of additional checks on GSIM classes where added:

1. when deriving a GSIM class a mispelling in the distance name like
   ``REQUIRES_DISTANCES = {'rhyp'}`` is now flagged immediately
   as an error (the correct spelling is ``rhypo``)
2. class level variables which are sets (like ``REQUIRES_DISTANCES``)
   are now automagically converted into Python ``frozensets``. This avoids
   potential mutability bugs while keeping backward compatibility.

We removed a depth check in `mesh.get_distance_matrix` and now it is
possible to compute correlation matrices even if the points are not
all at the same dephts: the depths are simply ignored. This is
consistent with the usual definition of spatial correlation that
consider only the longitude and latitude components and not the depths.

We added the ability to specify a `time_cutoff` parameter (in days) in the
decluster window of the HMKT. The syntax to use is as in this example:
```
  declust_config = {"time_distance_window": GardnerKnopoffWindow(), 
                    "fs_time_prop": 1.0, 
                    "time_cutoff": 100}
```
Rodolfo Puglia contributed spectral acceleration amplitudes at 2.5, 2.75 and
4 seconds for the Bindi_2014 GMPE, which is relevant for the Italy model.

Giovanni Lanzano contributed the SkarlatoudisEtAlSSlab2013 GMPE,
relevant for Greece.

Changlong Li contributed an update to the YU2013 GMPE, which is
relevant for the China model.

Valerio Poggi contributed a GMPE for average SA calculations.

Chris van Houtte contributed quite a few new GMPEs specific for New
Zealand, in particular in Bradley_2013 and Christchurch GMPEs.

WebAPI and plotting
-------------------

We extended the WebAPI to be able to extract specific hazard curves, maps
and UHS (i.e. IMT-specific and site specific). There is now an `Extractor`
class to extract data from a local calculation and a `WebExtractor` class to
extract data from a remote calculation. They are documented here:

https://github.com/gem/oq-engine/blob/engine-3.4/doc/adv-manual/extract-api.rst

Thanks to the WebExtractor it is not easier to import a remote calculation
into a local database with the `oq importcalc` command:
```
  $ oq importcalc --help
  usage: oq importcalc [-h] calc_id
  
  Import a remote calculation into the local database. server, username and
  password must be specified in an openquake.cfg file. NB: calc_id can be a
  local pathname to a datastore not already present in the database: in that
  case it is imported in the db.
  
  positional arguments:
    calc_id     calculation ID or pathname
  
  optional arguments:
    -h, --help  show this help message and exit
```
Moreover the plotting facilities of the engine have been extended so
that it is now possible to plot hazard curves, maps and uniform hazard
spectra even of a remote calculation. Notice that `oq plot` is still
unofficial and subject to changes: the official way to plot hazard
results is the [QGIS plugin](https://plugins.qgis.org/plugins/svir/).

We added a few new `extract` commands: as usual you can see the full
list of them with the command
```
$ oq info --extract
```

New checks and validations
---------------------------

1. We restored the source logic validation routines that were lost years ago.
Now you will get errors if you try to define invalid logic
trees, like using an `applyToSources` with multiple source IDs on
parameters of kind "Absolute":
```xml
   <!-- this is invalid -->
   <logicTreeBranchSet branchSetID="bs31"
                       uncertaintyType="abGRAbsolute"
		       applyToSources="1 2">
```
2. There is an additional check in the `uncertaintyModel` tag of the source
model logic tree file, to forbid accidentally duplicated source model files.

3. We now raise an error for missing occupants in the exposure
before starting the calculation, not in the middle of it.

4. Now we make sure the IMTs are sorted by period in the `job.ini` file,
to make it easier to compare different `job.ini` files.

5. We added a check for missing retrofitted values in the benefit-cost-ratio
calculator.

6. We added a check to forbid the users from setting
`ses_per_logic_tree_path = 0` (this happened to users confusing
`ses_per_logic_tree_path` with `number_of_logic_tree_samples`).

7. We raise an error early if somebody tries to disaggregate a model
with atomic source groups, since this feature is not supported yet.

Bug fixes
---------

1. We fixed an error in the calculation of loss maps from loss curves: instead
of the risk investigation time the hazard investigation time parameter was
passed, thus producing wrong curves when the two parameters were different.

2. The event based risk calculator in engine 3.3 had an issue with
tabular GMPEs stored in external HDF5 files: the directory path was
set incorrectly and the files not found. Now the tables are fully
serialized inside the datastore and the risk calculator can take
advantage of that.

3. We fixed a regression in `applyToSources` that made it impossible,
in engine 3.3 to use it on more than 1 source, i.e. to write things
like `applyToSources="1 2"` even when it would have been correct.

4. Engine 3.3 introduced a bug in the XML exporter for the hazard curves:
files with different spectral accelerations contained always the same
content, corresponding to the highest period. This has been fixed.

5. Sometimes the `oq abort` command was giving confusing information:
now it prints a message only for jobs that were really aborted.

6. The documentation for the event loss table exporter in the manual
was horribly outdated and has been fixed.

Changes
-----------------------------------------------

1. We changed the way the hazard maps are stored, therefore it is not
possible to export from engine 3.4 the results of a calculation
executed with a previous release.

2. We removed the realization index column from the event loss table export and
from the GMF csv export: they were redundant in event based calculations
and confusing in scenario calculations where there is a single realization.

3. We removed the `site_model.xml` exporter since it was not used.

4. We removed the command `oq extract hazard/rlzs`: if you want to export
all the hazard curves, set the flag `individual_curves=true` in the
job.ini, as explained in
https://github.com/gem/oq-engine/blob/engine-3.4/doc/faq-hazard.md

5. We removed the parameter `max_site_model_distance`, since its role
is now taken by the `asset_hazard_distance` parameter.
 
6. We changed the syntax of the ``MultiGMPE`` feature which was
experimental and undocumented. It is now stable and documented here:
https://github.com/gem/oq-engine/blob/engine-3.4/doc/adv-manual/parametric-gmpes.rst.

7. In the `job.ini` file you should replace the parameters
`quantile_loss_curves` and `quantile_loss_maps` with `quantiles`, otherwise
you will get an annoying warning.

8. We changed the exporter for the aggregate losses: now the
exposed value and loss ratios are exported too.

9. The exporter for the loss curves now exports more fields.

Deprecations
--------------------

1. The hazard XML exporters have been officially deprecated: unofficially,
they have been deprecated for years, since the time we introduced the CSV
exporters. You use the CSV for regular usage; for advanced postprocessing -
typically involving the hazard curves for all realizations - you should use
the Extractor API instead.

2. The scenario GMF XML exporter has been deprecated and will be removed in
the future: you should use the CSV exported instead.

3. The insured losses feature has been deprecated months ago and it is still
deprecated: it may disappear or change in the next release.

4. The ability to compute individual loss curves and maps in the
`event_based_risk` calculator has been deprecated and will be removed
in the future, since the interesting things to compute are the aggregated
loss curves and maps which are available in the `ebrisk` calculator.

5. Windows 7 has been deprecated as a platform for running the engine since
it is very old, it is going out of support from Microsoft next year,
and we discovered that sometimes engine calculations hang with it.

Packaging and internals
------------------------

1. We have removed the dependency from nose. You can still run the tests
with nose, but the engine does not import it anymore: it can be
considered a completely external tool.

2. We are considering using pytest as preferred testing tool for the
engine, since it is more powerful and well maintained. It also has
better discovery features that helped us to find hidden broken tests.

3. We have added a dependency from toml, a small module used to
serialize/deserialize literal Python objects to TOML format.

4. It is now possible to convert the Windows nightly builds into a development
environment.

5. There is now a `sap.script` decorator that should be used instead
of the `sap.Script` class.

6. We added a command `oq info --parameters` tha displays the list of
all the parameters recognized by job.ini files.

7. We reduced drastically the number of client sockets attached to
the DbServer, which was a waste of resources, and we removed the
DbServer log file, which was not used.
