Release notes for the OpenQuake Engine, version 3.17
====================================================

Version 3.17 is the culmination of 5 months of work involving around 470
pull requests. It is aimed to users wanting the latest features
and maximum performance. Users valuing stability may want to stay with
the LTS release instead (currently at version 3.16.4).

The complete set of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.17/debian/changelog

A summary is given below.

## Disaggregation calculator

The disaggregation calculator has been deeply revised, by changing the
underlying algorithms and by making it possible to compute the average
disaggregation directly. For the first time it is possible to compute
the mean disaggregation for large models like Europe (with
10,000 realizations) without running out of memory and in a
surprisingly small amount of time (minutes on a cluster). The game
changer was computing the mean disaggregation in terms the rates and
not probabilities, since rates are additive and therefore the mean
calculation can be parallelized cleanly without the need to keep all
realizations in memory. This is why now the only statistics supported
in disaggregation is the mean and you cannot compute the quantiles.
Computing the standard deviation is possible with a memory-efficient
algorithm so that could be added in the future.

The changes have touched all kinds of disaggregation, including
epsilon_star disaggregation, disaggregation over multiple sites and
disaggregation by source. The disaggregation outputs are stored in a
different way and the exporters have been updated and optimized. The
CSV outputs have an additional column `iml`. We renamed the "by
TRT" disaggregation outputs and added a new output `TRT_Mag`. Models
with mutually exclusive sources (i.e. Japan) can now be disaggregated,
as well as models using the NegativeBinomialTOM temporal occurrence
model (i.e. the New Zealand model).

The disaggregation using the `poes_disagg` parameter has been unified
with the disaggregation based on the `iml_disagg` parameter. We fixed
a few bugs (for instance the disaggregation sometimes failed when
using the NGAEast GMPEs) and changed the binning algorithm for LonLat
bins. Since the algorithms have changed you will get (slightly)
different results. Also, now the default behavior is to compute the
mean disaggregation while before it was to compute the disaggregation
only for the realization closest to the mean hazard curve.

Moreover, we substantially changed the `disagg_by_src` feature. The pandas
dataframe stored under the name `disagg_by_src` has been replaced by
an `ArrayWrapper` called `mean_rates_by_src` and the documentation
changed accordingly. The new structure contains less information than
before (only the means) and in a different form (rates instead of
PoEs), however it is enough for the purpose of finding the most
relevant sources and it can be actually stored for all hazard models
in the mosaic, since it requires a lot less storage (like 10,000 times
less storage for the EUR model).

The AELO project required the ability to store disaggregation results
by source. This is why we added a new output
`mean_disagg_by_src` with its own CSV exporter. The AELO project
als required a deep refactoring of the logic tree processor,
to implement the ability to reduce a full logic tree to a specific
source. That was hard and time-consuming and may require further
work in the future.

Finally, we changed the task distribution to reduce data transfer in
disaggregation and ensure optimal performance in all cases.

## Classical PSHA

The major new feature in Classical PSHA is the ability to define
custom post-processors as documented in
https://docs.openquake.org/oq-engine/advanced/3.17/classical_PSHA.html#the-post-processing-framework-and-vector-valued-psha-calculations

We took advantages of this feature to reimplement the conditional
spectrum calculator as a post-processor. Vector PSHA is also
implemented as a post-processor, and so the AELO disaggregations by source.
Users can easily implement custom postprocessors by following the
examples in
https://github.com/gem/oq-engine/tree/engine-3.17/openquake/calculators/postproc

Apart from post-processors, we kept working on the calculator to make
sure that even the largest model on the GEM mosaic can run with a
limited amount of RAM. We also changed the internal `_poes` storage to
reduce the disk space occupation.

It is now possible to set at the same time both the `sites` parameter
and the `site_model_file` parameter; previously it was an error, now
instead the closest vs30 parameters are used for the specified sites
and the zpt site parameters are recomputed. The change was required
in the context of the AELO project.

Finally, we needed a new feature to support the 2018 USA model. In that
model some multipoint sources use the equivalent distance
approximation, while others do not. To manage such situations we added
a new parameter in the job.ini, `reqv_ignore_sources`, which is a list
of IDs for the sources that should not use the equivalent distance
approximation.

## Event Based Hazard

The mechanism to generate ruptures in event based calculations has
been changed and now different ruptures will be sampled with respect
to the past. There is not only a change in the random seed generation
algorithm but also a substantial change of approach: starting from
engine 3.17 ruptures are *first sampled and then filtered* which is
the *opposite* order with respect to the previous versions. The previous
order was more efficient but it was making it impossible to define a
meaningful rupture ID. The problem is documented in detail in
https://docs.openquake.org/oq-engine/advanced/3.17/event_based.html#rupture-sampling-how-to-get-it-wrong

Here we will just note that previous versions of the engine had a
sequential rupture ID, exported in the file `ruptures.csv`, but was
not usable, because by changing by a little the minimum magnitude or
the maximum distance the IDs would refer to totally different
ruptures. Moreover, there was no easy way to export a rupture given
the rupture ID. All this has changed now, and the rupture ID does not
depend on the details of the filtering anymore; as a consequence it is
finally possible to disaggregate the GMFs (and the risk) by rupture, a
much desired feature.

The command to extract a single rupture is as simple as

`oq extract ruptures?rup_id=XXX`

and there is an associated HTTP API.

The new rupture ID is a 60 bit integer, with the
first 30 bits referring to the index of the source generating the
rupture and the second 30 bits referring to the index of the rupture
inside the source. Sources containing more than 2^30=1,073,741,824
ruptures are now rejected. Notice that this is not a limitation, since
you can always split a large source. Also, in the entire GEM mosaic
there is not a single source with more than 2^30 ruptures, so we did
not break any model.

We fixed sampling of the ruptures both in the case of
mutex ruptures (relevant for the USA model around the New Madrid cluster)
and in the case of mutex sources (relevant for the Japan model).
The sampling for mutex sources was extended to include the
`grp_probability` parameters, thus making it possible for the first
time to sample the Japan model correctly.

There was some work to improve the performance of multiFault sampling
by splitting the sources and thus parallelizing the sampling: the
improvement was spectacular in the USA model (over 100x on a machine
with 120 cores). Moreover, we strongly optimized the generation of
events from the ruptures, which now can be dozens of times faster than
before.

We improved the view `extreme_gmvs` to display the largest ground motion
values, and we added a new parameter `extreme_gmv` (a dictionary IMT->threshold)
to discard the largest GMVs on demand. This a feature to use with care and
not recommended: in presence of extreme GMVs one should fix the GMPE instead.

Finally, we added an output "Annual Frequency of Events" which can be exported
as a file `event_based_mfd.csv` with fields (mag, freq), which is
meant to be compared with the measured magnitude-frequency
distribution.

## Additions to hazardlib

The most important event in hazardlib was the porting of the GMPEs
required to run the Canada SHM6 model. The porting from the GMPEs used
in engine 3.11 was long and difficult, since there are many complex
GMPEs. In the process we discovered and fixed several subtle bugs. The
support for the Canada SHM6 is still considered experimental and you
should report any suspicious discrepancy with respect with a
calculation performed with engine 3.11.

Moreover there was work for supporting the release of the GEM 2023 Global
Hazard Mosaic. All the models were computed by converting the GMPEs with
nontrivial horizontal components to use the geometric average. That
involved specifying `horiz_comp_to_geom_mean = true` in the job.ini
file and required to fix a few GMPEs by adding the missing
`DEFINED_FOR_INTENSITY_MEASURE_COMPONENT` class attribute.

Apart from that, we added a parameter `infer_occur_rates` to speedup
rupture sampling in presence of multiFault sources. If you know that
the `probs_occur` in the multiFault sources are actually poissonian
(which is the common case) then you can set `infer_occur_rates=true`
and get an order of magnitude speedup in the sampling procedure.
This feature should be considered experimental at the moment and
by default is disabled.

Marco Pagani added the ability to pass the `kappa0` parameter
to the Lanzano 2019 GMPE.

As usual, some features were contributed by our users.

Chris DiCaprio from New Zealand added to the sourcewriter
the ability to add a prefix to MultiFaultSource IDs.

Julián Santiago Montejo contributed the GMPE Arteta et al. (2023)
and a bug fix the the GMPE Arteta et al. (2021).

Graeme Weatherill contribute a few bug fixes to various GMPEs,
already backported to engine 3.16 (https://github.com/gem/oq-engine/pull/8778).

## WebUI

In the context of the AELO project, we extended the WebUI to make it
possible to run single-site classical calculations including
disaggregation by `Mag_Dist_Eps` and disaggregation by relevant
sources for each site in the world. The calculator automatically
determine the model to use from the coordinates of the site and
recompute the site parameters starting from the user-provided
vs30. The performance has been tuned so much that a machine with only
16 GB and 4 cores is enough to run such calculations.

The WebUI was extended to log information on login/logout so that
tools like [fail2ban](https://github.com/fail2ban/fail2ban) can be
used to detect and stop denial-of-service attacks. We also worked on
the password-reset facility.

We also fixed the method `/v1/ini_defaults` returning a JSON with the
defaults used in the job.ini file. The issue was that it was
returning NaNs for some site parameters, i.e. not a valid JSON.
The solution was to not return anything for such parameters.

We introduced a READ_ONLY mode for the WebUI in situations when it is
advisable to remove the ability to post calculations (for instance
when the machine were the WebUI runs has not enough resources to spawn
calculations).

## Risk

We have a few new features in the risk calculators too.

The first one is the introduction of three new loss types and
vulnerability functions: `area`, `number` and `residents`. It is
enough to specify the corresponding vulnerability functions in the
job.ini file and the outputs relative to the new loss types will appear are
new columns in the loss outputs CSV files.

The `area` and `number` loss types are associated to the corresponding
fields in the exposure, while the `residents` loss type is associated
to the field `avg_occupants` in the exposure; if missing, it is
automatically computed as the mean of night, day and transit
occupants.

The second important new feature is disaggregation by rupture. The
command to give is simply `$ oq show risk_by_rup:structural <calc_id>`
which will return a DataFrame keyed by the rupture ID and with fields
including the total loss generated by the rupture and the parameters
of the rupture (magnitude, number of occurrences and hypocenter).
```
                        loss   mag  n_occ         lon        lat         dep
rup_id
52076478464016  3.091906e+12  6.60      9  128.401993  27.496000   68.199997
52037823758352  2.223281e+12  6.60      9  128.501999  27.596001   70.000000
```
We changed the (re)insurance calculator to read the deductible
field from the exposure: this gives a speedup of multiple orders of
magnitude in cases where you have thousands of assets all with the same
limit and different deductibles. This was the common case for our
sponsor SURA, so we switched from a slow and memory-consuming
calculation aggregating 6 million different policies to an ultra-fast
calculation aggregating only 6 policies.

At user request, we extended the
`total_losses` feature to include `business_interruption` and
we improved the error handling for reinsurance calculations.

There was also a major performance improvement when reading the
exposure. The issue was that we could not read the USA exposure (22
million assets) without running out of memory; now we can and the
exposure processor is three times faster. We also improved the event
based risk calculator to use very little memory on the workers even in
presence of a huge exposure.

There was a huge amount of work on the conditioned GMF calculator, for
which we included a [comprehensive verification test suite]
(https://github.com/gem/oq-engine/pull/8542)
based on the tests for the [ShakeMap code by USGS]
(https://usgs.github.io/shakemap/manual4_0/tg_verification.html)
We also changed the calculator to compute the GMFs only on the hazard sites
and not on the seismic stations.

At user request, we changed the behavior of `scenario_risk` calculations
to just print a warning in case of small hazard causing to losses, and not
to raise an error. This is consistent with the behavior of `scenario_damage`
calculations

Finally, we added an environment variable OQ_SAMPLE_ASSETS which is useful when
debugging calculations; for instance you can set OQ_SAMPLE_ASSETS=.001
to reduce a calculation by 1000 times, which will be much faster and easier
to debug.

## Bug fixes and new checks

We reimplemented the `minimum_magnitude` filter in terms of the
mag-dependent-distance filter, which can also be used to implement a
`maximum_magnitude` filter. The change eliminated a bunch of bugs and
corner cases that kept creeping in.

The engine was rounding longitude and latitude to 5 digits everywhere, except 
when generating a grid from a region; this has been fixed, and we have full
consistency now.

The `truncation_level` parameter is now mandatory in classical and
event based calculations. Before, if the user forgot to set it, a
default value of 99 was used, most likely not what the users wanted.

If the same parameter is present in different sections of the job.ini
file, now the engine raises an error.

If the user by mistake disable the statistics and does not specify
`individual_rlzs=true`, now gets an early error; before, the engine
was computing the individual realizations (which was an error).

If the exposure contains empty asset IDs, now the engine raises a clear
error.

If the site model file does not contain a required site parameter,
and the parameter is not set in the job.ini either, now a clear
error is used instead of using incorrectly a NaN value.

The New Zealand model uses the `CScalingMSR`
magnitude-scaling-relationship. That caused a surprising error when
using the `ps_grid_spacing` approximation due to the way the names of
the CollapsedPointSources were generated. This is now fixed since the
name does not contain anymore the name of the MSR.

It is now possible to use a percent character in the job.ini file
without interfering with the ConfigParser interpolation feature.

The GMF importer was failing to import GMFs in CSV format with a
`custom_site_id` field: this has been fixed.

In case of errors, the engine was printing the same traceback two or
even three times: this has been fixed.

## oq commands

We finally removed the command `oq celery`, since we have deprecated
celery for over 5 years. We also removed the obsolete references
to celery and rabbitmq in the engine documentation.

If a calculation ID is already taken in the database, now
`oq importcalc` raises a clear error before importing the HDF5 file.

We enhanced the command `oq sample` which is now able to sample
MultiPointSources too.

We extended the command `oq shakemap2gmfs`: on demand it can amplify
the generated GMFs depending on the ShakeMap vs30 or on the site model
vs30. See the `--help` message for more.

We refined the plotting command `oq plot event_based_mfd?` to plot
the magnitude-frequency distribution of the events in an event based
calculation.

We updated the command `oq plot uhs_cluster?k=XXX` to clusterize together
uniform hazard spectra given similar or identical hazard.

We added a new command `oq compare med_gmv <imt>` which is able to compare
the median GMVs between two calculation: this is useful when debugging
different versions of the engine.

We added a new command `oq reduce_smlt` which is able to 
reduce source model logic tree file and associated source mode files to 
a single source; this is useful when debugging AELO calculations.

We introduced a new family of commands `oq mosaic` with the following
two subcommands:

1. `oq mosaic run_site` to run a classical calculation on the given
   longitude,latitude site.

2. `oq mosaic sample_gmfs` to sample the ruptures on a given mosaic model

## Other

We extended the `sensitivity_analysis` feature to work also on file
parameters: for instance, you can provide multiple different logic
tree files to study the sensitivity from the logic tree.

There was a lot of work on documentation, both on the manuals (fully documented
`aggregate_by` and `ideductible` and `maximum_distance`), and the FAQs
(how configure multiple engine installations). We also improved the
installation instructions.

The full report output has been revised and now a compact
representation for the involved GMPEs is used when needed, to avoid
unreadable extra-long lines.
