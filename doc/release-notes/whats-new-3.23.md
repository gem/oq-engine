Release notes v3.23
===================

Version 3.23 is the new Long Term Support (LTS) release after version
3.16 of two years ago. It features massive benefits in terms of
performance, especially for large models (for instance the USA
classical PSHA model is 3-4 times faster than it was in version
3.16), and includes many new features.

The complete set of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.23/debian/changelog

A summary of the most recent changes (i.e. with respect to version 3.22)
is given below.

Hazard
------

The new "Event Based from ruptures.hdf5" feature has been extended to
work with an user-provided site model, rather than using the stored
site model. Moreover it has been optimized to discard far-away ruptures
using the `query_ball_tree` spatial feature of scipy.spatial.KDTree,
with a huge performance improvement.

The `rupture_dict` dictionary of scenario calculations has been extended to accept
to the `msr` and `aspect_ratio` keys, which are used to customize
the generated planar rupture.

The preclassical calculator has been extended to work in absence
of sites: this is useful for source model processing tools such as
HAMLET. Moreover, it has been optimized to
parallelize better and now it can eun significantly faster (
for the USA model it runs 7 times faster then version 3.22, at least
for the parallel phase of the analysis).

The change comes together with a different way of grouping the
CollapsedPointSources and therefore the hazard curves obtained
when using the `ps_grid_spacing` approximation can be slightly
different than before. This is normal, since the `ps_grid_spacing`
approximation is subject to refinements in any new release.

The parameter `pmap_max_mb` has been raised by 4 times resulting
in up to a 10% speedup in classical calculations at the cost of a
slightly larger memory occupation.

The sourcewriter has been changed to store the `rupture_idxs` dataset
in compressed format. This is a huge improvement in models with a large
number of multifault sources and we saw a case where the size of the
HDF5 file containing the model shrunk down from 400 MB to 17 MB.

The GMPEs for the most recent New Zealand model (NZ_2022) had some
missing attributes, causing errors to be raised in calculations using
parameters like 'region', 'm_b', 'sigma_mu_model', 'sigma_mu_epsilon'
or site parameters like 'backarc'. This has been fixed by
[Chris Brooks](https://github.com/CB-quakemodel).

[Savvinos Aristeidou](https://github.com/Savvinos-Aristeidou)
contributed a new ANN-based GMPE in hazardlib,
named `aristeidou_2024`, and added a few new Intensity Measure Types:
FIV3, Sa_avg2, and Sa_avg3.

In the AELO web interface the vs30 input field has been enabled for ASCE7-22.

Risk
----

We continued the refactoring of the
[multi-peril risk framework](https://github.com/gem/oq-engine/issues/10162)
initiated in the previous release. The documentation about the obsolete format
for the consequence files has been removed and we updated the
consequence files in all of our tests. We also added a script
`utils/fix_consequences` which is able to fix old consequence files
using risk IDs instead of taxonomies (this happens in the presence of a taxonomy mapping).

Many consistency checks were added to the consequence files to make
sure that they contains taxonomy strings consistent with the exposure and
perils consistent with the vulnerability functions.

We added a new output "Aggregated Exposure Values", containing the
sums of the exposure values aggregated by the tags specified in `aggregate_by`.

We made it possible to compute quantiles in scenario risk calculations
by specifying for instance `quantiles = 0.05 0.95` in the job.ini file.
The quantiles are computed in the "post-risk" phase and stored in
`aggrisk_quantiles` for each aggregation tag.

We added an extractor for the `aggrisk_tags` quantity which can be
extracted as a pandas DataFrame or as a JSON: it contains information
about the aggregated exposure, the mean losses and the quantile losses
for each aggregation tag, as documented in
https://docs.openquake.org/oq-engine/master/manual/api-reference/rest-api.html#get-v1-calc-calc-id-aggrisk-tags .

This output is still experimental and may change in the future.

OQ-Impact Assessment platform
--------------------------------

The old project Aristotle (https://www.globalquakemodel.org/proj/aristotle)
has been subsumed into a new project called OQ-Impact which has all of its
features and some more.

The kind of features available depends on the user, with users of
level 2 (currently restricted to GEM personnel) having access to
everything, including the ability to upload custom ruptures and
perform scenario calculations. Users of level 1 can only run
scenarios starting from a ShakeMap ID while users of level 0 can only
see the results of scenarios shared by GEM staff.

We renamed everything which was user-visible, like the project name
displayed in the WebUI and the project name used in email
notifications. Moreover we renamed some templates and some of the
code.

We improved the logic for user registration.

We improved the visualization of the losses table and we added the ability
to visualize the `aggrisk_tags` output.

We fixed a minor bug with the timestamp in ShakeMaps.

We removed the 'Continue' button which made no sense in OQ-Impact mode.

We changed OQ-Impact calculations to use `aggregate_by = ID_1;OCCUPANCY` and
`quantiles = 0.05 0.95`.

Finally, now we give the user feedback through the WebUI if the
uploaded rupture XML is malformed.

Bug fixes and other
-------------------

There was a bug breaking the `avg_losses-rlzs` exporter due to the
fact that the full asset collection was stored instead of the reduced
asset collection. It has been fixed now.

In scenario calculations it is possible to specify the `gsim` directly
as a string, however there was a bug when using the full TOML syntax
and not simply the GMPE name. It has been fixed now.

Evi Riga reported a bug in `classical_damage` calculations with sampling,
causing a numpy broadcast error. This bug has been
[fixed](https://github.com/gem/oq-engine/pull/10326).

File-dependent GMPEs store the associated files in the datastore so
that if the calculation HDF5 file is moved into a different machine,
post-processing scripts can run there. However, due to a bug, the
GMPEs could not be instantiated in the postprocessing machine.  It has
been fixed now.

We added an optional parameter `minimum_engine_version` in the job.ini file,
which can be used to specify the minimum engine version needed to run the calculation.
