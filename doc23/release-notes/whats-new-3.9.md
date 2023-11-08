Release notes for the OpenQuake Engine, version 3.9
===================================================

This is a major release featuring several new optimizations, features and bug
fixes. Over 320 pull requests were merged.

For the complete list of changes, see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.9/debian/changelog

## Changes in behavior

There are a couple of important changes in engine 3.9 that *must* be signaled:

1. there is no automatic reduction of the GMPE logic tree anymore: potentially,
   this can cause the generation of redundant outputs
2. the `pointsource_distance` approximation now replaces planar ruptures
   with pointlike ruptures: this can produce differences in the hazard curves

In both cases the engine raises warnings asking the user to take
action if problems are identified. Both changes were motivated by the request of
making the engine less magic. They are fully documented here

https://github.com/gem/oq-engine/blob/engine-3.9/doc/adv-manual/effective-realizations.html

and here:

https://github.com/gem/oq-engine/blob/engine-3.9/doc/adv-manual/common-mistakes.rst#pointsource_distance

## Logic trees

Most of the work on this release went into a deep refactoring of the
logic tree code. From the user perspective the most notable change is
the time needed to parse and manage the source models, which has been
substantially reduced. This is particularly visible in the case of the
complex logic trees used for site specific analysis (we are talking
about orders of magnitude speedups). For continental scale
calculations the speedup is very significant when running in preclassical
mode or for single site calculations, while it is not noticeable - 
compared to the total runtime - in the other cases.

The basic logic tree classes, as well as the code to
manage the uncertainties, have been moved into hazardlib. The change
makes it possible for a power user to introduce new custom
uncertainties with a little Python coding, whereas previously,
adding new uncertainties was extremely difficult, even for a core
developer. Users with an interest on such topics should
contact us and we can give some guidance.

The removal of the *automatic* reduction of the GMPE logic tree
feature allowed substantial simplifications and made it possible to
infer in advance the size of a calculation, thus giving early warnings
in the case of calculations too big to run. It is possible to
reduce the GMPE logic tree *manually*, by discarding irrelevant
tectonic region types (a TRT is irrelevant if there are no sources for
that TRT within the integration distance). The engine will tell you
automatically which are the irrelevant TRTs, even without running a
full calculation.

There is a new (and much requested) feature, the ability to add sources
to a source model as a special kind of uncertainty. The feature is
called `extendModel` and is documented here:

https://github.com/gem/oq-engine/blob/engine-3.9/doc/adv-manual/special-features.rst#extendmodel

A substantial amount of work made it possible collapse logic trees
programmatically. The feature is implemented but not exposed to the
final users (yet).

Even if the engine does not offer any built-in way to plot logic trees, an
example of how you can do it yourself by using the
[ete3](http://etetoolkit.org/) library has been added in
https://github.com/gem/oq-engine/blob/engine-3.9/utils/plot_lt

## New optimizations

There are several new optimizations and improvements.

The most impressive optimization is the enhancement of the point
source collapsing mechanism for *site-specific classical
calculations*.  This can easily give an order of magnitude speedup for
calculations dominated by point sources, i.e. most calculations. The
price to pay is a small reduction in precision, as discussed here:

https://github.com/gem/oq-engine/blob/engine-3.9/doc/adv-manual/site-specific.rst

There is a new demo (in demos/hazard/MultiPointClassicalPSHA) to
demonstrate the feature. For the moment, this feature should be regarded as
experimental and it is *not enabled* by default, unless you set some
parameters in the `job.ini`.

Classical calculations with few sites (meaning fewer than the
parameter `max_sites_disagg`, which has a default value of 10) 
have been optimized too. Not only they are faster, but they require 
less disk space to store the rupture information, since we are now 
compressing the relevant datasets. The change made disaggregation 
calculations faster and more efficient, with a reduced data transfer 
and a lower memory consumption.

Calculations with many sites have not been optimized per se,
but since the task distribution has been improved, avoiding corner
cases where the engine was producing too many tasks or not enough
tasks, it is likely that they will be faster than before. The changes
in the task distribution affect the classical, the disaggregation,
the event based and the ebrisk calculators.

The data transfer in ruptures has been reduced in the event based
and ebrisk calculator, thus saving memory in large calculations.

There were *huge* improvements in the calculation of aggregate loss
curves with the `event_based_risk` and `ebrisk` calculators. Now
they can be computed without the need to store intermediate
asset loss tables (one per each tag combination) and therefore the
required storage space has dropped drastically.

The UCERF calculators have been unified with the regular calculators:
the calculators `ucerf_classical` and `ucerf_hazard` are no more,
just use the regular `classical` and `event_based` calculators; now
they can manage UCERF calculations too. Since the task distribution
has improved, now classical UCERF calculations are a bit faster than
before (say 10-20% faster).

## New features

The disaggregation calculator can now compute the mean disaggregation,
if multiple realizations are specified by the user in the `job.ini`. This
is useful to assess the stability of the disaggregation results.

The ebrisk calculator accepts a new parameter called
`minimum_asset_loss`: by specifying it, losses below the threshold are
discarded in the computation of the aggregate loss curves. This does
not improve the speed of the calculation much, but saves a substantial
amount of memory. Notice that in the calculation of
average losses and total losses the parameter
`minimum_asset_loss` is ignored and losses are not discarded: the
results are exact. It is only the aggregate loss curves that
are approximated. The parameter is experimental and it is there for
testing purposes.

There is a new stochastic `event_based_damage` calculator, which for the moment
should be considered experimental. Specifications for this calculator
are listed in this issue: https://github.com/gem/oq-engine/issues/5339.
The `event_based_damage` calculator allows for the computation of
aggregated damage statistics for a distributed portfolio of assets starting 
from a stochastic event set, with an approach similar to the
`event_based_risk` calculator. Similar to the `scenario_damage`
calculator, the `event_based_damage` calculator also includes 
the ability to compute probabilistic consequences (such as
direct economic costs of repairing the damaged buildings, 
estimates of casualties, displaced households, shelter requirements, 
loss of use of essential facilities, amount of debris generated etc.),
given the appropriate input consequence models. If you
are interested in beta-testing this new calculator, we welcome you to
write to engine.support@openquake.org. 

In order to support the `event_based_damage` calculator, the
`scenario_damage` calculator has been updated. If the field `number`
in the exposure is an integer for all assets, the `scenario_damage` calculator
will employ a damage state sampling algorithm to assign a specific
damage state for every building of every asset. Previously, the 
`scenario_damage` calculator was simply multiplying the probabilities
of occurrence for the different damage states for an asset (gleaned from the
fragility model) by the `number` of buildings to get the expected number of
buildings in each damage state for the scenario. The old behavior is 
retained for exposures that contain non-integral values in the `number` field
for any asset.

Finally, there was work on a couple of new experimental features:

- amplification of hazard curves
- amplification of ground motion fields

These features are not documented yet, because they are not ready.
We will add information in due course.

## hazardlib

[Graeme Weatherill](https://github.com/g-weatherill) extended hazardlib 
so that it is possible to compute Gaussian Mixture Models in the standard deviation
(see https://github.com/gem/oq-engine/pull/5688).

Graeme also implemented Forearc/Backarc Taper in the SERA BC Hydro Model
(see https://github.com/gem/oq-engine/pull/5479), and updated the
Kotha et al SERA GMPE (https://github.com/gem/oq-engine/pull/5475)
and the Pitilakis et al. Site Amplification Model
(https://github.com/gem/oq-engine/pull/5732).

[Nick Horspool](https://github.com/nickhorspool) discovered a typo 
in the coefficient table of the GMPE of Youngs et al (1997) that was 
[fixed](https://github.com/gem/oq-engine/pull/5700).

The INGV contributed three new GMPEs with scaled coefficients, Cauzzi (2014)
scaled, Bindi (2014) scaled and Bindi (2011) scaled
(https://github.com/gem/oq-engine/pull/5682).

[Kendra Johnson](https://github.com/kejohnso)
added the new scaling relationships Allen and Hayes (2017)
(see https://github.com/gem/oq-engine/pull/5535).

[Kris Vanneste](https://github.com/krisvanneste)
discovered a bug in the function `calc_hazard_curves` that was not working 
correctly in the presence of multiple tectonic region types. It has been fixed.

The AvgGMPE class was saved incorrectly in the datastore, causing issues
with the ``--hc`` option. It has been fixed. Moreover now it can be used
with a correlation model if all the underlying GMPEs can be used with a
correlation model.

## Outputs

The exporter for the `events` table has been changed. It exports
two new columns: `ses_id`, i.e. the stochastic event set ID, which is an integer
from 1 up to `ses_per_logic_tree_paths`, and `year`, the year in which
the event happened, an integer from 1 up to `investigation_time`.

The header of the exported file `sigma_epsilon_XXX.csv` has changed,
to indicate  that the values correspond to inter event sigma.

`.rst` has been added to the list of default formats: this means that
now the `.rst` report of a calculation can be exported directly.

The `dmg_by_asset` exporter for `modal_damage_state=true` was buggy, causing
a stddev column to be exported incorrectly. It has been fixed.

There were a few bugs in the `tot_losses` and `tot_curves` exporters in
event based risk calculations which have been fixed (a wrong header and
an inconsistency with the sum of the aggregate losses by tag).

When computing loss curves for small periods the engine was producing NaNs
if there were not enough events to produce reliable numbers. Such NaNs have
been replaced with zeros because the reason for having not enough events
was discarding the small losses.

There was an ordering bug in the exporter of the asset loss curves, causing
the curves to be associated to the wrong asset IDs, in some cases. It has
been fixed.

If `aggregate_by` was missing or empty, ebrisk calculations were exporting
empty aggregate curves files. Now nothing is exported, as it should be.

We fixed a bug with quotes when exporting CSV outputs.

## Bug fixes

We fixed an encoding issue on Windows, so that the calculation descriptions
where incorrectly displayed on the WebUI for UTF8 characters.

We fixed a memory issue in calculations using the `nrcan15_site_term`
GMPE: unnecessary deep copies of large arrays were made and large
calculations could fail with an out of memory error.

[Avinash Singh](https://github.com/AvinashSingh786) pointed out that the
`bin_width parameter` was not passed to
`openquake.hmtk.faults.mtkActiveFaultModel.build_fault_model` in
the Hazard Modellers Toolkit. 
[Graeme Weatherill](https://github.com/g-weatherill) fixed the issue
(https://github.com/gem/oq-engine/pull/5567).

There was a bug when converting USGS ShakeMap files into numpy arrays, since
the wrong formula was used. Fortunately the effect on the risk is small.

The zip exporter for the input files was incorrectly flattening the tree
structure: it has been fixed.

There was a BOM bug (Byte Order Mark: a nonprintable character added by
Excel to CSV files) that was breaking the engine when reading CSV exposures:
it has been fixed.

The procedure parsing exposure files has been fixed and now
`Exposure.read(fnames).assets` returns a list of `Asset` objects
suitable for a line-by-line database importer.

The extract API for extracting ruptures was affected by an ordering bug,
causing the QGIS plugin to display the ruptures incorrectly in same
cases.

We fixed a type error in the command `oq engine --run job.ini --param`.

## New checks

We added a limit on the maximum data transfer in disaggregation, to avoid
running out of memory in large calculations.

We added a limit of 1,000 sources when `disagg_by_src=true`, to avoid
disastrous performance effects.

Setting a negative number of cores in the `openquake.cfg` file, different
from -1, it is now an error.

If the GSIM logic tree file is missing a TRT, a clear error is raised
early.

A source with multiple `complexFaultGeometry` nodes is now invalid, while
before all the nodes except the first were silently discarded.

Instead of silently truncating inputs, now `baselib.hdf5.read_csv`
(used for reading all CSV files in the engine) raises an error when
a string field exceeds its expected size.

Instead of magically inferring the intensity measure levels
from the vulnerability functions, now the engine raises a clear error
suggesting to the user the levels to use.

Case-similar field names in the exposure are now an error: for instance
a header like `id,lon,lat,taxonomy,number,ID,structural` would be an
error since `id` and `ID` are the same field apart from the case.

There is a clear error when instantiating `hazardlib.geo.mesh.Mesh` with
arrays of incorrect shape.

There is a clear error message if the enlarged bounding box of the
sources does not intersect the sites, which is common in case of
mistakes like inverting longitude with latitude or using the exposure
for the wrong country.

## Warnings

Now we raise a warning when there is a different number of levels per IMT.
This helps finding accidental inconsistencies. In the future the warning
could be turned into an error.

We are logging an error message when the bounding box
of a source exceeds half the globe, which is usually a mistake.

We added a warning on classical calculations too big to be run,
based on the product (number of sites) x (number of levels) x 
(max number of gsims) x (max source multiplicity).

We improved the error message for duplicated sites, as well as the
error message for duplicated nodal planes.

We improved the error message in case of CSV exposures with wrong headers.

## oq commands

`oq check_input` was enhanced to accept multiple files. Moreover, it
checks complex fault geometries and prints an error if it discovers
issues, such as the error "get_mean_inclination_and_azimuth() requires
next mesh row to be not shallower than the previous one". Finally,
when applied to exposures, `oq check_input` warns about assets with field
number >= 65536.

`oq reduce_sm` has been parallelized, so it is much faster when there
are multiple files in the source model.

`oq reduce` has been renamed as `oq sample`, to avoid any confusion with
`oq reduce_sm`.

`oq info` has been fixed to work on a zmq cluster, thus avoiding the
dreaded "zmq not started" error. Moreover, `oq info source_model_logic_tree.xml`
now works correctly even for source models in format NRML/0.4. Finally,
the commands `oq info --<what>` have been changed to `oq info <what>` with
`<what>` one of "calculators", "gsims", "imts", "views", "exports",
"extracts", "parameters", "sources", "mfds".

`oq compare -s` has been enhanced to accept a file name with the control sites,
i.e. the sites where to perform the comparison, as a list of site IDs.

`oq run` has now an option `--calc-id`: this is useful when starting a bunch
of calculations in parallel, to avoid race conditions on the datastores.

`oq postzip` sends a zip file to the WebUI and start a calculation;
it also works on a `job.ini` file, by first zipping the associated files.

`oq plot sources?` now works with all kind of sources, except UCERF sources.
For nonparametric sources it is a lot faster than it was, since now it tries
to display only the convex hull of the underlying ruptures. It also has new
features, such as the ability to specify the sources to plot, an upper limit
on the number of sources and the kind of sources to plot.

`oq plot disagg?` has been fixed (there was an annoying
`ValueError: too many values to unpack (expected 1)` when specifying the
poe_id parameters).

`oq plot` accepts a flag `-l, --local` meaning that the local engine server
should be used instead of completely bypassing the server. This is useful
when debugging the web API.

`oq workerpool` immediately starts an oq-zworkerpool process.

## Other

As always there was a lot of documentation work on the 
[advanced manual](https://github.com/gem/oq-engine/tree/engine-3.9/doc/adv-manual)
and on the [Risk FAQ page](https://github.com/gem/oq-engine/blob/engine-3.9/doc/faq-risk.md). 
We also improved the docs about the parallelization 
features of the engine (i.e. openquake.baselib.parallel).

We added a demo for nonparametric sources, one for multipoint sources
and we extended the event based hazard demo to use sources of two different
tectonic region types.

In production installations, if the zmq distribution mode is enabled,
the zmq workers are now started when the DbServer starts. This makes
configuration errors (if any) immediately visible in the DbServer logs.

The configuration file `openquake.cfg` has been cleaned up, by removing
a couple of obsolete parameters.

The module `openquake.hmtk.mapping` has been removed. The reason is that it
depended on the library basemap, which has been abandoned years ago by its
authors and it is basically impossible to install on some platforms, notably
macOS.

The usage of .yml files in the HMTK has been deprecated. In the next release
they will be replaced with .toml files.

There was a lot of activity to make the engine work with Python 3.8
and the latest versions of the scientific libraries. Currently the
engine works perfectly with Python 3.6, 3.7 and 3.8; internally we are
using Python 3.7 for production and Python 3.8 for testing. 
The Linux packages that we are distributing are still using 
Python 3.6, but in the next version of the engine we will fully 
switch to Python 3.8.

The QGIS plugin can now interact with an engine server using a
version of Python with a different pickle protocol, like Python 3.8.
