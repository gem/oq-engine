Release notes v3.12
===================

The 3.12 release is the result of 6 months of work involving around
550 pull requests and touching all aspects of the engine.

Most of the work went into the optimization/enhancement of the
risk calculators - notably the event based risk and damage
calculators - and into a full rewrite of the GMPE library, 
described in this post:
https://groups.google.com/g/openquake-users/c/Tj5t1rJ7MX0/m/BHLrOPt6AQAJ

The complete list of changes is listed in the changelog:
https://github.com/gem/oq-engine/blob/engine-3.12/debian/changelog

New risk features
-----------------

### Flexible field names in exposure csv files

Before engine 3.11 the header names of the columns in a CSV exposure was
hard-coded and therefore one had to manually rename columns to strictly
match the names required by the engine from any pre-existing exposure files.
That often meant maintaning two exposure formats and required the exposure 
files for the engine to be regenerated after any changes in the
original one. Now a user can simply specify a mapping of the custom 
column names in their exposure files to the names required by the engine, 
in the exposure.xml metadata file. 

An example is given here:\
https://github.com/gem/oq-engine/blob/engine-3.12/openquake/qa_tests_data/scenario/case_16/Example_Exposure.xml

### Other exposure-related improvements

- The reading of CSV exposures has been optimized by using pandas.

- We added an option to ignore encoding errors by skipping any
offending characters. The reason is that often exposures are a
patchwork of CSV files of unknown encoding. `ignore_encoding_errors = true`
should be used only as a last resort: if possible, you should
convert all of your exposures into UTF-8, the only encoding supported
by the engine. However, in case there are a few bad characters in a
description or geographic region, it is better to have a mispelling in
the description or region name when exporting the results rather than
having the entire calculation fail.

### ShakeMaps enhancements

There was a nontrivial amount of work on the ShakeMaps module, mostly
contributed by [Nicolas Schmid](https://github.com/schmidni) of ETH Zurich.
Now it is possible to
read a ShakeMap from a custom URL (or local file) and not only from
the USGS site. It is also possible to read ShakeMaps in ShapeFile
format, as well as many other formats (.xml, .zip, .npy). Moreover we
now support the MMI intensity measure type if spatial and cross
correlation are disabled. The advanced manual has been updated with
the new features, see\
https://docs.openquake.org/oq-engine/advanced/risk-features.html#scenarios-from-shakemaps

### Risk calculations starting from GMFs in HDF5

It is now possible to run risk calculations starting from GMFs
in HDF5 format by setting the option

`gmfs_file = gmf-data.hdf5`

but that involves some limitations. The HDF5 format of the GMFs is meant
to be stable across engine versions. However, the details of the logic-
tree implementation change in every release. Therefore, the approach can only
work if risk calculations starting from GMFs in HDF5 format are
restricted to see a single realization, obtained by collecting together
all realizations. This is equivalent to using the new option

`collect_rlzs=true`

Notice that the results will be meaningful and corresponding
to mean results *only if* originally all the realizations have the same
weight, which is the case if the original hazard calculation was
using sampling of the logic tree.

Event based risk calculators
----------------------------

- The work on unifying the `scenario_risk`, `event_based_risk` and
`ebrisk` calculators - started in engine 3.11 - has been finally
completed. Thanks to this work the `ebrisk` calculator is now
deprecated. You should use the `event_based_risk` calculator instead,
since it is more efficient than `ebrisk` ever was. The trick was to
change `event_based_risk` to use the same distribution mechanism as
`ebrisk` (i.e. distribution by ruptures, not by site).

- The management of random numbers in risk calculations has been changed. 
In particular, previously, it was impossible to run even
medium-sized event based risk calculations if the vulnerability functions had
non-zero coefficients of variation, because all the time was spent
reading a huge matrix of epsilons which could be hundreds of GB in size.

Now the epsilons matrix has disappeared since the corresponding random
numbers (governed by the `master_seed` parameter) are generated
dynamically by using modern numpy features (i.e. the
`numpy.random.Philox` random number generator).

However, running extra-large event based risk calculations may still
impossible unless you set `ignore_master_seed = true`, which
effectively turns off the generation of the epsilons.

- The work on the risk random numbers allowed us to fix some long standing
bugs in calculations with vulnerability functions using the Beta distribution
(dist="BT"). In particular, the results are now independent from the
number of spawned tasks, and are the same both for `ebrisk` and `event_based_risk`.
Before engine 3.12 we were not able to ensure 100% replicability of results from
risk calculations using the beta distribution in the vulnerability functions.

- A lot of work went into estimating and saving the variance of the
losses due to the coefficients of variation, therefore, it is possible
to set `ignore_master_seed = true` for performance reasons but still
have an indication of the uncertainty. Such information is only
available by reading the event loss table with pandas and is not
exposed as a CSV file, due to the sheer amount of data involved.

- Aggregation by tag has been optimized - their calculation now utilizes all
available cores and a lot less memory - and is documented in the advanced
manual, see the section\
https://docs.openquake.org/oq-engine/advanced/risk.html#aggregating-by-multiple-tags

- Moreover, it is now possible to set the parameter\
\
`collect_rlzs = true`\
\
in the `job.ini` file. That makes the risk part of an event based risk
calculation even faster and more memory efficient than before, at the price of
losing information about the specific realizations.\
\
For continental scale calculations setting `collect_rlzs = true` can
make the difference between being able to run a calculation and being
unable to do so due to memory constraint or computational constraints.

- Finally the scenario from CSV ruptures calculators have been
extended to work with multiple TRTs.

Event based damage calculator
-----------------------------

We introduced an experimental `event_based_damage` calculator in the engine in v3.8. 
Now it has been rewritten, optimized, and extended,
so that it is possible to use it for very large calculations and to compute
generic consequences based on the damage tables, not only for economic losses.

In order to be efficient, some features had to be sacrified, and in
particular it is not possible to compute consequences for each
individual realization: we can can only compute means. This is
equivalent to using `collect_rlzs = true` in `event_based_risk`. To be
completely correct, it is actually possible to compute the
consequences for a specific realization, but it is inconvenient
since you have to manually change the logic tree until there is only
the desired realization.

If you want to see an example of usage of the calculator, you should
look at the EventBasedDamage demo:
https://github.com/gem/oq-engine/tree/engine-3.12/demos/risk/EventBasedDamage

The new EventBasedDamage also works in presence of a taxonomy mapping file, a
feature that was missing in the past. Currently the following generic
consequences are supported: "losses", "collapsed", "injured", "fatalities",
"homeless". Since the mechanism to add a new consequence is now quite simple,
more are expected to be supported in the future. You can print the updated
list of available consequences with the command

`$ oq info consequences`

New optimizations in the hazard calculators
-------------------------------------------

- We improved the rupture weighting algorithm, thus removing some
dramatic slow tasks in event based calculations.

- We also saved some preprocessing time by weighting the heavy sources
in parallel in event based calculations.

- We saved memory when generating PoEs in classical calculations and
we mitigated the slow task issue when using the point source gridding
approximation. 

- We also did some experiments with the optimizing compiler numba and
we were able to speedup significantly some parts of the engine - we measured
a 54x speedup when computing the mean hazard curves - but sadly not the
real bottlenecks. `numba` is not a dependency of the engine and
everything works without it. The plan is to keep it that way.

### Refactoring of the GMPE library

The GMPE library has been completely rewritten and the API for
implementing new GMPEs has changed significantly. That means that if
you have written a GMPE with the old API it will not work anymore once
you upgrade to engine 3.12: you will have to rewrite it. This is quite
simple is the GMPE is simple, but it can be quite difficult if the GMPE
depends from other GMPEs in complex ways. Should you encounter any
compatibility issue, please contact us.

On the bright side, if you are just using library GMPEs by calling the method
`.get_mean_and_stddevs`, your application should work exactly as
before. We tried very hard to keep backward compatibility as much as
possible.

As part of the refactoring, 15 GMPEs of the SHARE model have been
vectorized and are now a lot faster than before (up to 200x in single
site situations). The rest of the GMPEs have not been vectorized, so they
are slow as before. The good news is that with the new API it easy to
vectorize a GMPE and more are expected to be vectorized in the future.

Due to the refactoring work, many things have changed internally, and
are listed here for completeness sake:

- `hazardlib.const.TRT` is now an Enum class
- `hazardlib.imt.PGA`, SA and all other constructors are now factory functions
  and not classes
- there is a limit of 12 characters to IMT names
- multiple inheritance in GMPE hierarchies has been forbidden
- defining methods different from `__init__` and `compile` in GMPE classes
  is now an error
- a name convention on GMPE classes has been enforced: attributes starting
  with COEFF must be instances of the the CoeffsTable class, which has been
  refactored too

### Other updates to hazardlib

There was also a lot of activity not related to the refactoring:

- we fixed a bug in the Abrahamson et al. (2014) GMPE and updated the
  verification tables
- we added a `hazardlib.cross_correlation` module to compute the correlation
  between different intensity measure types
- we implemented MultiFaultSources, a new typology of sources to
  be used in UCERF-like models
- we improved the precision of site amplification with the convolution method
- we added more epistemic uncertainties to the logic tree module
- we fixed a few bugs in KiteSurfaces (having to do with NaN values)
- we added a classmethod `PlanarSurface.from_hypocenter`
- we updated the parameter DEFINED_FOR_REFERENCE_VELOCITY in a few GMPEs
 -we optimized the SiteCollection class and now unneeded parameters are
  not stored anymore; an example could be the parameter
  `reference_depth_to_2pt5km_per_sec` in a calculations with GMPEs that
  do not require it; same for the `reference_siteclass` and `reference_backarc`
  parameters
- we changed how the SiteCollection is stored so that it can be read
  with pandas
- we changed the signature of the functions `calc.hazard_curve.classical`
  and `calc.stochastic.sample_ruptures`

### New GMPEs

Finally, many new GMPEs have been contributed.

- [Graeme Weatherill](https://github.com/g-weatherill) 
has contributed the Abrahamson & Gulerce (2020) NGA
Subduction Model as well as the Ameri (2014) Rjb GMPE. Moreover, he
has updated the Atkinson (2015) GMPE in accordance with the
indications of the original author.  He also updated the
KothaEtAl2020ESHMSlopeGeology GMPE, following changes to the
underlying geology dataset.

- [Nico Kuehn](https://github.com/nikuehn) and 
[Graeme Weatherill](https://github.com/g-weatherill) have contributed the
NGA Subduction ground motion model of Si, Midorikawa and Kishida (2020)
as well as the Kuehn et al. (2020) NGA Subduction Model.

- [Stanley Sayson](https://github.com/stansays) contributed 
the Gulerce and Abrahamson (2011) GMPE
for the vertical-to-horizontal (V/H) ratio model derived using
ground motions from the PEER NGA-West1 Project.
Moreover he contributed the SBSA15b GMPE by Stewart et al. (2016)
vertical-to-horizontal ratio (V/H) for ground motions from the
PEER NGA-West2 Project, as well as the GMPE by Bozorgnia & Campbell (2016)
for vertical-to-horizontal (V/H) ratio. Finally he fixed a few bugs in
the Campbell and Bozorgnia (2014) GMPE.

- Chung-Han Chan and Jia-Cian Gao have contributed a couple of GMPEs
for the Taiwan 2020 hazard model (TEM): Lin2011foot and Lin2011hanging.

- [Pablo Heresi](https://github.com/pheresi) has contributed the Idini (2017) GMPE.

- [Cladia Mascandola](https://github.com/mascandola) has contributed 
the Lanzano et al (2020) GMPE and the Sgobba et al. (2020) GMPE.

- [Laurentiu Danciu](https://github.com/danciul) has contributed the Boore (2020) GMPE.

Bugfixes
--------

- We fixed a few bugs in the CSV exporters. First, the encoding was
not specified, thus causing issues when exporting exposure data on
systems with a non-UTF8 locale (affecting a Chinese user). Second,
the CSV exporters on Windows were not producing the right line ending.
Finally, we fixed some CSV exporters that were not generating the
usual pre-header line with the metadata of the calculation, such
as the date and the engine version.

- There was a bug in scenario damage calculations, happening (rarely)
in situations with very few events and causing an IndexError in the
middle of the calculation. This is fixed now.

- We fixed a subtle bug in risk calculations with a nontrivial taxonomy
mapping: loss curves could be not computed due to spurious duplicated
event IDs in the event loss table.

- We fixed a bug in the serialization of the gsim logic tree in the
datastore, preventing a correct deserialization due to missing branchset
attributes.

- We fixed a bug in the logic tree processing: the option
`applyToSources` did not work with multipoint sources, by not
modifying the parameters and by producing the same contribution for
each branch.

- We fixed the function `baselib.hdf5.dumps` that was generating invalid JSON
for Windows pathnames, thus breaking the QGIS plugin on Windows.

- We fixed a bug in the management of GMPE aliases; now the dictionary
returned by `get_available_gsims()` contains also the aliases. That means
that now the Input Preparation Toolkit (IPT) also work with GMPE aliases.

New checks and warnings
-----------------------

- Years ago we restricted the `asset_correlation` parameter to be 0 or 1.
Setting an unsupported value now raises a clear error early in the
calculation an not in the middle of it, also for scenario risk calculations.

- We added a check to forbid `-Inf` in the sources. This happened to people
generating the source model automatically, where the XML file contained
things like
 ```xml
 <truncGutenbergRichterMFD aValue="-Inf" bValue="0.90" maxMag="6.5" minMag="4.5"/>
 ```

- We added an early check to discover situations in which the user mistakenly
uses fragility functions in place of vulnerability functions or viceversa.

- We added a warning if extreme ground motion values (larger than 10g) are
  generated by the engine. This may happen for sites extremely close to
  a fault.

- The warning about discardable tectonic region types now appears in all
calculations, not only in classical calculations.

- A warning is now printed if the loss curves appear to be numerically instable.

- Setting a too large `area_source_discretization` parameter was
breaking the engine with an ugly error; now you get a clear error
message.

oq commands
-----------

- The command `oq checksum source_model_logic_tree.xml` was broken,
raising a TypeError. It is fixed now.

- The command `oq workers kill` (to be used on a linux cluster) now calls
`killall` and kills all processes of the user `openquake`, including possible
zombies left by an out-of-memory crash, so it is much better than before.

- We added a new kind of plot (`oq plot uhs_cluster`) displaying similar
uniform hazard spectra from different realizations clustered together.

- We added a new command `oq export disagg_traditional` to export the
disaggregation outputs in traditional format (i.e. Bazzurro and Cornell 1999),
where the probabilities sum up to 1.

- The command `oq --version` now gives the git hash if the engine was
installed with the universal installer using the `--version=master`
option.

Other changes
-------------

- As often is the case with every new release, the inner format of the
datastore has changed in several places, and in particular, the event
loss table has been renamed from `losses_by_event` to `risk_by_event`,
since this table can now also be populated by the event-based damage
calculator, with consequences other than economic losses.

- The XML exporter for the ruptures, deprecated years ago, has been finally
removed. You should use the CSV exporter instead.

- The experimental feature "pointsource_distance=?" has been removed. It was
complicating the engine without giving a significant benefit.

- The special feature `minimum_distance`
(https://docs.openquake.org/oq-engine/advanced/special-features.html#the-minimum-distance-parameter)
now works with a single parameter in the `job.ini` which is used for
all GMPEs.  This is simpler and more consistent than the previous
approach that required changing the gsim logic tree XML file by adding
an attribute to each GMPE.

- For single-site classical calculations now the engine automatically
stores individual hazard curves for each realization.

- The hazard curve and UHS exporters now export the `custom_site_id`
parameter if defined.

- We improved the universal installer, especially on Windows.

- We upgraded Django to release 3.2.6.

- We updated the documentation (including the API docs) and the demos.
