This is a major release featuring several optimizations, new features,
and a bug fixes. Nearly 400 pull requests were merged.

For the complete list of changes, see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.11/debian/changelog

Here are the highlights.

# New features

The classical PSHA calculator has a brand new optimization called
*point source gridding*, based on the idea of using a raw grid of point
sources for distant sites and a fine grid for close sites.
The feature is still experimental and not enabled by default, but the
first results are very encouraging: for instance, the Australia and
Europe models can be made 3 times faster without changing the results
much.  The point source gridding optimization is documented here:

https://docs.openquake.org/oq-engine/advanced/point-source-gridding.html

and you are invited to try it.

There is also a new syntax to perform sensitivity analysis, i.e. to
run multiple calculations with different values of one (or more)
parameters. This can be used to test the sensitivity to the parameters
used in the point source gridding approximation, but in general it
works for any global parameter.  An example to assess the sensitivity
to the integration distance is the following:
```
sensitivity_analysis = {'maximum_distance': [200, 300]}
```
Finally, now the engine can automatically download and run
calculations from an URL containing a .zip archive. For instance

```
$ oq engine --run "https://github.com/gem/oq-engine/blob/master/openquake/server/tests/data/classical.zip?raw=true"
```

# Hazard calculators

The memory occupation of classical PSHA calculation has been reduced
significantly; for instance the Australia model that used to require
over 100 GB of RAM on the master node now runs with less than 32 GB
on the master node. We also optimized the calculation of the
probability of exceedence by carefully generating arrays with a size
smaller than the CPU cache (that can give a speedup of a factor 2 or 3).

A time-honored performance hack in event based calculations with full
enumeration has been finally removed: now the number of generated ruptures
is consistent with the case of sampling. That avoids a lot of confusion at
the cost of producing more ruptures and being a bit slower than before.

The scenario and event based calculators have been fully unified.  As
a consequence, the parameter controlling the
rupture seeds is now always `ses_seed`. Before it was `ses_seed` in
event based but `random_seed` in scenario, confusing the users since
`random_seed` was also used for the logic tree sampling.

We changed the algorithm generating the rupture seeds, thus the engine
will not produce the same GMFs as before, but they will still be
statistically equivalent.

We refined the "minimum_intensity" approximation, by making it more precise:
below threshold ground motion values are replaced with zeros only if they
are below threshold for *all* intensity measure types.

We improved the task distribution in event based calculations, because sometimes
it was producing too many tasks and sometimes sending the
tasks to the workers was excessively slow.

We changed the task distribution also in scenario calculations: now we
parallelize by `number_of_ground_motion_fields` if there are more than
`max_sites_disagg` sites (i.e. 10 sites). This improved a lot the performance
in cases with many thousands of sites.

The `scenario` and `event_based` calculators (including `ebrisk`) now generate
and store as a pandas-friendly dataset the (geometrically) averaged GMF
on the events. This is useful for plotting and debugging purposes.

We reduced the data transfer due to the GMPEs: in some models
(i.e. Europe with the Kotha GMPEs) that makes a huge difference (10x
in data transfer, with a significant reduction on the required RAM) while for
most models you will not see any sensible difference.

The preclassical calculator has been made faster and improved to
determine the source weights more reliably, thus reducing the slow
task issue in classical calculations. Now all sources are split and
prefiltered with a KDTree in the preclassical phase.

We changed the semantic of the `pointsource_distance` approximation:
before it was ignoring finite size effects, now it is just averaging them,
so it is much more precise than before.

For calculations with few sites now we store the classical ruptures in a
single pandas-friendly dataset, including information about the
generating source.

We worked at the UCERF calculator, doing some minor optimizations, but a
lot more could be done to improve its performance.

# Risk calculators

The `scenario_risk` and `event_based_risk calculator` have been unified, as
well as the `scenario_damage` and `event_based_damage` calculators, so do not
worry if when running a `scenario_risk` calculation the progress log will say
that you are running an `event_based_risk` calculation. The core calculation
is the same now.

We added the ability to compute aggregate losses to the scenario calculators
and aggregate loss curves to the `event_based_risk` calculator. Notice, however,
that they are less efficient than the `ebrisk` calculator.

We optimized the case of many tags so that now it is possible to
aggregate by asset ID or by site ID by setting in the job.ini file

  aggregate_by = id  # compute loss curves by asset
  aggregate_by = site_id  # compute loss curves by site

This works up to many thousands of assets/sites; before it was impossible due
to memory issues.

There was a huge speedup in large `ebrisk` calculations due to the removal of
zero losses (we measured a 7x speedup in a calculation for Canada).

The risk model is now stored in a pandas-friendly way; that improves by
two orders of magnitude the saving time in calculations with many thousands
of vulnerability/fragility functions.

The `scenario_damage` calculator is more efficient than before and it stores
the damage distributions in a pandas-friendly way. It also stores a
dataset `avg_portfolio_damage` useful for comparison purposes.

The CSV exporters have been updated to use pandas, thus improving the
performance. Moreover various exporters have been changed in order to
unify the aggregate losses outputs between `ebrisk`,
`event_based_risk` and `scenario_risk` calculators. The most notable
change is that the exporter for the loss curves aggregated by tag now
also exports the total loss curve (in the same file). Here is an example:

https://github.com/gem/oq-engine/blob/engine-3.11/openquake/qa_tests_data/event_based_risk/case_6c/expected/agg_curves_eb.csv

# Logic trees

We made the engine smarter in the presence of different sources with
the same ID, which are unavoidable in presence of logic trees changing
the source parameters. Now internally the engine uses an unique
ID. For instance in the case of two different sources with ID "A", the
engine will generate two IDs: "A;0" and "A;1". The information about
the sources is now stored in a pandas-friendly dataset `source_info`
with an unique index `source_id`.

Whe changed the internal storage of the PoEs in classical calculations
to allow a substantial optimization of performance and memory
occupation: this visible only in calculations with particularly
complex logic trees, like the South Africa (ZAF) model. While at it,
we fixed a bug in the sampling logic affecting the ZAF model in engine
3.11.

We changed the string representation of the realizations to make it
more compact (before it was practically impossible to print out the
realizations for models like ZAF since the strings were too long).

We added a check on valid branch ID names: only letters, digits and the
caracter "-", "_" an "." are accepted.

We added a new type of uncertainty for the seismic sources
called `TruncatedGRFromSlipAbsolute`. That required adding
a classmethod `TruncatedGRMFD.from_slip_rate` and to update the I/O
routines to recognize the `slip_rate` parameter.

# hazardlib/HTMK

We introduced a new MFD parameter `slipRate` and implemented a new GMPE
`AvgPoeGMPE` performing averages on the probabilities of exceedence:
this is an alternative approach to the `AvgGMPE`, which performs
geometric averages on the GMFs.

The `AvgGMPE`, introduced over an year ago, has been extended to work
also for scenario and event based calculations and has been documented here:

https://docs.openquake.org/oq-engine/advanced/mean-ground-motion-field.html

The `ModifiableGMPE` was enhanced with new methods set_scale_median_scalar,
set_scale_median_vector, set_scale_total_sigma_scalar,
set_scale_total_sigma_vector, set_fixed_total_sigma,
set_total_std_as_tau_plus_delta, add_delta_std_to_total_std.

Richard Styron introduced a tapered Gutenberg-Richter MFD, closely
following the implementation in the USGS NSHMP-HAZ code.

M. Pagani introduced a new distance called  'closest_point' and
a method to create a `TruncatedGRMFD` from a value of scalar seismic
moment. Moreover he introduced a KiteSurface class and and KiteFaultSource
class, which at the moment are still considered experimental.

Viktor Polak contributed the GMPE Parker et al (2020).
He also contributed the Hassani and Atkinson (2020) GMPE and added a new
site parameter `fpeak`. Finally he contributed the GMPEs Chao et al. (2020)
and Phung et al. (2020).

Laurentiu Danciu and Athanasios Papadopoulos contributed several
intensity prediction equations for use in the Swiss Risk Model.
The new IPEs refer to models obtained from the ECOS (2009), Faccioli and 
Cauzzi (2006), Bindi et al. (2011), and Baumont et al. (2018) studies.
They also extended the `ModifiableGMPE` class to allow amplification of the
intensity of the parent IPE based on a new `amplfactor` site parameter.

G. Weatherill made some updates to the GMPEs used in the newest European
model ESHM20.

Claudia Mascandola contributed the GMPE Lanzano et al. (2019) and the
NI15 regional GMPE by Lanzano et al. (2016).

We changed the `SourceWriter` not to save the `area_source_discretization`
on each source when writing the XML files, otherwise the same parameter
in the `job.ini` file would be ignored, which is normally undesirable.

# Bugs

A regression entered in the `classical_risk` and `classical_damage`
calculators in engine 3.10 causing an increase of the data transfer
in hazard curves. That was killing the performance in the case of
calculations with many thousands of sites. Fixed after the report by
EUCENTRE.

The exporters for the hazard maps and UHS were exporting zeros in the case of
`individual_curves=true`. Fixed after the report by Jian Ma.

In presence of an unknown parameter in the `job.ini` file - typically because
of a mispelling - the log was disappearing.

The boolean fields `vs30measured` and `backarc` where not cast correctly
when read from a CSV field (the engine was reading the zeros as true values).
Fixed after the report by Peter Pazak.

We fixed a wrong check raising incorrectly a `ValueError` in the case of
multi-exposures with multiple cost types.

We fixed a bug in the calculation of averages losses in
`scenario_risk` computations: events with zero losses that were
incorrectly discarded.

Now `ignore_covs = 0` effectively set all the coefficients of variation
to zero, even when using the Beta distribution, which was missing.

# New checks and warnings

We removed some annoying warnings in classical_damage calculations
in the case of hazard curves with PoEs == 1.

The engine logs a warning in case of a suspiciously large seed dependency
in event based/scenario calculations.

The engine raises an early error if the parameter `soil_intensities`
is set with an amplification method which is not "convolution".

The engine raises an early error in case of zero probabilities in the hypocenter
distribution or the nodal plane distribution in the XML source files.

We added a check on the vulnerability functions
with the Beta distribution: the mean ratios cannot contain zeros unless the
corresponding coefficients of variation are zeros too.

Now we perform the disaggregation checks before starting the classical
part of the calculation, so that the user gets an early error in case
of wrong parameters.

The engine warns the user if it discover a situation with zero losses
corresponding to nonzero GMFs.

We now accept vulnerability functions for taxonomies missing in the
exposure: such functions are just ignored. This is useful since it
means that a vulnerability model file prepared for a full exposure
can be used on a reduced exposure missing some taxonomy.

# oq commands

We replaced the command `oq workers inspect` with `oq workers status`.

We renamed `oq recompute_losses` as `oq reaggregate` and made it to work
properly.

We enhanced the command `oq compare` and extended it also to the `avg_gmf`
outputs.

We improved a fixed a few `oq plot` subcommands.

We enhanced `oq plot sources` to plot point sources and to manage the
internationa date line.

We fixed a bug in `oq prepare_site_model` ` when `sites.csv` is
the same as the `vs30.csv` file and there is a grid spacing parameter.

The command `oq nrml_to` has been documented.

# WebUI/WebAPI/QGIS plugin

If the authentication is off now the WebUI shows the calculations of
all users and not only the calculations of the current user.

We improved the submission of calculations to the WebAPI: now they can
be run on a full cluster, `serialize_jobs` is honored and the log level is
configurable with a variable `log_level` in the file `openquake.cfg`.

We updated the QGIS plugin to reflect the changes in the engine outputs.

# Other

The flag `--reuse-hazard` has been replaced by a flag `-reuse-input`
that allows to reuse only source models and exposures. This is safer
than trying to reuse the GMFs, which should be done with the `--hc`
option instead.

The `num_cores` parameter has been moved from the `job.ini` file to the
`openquake.cfg` file and now it works as expected.

There was a lot of work on secondary perils, both on the hazard and on
the risk side, but the feature is still not ready.

# Packaging

We have now an universal installer working on Linux, Windows and Mac
(see https://github.com/gem/oq-engine/blob/master/doc/installing/universal.md).

The universal installer is the only supported way to install the engine on Mac
and generic linux systems. In works by using a preinstalled Python, which can
be Python 3.6, 3.7. or 3.8. Python 3.9 is not supported; if you have an older
Python you can just install a newer Python and then the engine.

For Debian-based systems the universal installer works just fine, but we also
provides packages that include their own Python (version 3.8).

For RedHat-based systems we also provides packages that include their
own Python (version 3.6). Notice that due to the change of policy of
RedHat about the CentOS operating system, it is not clear if we will
keep supporting it with the packages, but the universal installer will
work.

We upgraded h5py to version 2.10 (for performance improvements) and shapely
to version 1.7.1 (to unofficially support macOS Big Sur). Notice that Big Sur
is not officially supported since we cannot test it, given that GitHub
Continuous Integration system does not support it yet. But we know of
some users for which the engine works on Big Sur, via the universal
installer. The new processor M1 is not supported.
