Release notes for the OpenQuake Engine, version 3.2
===================================================

This release features several improvements to the engine calculators, some
new features and many bug fixes. Over 190 issues were closed. For the complete
list of changes, please see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.2/debian/changelog.
Here is a summary.

Improvements to the calculators
-------------------------------

As always, there was a lot of work on the event based calculators,
both on the hazard side and on the risk side. Some simplifications were
made, and now the only way to run an event based risk calculation
is by reading the ground motion fields stored in the datastore. In
previous versions of the engine, in the case of an event based risk
calculation with a single `job.ini` file, the GMFs were calculated 
on the fly and kept in memory to compute the losses, but this approach had strong
limitations and a bad performance. Now, the recommended way to run an
event based risk calculation is to use two different `job.ini`
files, one for the hazard part (generating the ruptures and producing the 
ground motion fields) and one for the risk part (computing the losses),
and to run the risk calculation after the hazard. 
If you use a single job file, the GMFs will have to
be transferred to the workers and this is less efficient than
reading them from the datastore. Furthermore, on a cluster, rabbitmq/celery
may run out of memory or fail in strange ways.

The improvements to the event based calculators were motivated by
the Global Risk Model project, which requires to be able to run
calculations of unprecedented size. Since the calculations may become so
huge as to be unmanagable, there is now a limit on the maximum size of the 
GMFs that can be stored in the datastore: the
`gmf_data` dataset cannot contain more than 4 billion rows. This
limit forbids the users from running hazard calculations which are
too big and would be impossible to run on the risk side anyway. If
you are reaching the limit, you must revisit your calculation 
configuration and try to reduce your calculation,
preferably by reducing the number of realizations in the logic tree.

The source prefiltering phase and the rupture-generation phase have
been merged into a single preprocessing phase. At the end of it, an
upper limit for the estimated size of the GMFs is printed: it means
that you can kill a calculation if see you that the estimated GMFs
size is of the order of terabytes. It should be noticed that the
estimated size is an upper limit: if there is a `minimum_intensity`
parameter, the GMFs below the threshold are discarded and therefore the
actual size of the GMFs can be a lot less than the estimate, even
orders of magnitude less.

There was a *huge* improvement in the algorithm used to compute the
loss curves and loss maps: they do not require storing the entire asset loss table
anymore, so a lot of calculations that were technically impossible in the
past are now possible and often even easy. Thanks to this breakthrough,
the loss curves and maps are no more experimental outputs but *bona fide*
outputs, they appear in the Web UI and are exportable like all the other
risk outputs.

Due to the many changes in the event based calculators — changes in the
source splitting procedure, changes in the the source weights, changes
in the seeds generation algorithm, changes in some outputs from
64 bit floats to 32 bit floats and others — the numbers generated with
this release of the engine are slightly different than before.
This is expected.

The way data is stored in the datastore has also changed, in
particular, for the indices of the GMFs and the event based ruptures.
These changes have been forced by a bug in HDFView 3.0 which is unable to visualize
variable-length structured arrays, so we had to simplify the data
structures used by the engine.

During the calculation of the statistical hazard curves we now also compute
the statistical hazard maps and store them. This makes the export of the
hazard maps extremely fast at the cost of making the main computation slightly
slower.

We implemented the equivalent epicentre distance approximation. This is
useful if you want to compare the results of a hazard calculation made
with the OpenQuake engine with some other code using that approximation
(i.e. USGS Fortran code).

There were also some minor changes in the risk calculators, in particular
in the number of risk inputs generated.

We changed the `dmg_by_event` exporter which now produces a single .csv with
all realizations instead of one file per realization. This is more convenient
and more consistent with the way the GMF exporter works.

Finally the memory consumption in UCERF classical calculations has been
reduced drastically and the calculator is now optimized and simplified.

Changes to hazardlib/HMTK
-------------------------

We made some work to make hazardlib more extensible: in particular, it
is now possible to add new site parameters, new intensity measure
types and new ground motion prediction equations *in user code*, without
changing core modules of hazardlib. This was a major improvement.

While at it, we added some new site parameters and new IMTs for
geotechnic hazard. We also added a MultiGMPE clas calling different
IMTs from different GMPEs, again for use in geotechnic hazard.

We improved the GSIM deprecation mechanism. Now you can write something
like this in your code

```python
class TheOldGSIM(GMPE):
   superseded_by = TheNewGSIM
```

and each instantiation of the old GSIM class will warn the user pointing out
that it is deprecated and supersed by the new GSIM.

We used this mechanism to deprecate the GSIMs of Montalva et al (2016),
since there are new versions of them published in 2017 with revised
coefficients and implemented in hazardlib in this release.

We fixed the source group XML writer so that the `srcs_weights` attribute
is written only if they weights are nontrivial. If the attribute is missing
the weights are assumed to be trivial, i.e. equal to 1. This is always the
case except in the case of mutually exclusive sources which are used
in the Japan model.

We added the new scaling relationship: Thingbaijam et al. (2017).

We added date validation in `openquake.htmk.seismicity.utils.decimal_time`.

We removed excessive validation in the HMTK source model parser: now
when the name is missing the source model is still accepted, since this
is a common case and the name is not used by the calculators anyway.

A new correlation model `HM2018CorrelationModel` was contributed by
Pablo Heresi, as well as three new IMTs needed for this model.

WebUI/QGIS plugin
-----------------

There were various improvements to the WebUI. For instance now
all the WebUI outputs are streamed, so that the QGIS plugin can
display a nice progress bar while downloading them.

The biggest improvement is in the performance of extracting the
hazard curves (or maps) from the WebUI or the QGIS plugin.
For instance, for a continental scale calculation, with
engine 3.1 you might have been required to wait around 20 minutes 
for the preparation of the hazard curves (or maps) plus 20 seconds 
to download them. Now you will just need to wait the 20
seconds of download time, depending on the speed of your internet connection.

Implementing such improvements required changing the internal storage
format of hazard curves and hazard maps. That means that you cannot
export calculations performed with previous version of the engine.

Moreover, now the WebUI now displays some information on the size of the stored
output, when possible. This is not the same as the size of the file that
will be downloaded, since it depends on the chosen output format (XML
outputs will be larger than CSV outputs) but it is still useful information.
For instance if you see that the stored GMFs are 100 GB you might think twice
before trying to download them. The size appears as a tooltip when hovering
with the mouse over the output name in the WebUI and it is also available
in the QGIS plugin and in calls to the URL `/v1/calc/list`.

We added some additional information to the "Aggregate Loss Curves" output
(`units`, `return_periods` and `stats`) so that they can be plotted
nicely using the QGIS plugin.

There is now a new entry point in the REST
API `/v1/calc/XXX/extract/event_based_mfd` to extract the magnitude-frequency
distribution of the ruptures of an event based calculation. This entry
point will be accessible in the future to the QGIS plugin.

We added indexes to the engine database and now the queries on it are
a lot faster: this makes a difference if you have a database with
thousands of calculations.

Bug fixes
---------

We fixed a bug with the CTRL-C: now you can kill a calculation with a
single CTRL-C, before you had to press it multiple times.

Some users reported an annoying permission error on Windows, when trying to
remove a temporary file after the end of a calculation. We fixed it.

There was an encoding error on Windows when reading the exposure: we
fixed this, since the encoding is known (UTF-8).

There was a long standing bug in `classical_damage` calculations: even
if fragility functions for multiple loss types were defined, only the
`structural` loss type was computed. Now this has been fixed.

Exporting the GMFs from a scenario calculation would sometimes fail in the presence
of a filtered SiteCollection: this has been fixed now.

We fixed a bug in the command `oq engine --delete-calculation` which now
removes the specified calculation correctly.

There was a rare splitting bug causing some event based calculations to
fail for sources splitting into a single subsource.

We reduced the error "corner points do not lie on the same plane" to a mere
warning.

We fixed an `OverflowError` when sending back from the workers more than
4 GB of data: now the error message returns back to the user and does
not get lost in the celery logs.

Additional checks
-----------------

We added a check so that the flag `optimize_same_id_sources` can be turned on
for classical and disaggregation calculations only.

We improved the exposure XML parser: now an incorrect exposure with an invalid
node

```xml
<costTypes name="structural" type="aggregated" unit="USD"/>
```
will raise a clear error message.

We added a `LargeExposureGrid` error, to avoid mistakes when the engine
automatically determines the grid from the exposure. For instance the
exposure for France may contain assets in French Polynesia, causing a
huge grid to be built. This situation is now flagged as an error.

We added an extra check on the source model logic tree parser; a logic tree
like the following

```xml
            <logicTreeBranchSet uncertaintyType="maxMagGRAbsolute"
                                applyToSources="1"
                                branchSetID="bs7">
                <logicTreeBranch branchID="b71">
                    <uncertaintyModel> 7.7 </uncertaintyModel>
                    <uncertaintyWeight>0.333</uncertaintyWeight>
                </logicTreeBranch>
                <logicTreeBranch branchID="b72">
                    <uncertaintyModel> 7.695 </uncertaintyModel>
                    <uncertaintyWeight>0.333</uncertaintyWeight>
                </logicTreeBranch>
                <logicTreeBranch branchID="b73">
                    <uncertaintyModel> 7.7 </uncertaintyModel>
                    <uncertaintyWeight>0.334</uncertaintyWeight>
                </logicTreeBranch>
            </logicTreeBranchSet>
```
will be rejected because it makes no sense to have the same value (7.7)
repeated twice. The `uncertaintyModel` values must be unique within
a branchset.

We added a check for duplicated branch IDs in the GSIM logic tree file.

We raised the length limit in the source IDs from 60 characters to 75
characters: this was needed to run the US14 collapsed model.

We moved the check on the maximum number of sites (65,536) and maximum
number of IMTs (256) in event_based calculations right at the
beginning, to avoid performing any calculation in unsupported
situations.

We removed a check on the Uniform Hazard Spectra: now UHS curves with a
single period are valid, but a warning will be logged. This was requested
by our Canadian users.

We added a check on the intensity measure types in the case of scenario
calculations starting from a ShakeMap, because the ShakeMap could miss
some of the IMTs required by the vulnerability/fragility functions.

New configuration parameters 
-----------------------------

In the section `[distribution]` of the global configuration file
`openquake.cfg` there is a new parameter `multi_node` which by
default is `false`. You should change it to `true` if you are installing
the engine on a cluster, otherwise you will get a warning.

There are three new parameters in the `job.ini` file.

The `minimum_magnitude` parameter allows to discard all the ruptures
below a given threshold, thus making a calculation faster.

The `hypo_dist_collapsing_distance` parameter allows to discard all
the ruptures more distant than the given distance. This feature applies to point
sources, multipoint sources and are sources; it works by taking the
hypocenter distribution and discarding all the ruptures except the first one.

The `nodal_dist_collapsing_distance` parameter works similarly to the
`hypo_dist_collapsing_distance`, but it acts on the nodal plane distribution.

By discarding all the ruptures over the collapsing distances,
a calculation can become a lot faster without losing precision.
For instance, we had a real calculation for Canada with area sources
with a nodal plane distribution of length 12 and an hypocenter distribution
of length 4: this approximation made the calculation 12 x 4 = 48 times
faster.

Note that we do not provide any facility to determine the appropriate
collapsing distances to use: this is not easy and it is left for the
future.

oq commands
-----------

There are two new `oq` commands, useful for advanced users.

`oq check_input` checks the validity of the input files: you can give
to it a `job.ini` file or a zip archive containing the `job.ini`
it. It uses exactly the same checks as the engine, but it does not run
a calculation.

`oq plot_memory <calc_id>` plots the memory allocated by the given calculation.
This works only on a single machine and not on a cluster. It is useful to
compare the memory consumption of a given calculation depending on the
configuration parameters.

Since the source models are read in parallel, the command `oq info
--report` will be a lot faster than before in large source models
split in several files. It will also use less memory. This makes it
possible to estimate the size of extra-large models without running
them.

Internals
---------

As usual, there was a lot of work on the internals of the engine that
is not directly visible to the users but paves the way for changes
that are in anticipated in future versions.

In particular there was a substantial effort on the parallelization
framework; the engine is now able to express tasks as generator
functions, potentially saving a lot of memory, but the feature is not
used in the calculators yet. We did also some experiments with [dask](
http://dask.pydata.org/en/latest/).

We started a project to make some important class of sources
serializable to HDF5, in particular MultiPointSources and
nonparametric gridded sources. The benefits will be visible only
in the future.

We improved the documentation and the [FAQ page](
https://github.com/gem/oq-engine/blob/master/doc/faq.md).

Finally, there was a lot of work on the packaging (new Python 3.6,
new h5py 2.8, work on Windows, MacOS and Linux packages).

Deprecations
------------

Python 3.5 has been deprecated and the engine will stop working with
it in the next release. This is of interest for people developing with
the engine and hazardlib, because they should be ready to migrate to
Python 3.6. For the other users nothing will change since the engine
packages and installers include Python 3.6 already, starting from this
release.

Ubuntu Trusty (14.04) is deprecated and from the next release we will
stop providing packages for it. The reason is that Trusty is reaching
the [end of its life](https://wiki.ubuntu.com/Releases) and will not be supported even by Canonical. It
will still be possible to install and use the engine on Trusty, but
not with the packages.
