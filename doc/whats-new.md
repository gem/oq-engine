This is a major release featuring several optimizations, new features,
and a bug fixes. Over 300 pull requests were merged.

For the complete list of changes, see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.11/debian/changelog

Here are the highlights.

# New features

It is now possible to perform a sensitivity analysis, i.e. to run multiple
calculations with different values of one ore more parameters with a single
command.

ps_grid_spacing


It is possibile to set `num_cores` in openquake.cfg.

# Optimizations

We can now row Australia with 22 GB.

We optimized the GMF saving and export by using pandas.
Optimized get_poes.
Changed the source seed algorithm.

# Hazard calculators

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

We worked at the UCERF calculator.

# Risk calculators

scenario_risk and event_based_risk have been unified, so scenario_damage
and event_based_damage. As a consequence of the unification the parameter
controlling the rupture seeds is now always `ses_seed`. Before it was
`ses_seed` in event based but `random_seed` in scenario, confusing since
`random_seed` was also used for the logic tree sampling.

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
There was a lot of work on secondary perils.
Added portfolio_damage_error view.

A regression entered in the `classical_risk` and `classical_damage`
calculators in engine 3.10 causing an increase of the data transfer
in hazard curves. That was killing the performance in the case of
calculations with many thousands of sites. It is fixed now.

dd_data is now pandas-friendly.

We fixed a bug in the calculation of averages losses in scenario_risk
calculations in presence of events with zero losses that were incorrectly
discarded.

# Other new features/improvements

The flag `--reuse-hazard` has been replaced by a flag `-reuse-input`
that allows to reuse only source models and exposures. This is safer
than trying to reuse the GMFs, which should be done with the `--hc`
option instead.

There was a lot of work on secondary perils, both on the hazard and on
the risk side, but this feature is still not ready.

The `num_cores` parameter has been moved from the job.ini to the
`openquake.cfg` file and now it works.

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

We introduced a KiteSurface and and KiteFaultSource

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

Claudia Mascandola contributed the GMPE Lanzano et al. (2019).

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

# New checks and warnings

We removed some annoyiung warnings in classical_damage calculations
in the case of hazard curves with PoEs == 1.
The engine now logs a warning in case of a suspiciously large seed dependency
in event based/scenario calculations.

Now we raise an early error if the parameter `soil_intensities` is set with an
amplification method which is not "convolution".

# oq commands

Renamed `oq recompute_losses` as `oq reaggregate` and made it to work
properly.
Enhanced the command `oq compare`.
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
￼
# Packaging

We have now an universal installation script working on Linux, Windows and Mac
(see https://github.com/gem/oq-engine/blob/master/doc/installing/universal.md).
We upgraded h5py to version 2.10 (for performance improvements) and shapely
to version 1.7.1 (to support macOS Big Sur).
We provide Debian packages with Python 3.8.
