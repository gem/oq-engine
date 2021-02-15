This is a major release featuring several optimizations, new features,
and a bug fixes. Over 400 pull requests were merged.

For the complete list of changes, see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.11/debian/changelog

Here are the highlights.

# New features and optimizations

The classical PSHA calculator has a brand new optimization called
*point source gridding*, based on the idea of using a larger grid
for sites distant from the point sources. The feature is still
experimental and not enabled by default, but the first results are
very encouraging: for instance, the Australia model can be made 3
times faster without changing the results much.  The point source
gridding optimization is documented here

https://docs.openquake.org/oq-engine/advanced/point-source-gridding.html

and you are invited to try it.

There is a syntax to perform sensitivity analysis, i.e. to run
multiple calculations with different values of one (or more)
parameters with a single command. This can be used to test the
sensitivity to the parameters used in the point source gridding
approximation, but in general it works for any global parameter.
An example is the following:

# add this to the job.ini to run 2 calculations
sensitivity_analysis = {'maximum_distance': [100, 200]}

Finally, the engine can now automatically download and run
calculations from an URL containing a .zip archive. For instance

```
$ oq engine --run "https://github.com/gem/oq-engine/blob/master/openquake/server/tests/data/classical.zip?raw=true"
```

# Hazard calculators

The memory occupation of classical PSHA calculations has been reduced
significantly; for instance the Australia model that used to require
over 100 GB of RAM on the master node now runs with less than 32 GB
of RAM. We also optimized the calculations of the probability of
exceedence by carefully generating arrays with a size smaller than the
CPU cache.

The scenario and event based calculators have been fully unified.  As
a consequence of the unification, the parameter controlling the
rupture seeds is now always `ses_seed`. Before it was `ses_seed` in
event based but `random_seed` in scenario, confusing since
`random_seed` was also used for the logic tree sampling.
Moreover we changed the algorithm generating the rupture seeds,
so the engine will not produce identical GMFs as before, but they will
still be statistically equivalent.

A time-honored performance hack in event based calculations with full
enumeration has been finally removed: now the number of generated ruptures
is consistent with the case of sampling. That avoids a lot of confusion at
the cost of producing more ruptures and being a bit slower than before.

We improved the task distribution in event based calculations that some times
was producing too many tasks and some times was too slow in sending the
tasks to the workers.

We changed the task distribution in scenario calculations: now we
parallelize by `number_of_ground_motion_fields` if there are more than
`max_sites_disagg` sites (i.e. 10 sites). This improved a lot the performance
in cases with many thousands of sites.

The scenario and event_based calculators (including `ebrisk`) now generate
and store as a pandas-friendly dataset the average GMF, averaged on the events.
This is useful for plotting and debugging purposes.

We reduced the data transfer due to the GMPEs: in some models (i.e. Europe
with the Kotha GMPEs) that makes a huge difference (10x in data transfer)
while for most models you will not see any sensible difference.

The preclassical calculator has been made faster and improved to
determine the source weights more reliably, thus reducing the slow
task issue in classical calculations. Now all sources are split and
prefiltered with a KDTree in preclassical.

We changed the semantic of the `pointsource_distance` approximation:
before it was ignoring finite size effects, now it is just averaging them.

For calculations with few sites now store the classical ruptures in a
single pandas-friendly dataset, including information about the
generating source.

We worked at the UCERF calculator, doing some minor optimizations, but a
lot more could be done to improve its performance.

# Risk calculators

The `scenario_risk` and `event_based_risk calculator` have been unified, as
well as the `scenario_damage` and `event_based_damage` calculators.

We added the ability to compute aggregate losses
and aggregate loss curves to the event based and scenario calculators,
even if they are less efficient than the ebrisk calculator. We optimized
terribly the case of many tags so that now it is possible to aggregate
by asset ID or by site ID with

  aggregate_by = id  # compute loss curves by asset
  aggregate_by = site_id  # compute loss curves by site
  
up to many thousands of assets/sites. We also reduced substantially
the memory occupation while computing the aggregate curves.

There was a huge speedup in ebrisk calculation due to the removal of
zero losses (7x in a calculation for Canada).
Added portfolio_damage_error view.

A regression entered in the `classical_risk` and `classical_damage`
calculators in engine 3.10 causing an increase of the data transfer
in hazard curves. That was killing the performance in the case of
calculations with many thousands of sites. It is fixed now.

The risk model is now stored in a pandas-friendly way; that improves by
two orders of magnitude the saving time in calculations with many thousands
of vulnerability/fragility functions.

dd_data is now pandas-friendly.

We fixed a bug in the calculation of averages losses in scenario_risk
calculations in presence of events with zero losses that were incorrectly
discarded.

Now `ignore_covs = 0` effectively set all the coefficients of variation
to zero even when using the Beta distribution.

The CSV exporters have been extend to save pandas DataFrame, thus improving
the speed of several exporters. Moreover various exporters have
been changed in order to unify the agg_losses-XXX outputs between ebrisk,
event_based_risk and scenario_risk.

# Logic trees

We made the engine smarter in the presence of different sources with
the same ID, which are unavoidable in presence of nontrivial logic trees.
Now internally the engine uses an unique ID. For instance in the case
of two different sources with ID "A", the engine will generate two
IDs "A;0" and "A;1". As a consequence, the information about the sources
can be stored in a pandas-friendly dataset `source_info` with an unique index
`source_id`.

Whe changed the internal storage of the PoEs in classical
calculations to allow a substantial optimization of the performance and
memory occupation of calculations with particularly complex logic
trees, like the South Africa (ZAF) model. While at it, we fixed a bug
in the sampling logic affecting the ZAF model in engine 3.11.

We added a new type of uncertainty for the seismic sources
called `TruncatedGRFromSlipAbsolute`.

We changed the string representation of the realizations to make it
more compact (before it was practically impossible to print out the
realizations for models like ZAF since the strings were too long).

We added a check on valid branch ID names: only letters, digits and the
caracter "-", "_" an "." are accepted.

# hazardlib/HTMK

We introduced a new MFD parameter slipRate.
Implemented AvgPoeGMPE.

M. Pagani introduced a new distance called  'closest_point'. He also
added a method to create a `TruncatedGRMFD` from a value of scalar seismic
moment.

We introduced a KiteSurface and and KiteFaultSource.

Richard Styron introduced a Tapered Gutenberg-Richter MFD, closely
following the implementation in the USGS NSHMP-HAZ code.

The `ModifiableGMPE` was enhanced with new methods set_scale_median_scalar,
set_scale_median_vector, set_scale_total_sigma_scalar,
set_scale_total_sigma_vector, set_fixed_total_sigma,
set_total_std_as_tau_plus_delta, add_delta_std_to_total_std.

Viktor Polak contributed the GMPE Parker et al (2020).
He also contributed the Hassani and Atkinson (2020) GMPE and added a new
site parameter `fpeak`. Finally he contributed the GMPEs Chao et al. (2020)
and Phung et al. (2020).

Laurentiu Danciu and Athanasios Papadopoulos contributed several
intensity prediction equations for use in the Swiss Risk Model.
The new IPEs refer to models obtained from the ECOS (2009), Faccioli and 
Cauzzi (2006), Bindi et al. (2011), and Baumont et al. (2018) studies.
They also extended the ModifiableGMPE class to allow amplification of the
intensity of the parent IPE based on a new `amplfactor` site parameter.

G. Weatherill made some updates to the GMPEs used in the newest European
model ESHM20.

Claudia Mascandola contributed the GMPE Lanzano et al. (2019) and the
NI15 regional GMPE by Lanzano et al. (2016).

We added a classmethod `TruncatedGRMFD.from_slip_rate` and updated the I/O
routines to recognize the slip_rate parameter.

We changed the `SourceWriter` not to save the `area_source_discretization`
on each source when writing the XML files, otherwise the same parameter
in the `job.ini` file would be ignored.

# Bugs

The exporters for the hazard maps and UHS were exporting zeros in the case of
`individual_curves=true`. Fixed after the report by Jian Ma.

In presence of an unknown parameter in the `job.ini` file - typically because
of a mispelling - the log was disappearing.

The boolean fields `vs30measured` and `backarc` where not cast correctly
when read from a CSV field (the engine was reading the zeros as true values).

We fixed a wrong check raising incorrectly a ValuEError in the case of
multi-exposures with multiple cost types.

# New checks and warnings

We removed some annoyiung warnings in classical_damage calculations
in the case of hazard curves with PoEs == 1.
The engine now logs a warning in case of a suspiciously large seed dependency
in event based/scenario calculations.

Now we raise an early error if the parameter `soil_intensities` is set with an
amplification method which is not "convolution".

We raise an early error in case of zero probabilities in the hypocenter
distribution or the nodal plane distribution in the XML source files.

We added a check on the vulnerability functions
with the Beta distribution: the mean ratios cannot contain zeros unless the
corresponding coefficients of variation are zeros too.

We perform the disaggregation checks before starting the classical part of
the calculation, so the user gets an early error in case of wrong parameters.

The engine warns the user if it discover a situation with zero losses
corresponding to nonzero GMFs.

We now accept vulnerability functions for taxonomies missing in the
exposure: such functions are just ignored.

# oq commands

We changed a bit the command `oq workers`.
Renamed `oq recompute_losses` as `oq reaggregate` and made it to work
properly.
Enhanced the command `oq compare`.
We improved a fixed a few `oq plot` subcommands.
Enhanced `oq plot sources` to plot point sources and to manage the IDL.
We fixed a bug in `oq prepare_site_model` ` when `sites.csv` is
the same as the `vs30.csv` file and there is a grid spacing parameter.
The command `oq nrml_to` has been documented.

# WebUI/WebAPI/QGIS plugin

If the authentication is off now the WebUI shows
the calculations of all users and not only the ones of the current user.
Improved submitting calculations to the WebAPI: now they can be run on a
cluster, `serialize_jobs` is honored and the log level is configurable with
a variable `log_level` in the file `openquake.cfg`.

# Other changes

The flag `--reuse-hazard` has been replaced by a flag `-reuse-input`
that allows to reuse only source models and exposures. This is safer
than trying to reuse the GMFs, which should be done with the `--hc`
option instead.

The `num_cores` parameter has been moved from the job.ini to the
`openquake.cfg` file and now it works.

There was a lot of work on secondary perils, both on the hazard and on
the risk side, but this feature is still not ready.

# Packaging

We have now an universal installation script working on Linux, Windows and Mac
(see https://github.com/gem/oq-engine/blob/master/doc/installing/universal.md).
We upgraded h5py to version 2.10 (for performance improvements) and shapely
to version 1.7.1 (to support macOS Big Sur).
We provide Debian packages with Python 3.8.
