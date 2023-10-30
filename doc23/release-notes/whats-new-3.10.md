Release notes for the OpenQuake Engine, version 3.10
====================================================

This is a major release featuring several optimizations, new features,
and a bug fixes. Over 300 pull requests were merged.

For the complete list of changes, see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.10/debian/changelog

Here are the highlights.

## Disaggregation

There was a substantial amount of work on optimizing the
disaggregation calculator in the case of many sites and/or many
realizations. Now it requires a lot less memory and it is significantly
more performant than before (at least 3 times better then engine 3.9
in test calculations for Colombia and the Pacific Islands). However,
for single-site and single-realization calculations you will not see much
of a difference.

The distribution mechanism and rupture storage have been changed
(ruptures are now distributed and stored by magnitude), thus reducing
both the data transfer and the time required to read the ruptures. The
effect is spectacular (orders of magnitude) in large calculations.

The way disaggregation outputs are stored internally has changed
completely, resulting in speedups up to orders of magnitude in the
saving phase. Also, we are logging much less when saving the
disaggregation outputs. There was another huge speedup in the
extraction routines for all outputs, including the `disagg_layer`
output which is use by the QGIS plugin. Such output has been extended
to include IML information and more.

The `disagg_by_src` functionality, temporarily removed in engine 3.9,
has been re-implemented and there is a new extractor for it. However,
there are a couple of constraints: in order to use it, you must
convert the point sources of your model (if any) into multipoint
sources; moreover, the size of `disagg_by_src` matrix (num_sites x num_rlzs x
num_imts x num_levels x num_sources) must be under 4 GB.

If disaggregation by epsilon is not required and the parameter
`num_epsilon_bins` is incorrectly set to a value larger than 1, now
the engine automatically corrects the parameter (by warning the user),
thus saving a lot of wasted calculation time.

We fixed a bug for the case of zero hazard: having zero hazard
for a single return period caused the disaggregation to be zero for
all periods.

We fixed a subtle bug for magnitudes on the edge of a magnitude bin,
causing some small difference in the disaggregation by magnitude
outputs.

We changed the algorithm for the `Lon_Lat` bins, to make sure that
the number of bins is homogeneous across sites, thus changing the
numbers for the `Lon_Lat` disaggregation.

Setting both `rlz_index` and `num_rlzs_disagg` is now an error, since
the two options are mutually exclusive.

Setting `max_sites_disagg` to a value lower than the total number of
sites is now flagged as an early error (before the error was raised in
the middle of the computation).

We fixed the IML interpolation to be consistent with the
algorithm used for the hazard maps: the change may cause slight
differences in the numbers, in all kind of disaggregations except the
ones using the parameter `iml_disagg`. Moreover, the parameter
`poes_disagg` in the job.ini file is now deprecated and you can just use
the parameter `poes` used for the hazard maps.

## Multi-rupture scenarios

At the end of a year-long effort, we have finally unified the scenario
and event based calculators and introduced a full CSV format for the
ruptures, i.e. a format containing also the geometries.  The full CSV
format [is documented here](
https://docs.openquake.org/oq-engine/advanced/special-features.html#ruptures-in-csv-format).
It should not be confused with the old CSV format which is missing the
geometry information and therefore cannot be used to start scenario
calculations. The new format is for the moment experimental, not
guaranteed to stay the same in future releases.  It completely
supersedes the experimental TOML format for the ruptures introduced
some time ago and that now has been removed.

It is now possible to run a slow event based calculation,
export the ruptures in the full CSV format, trim the ruptures
according to some criterium (for instance consider only the ruptures
that dominate the risk and discard the irrelevant ones) and then
perform *fast* scenario calculation starting for the reduced
ruptures. This is of huge importance for any risk analyst.

Multi-rupture scenarios can also be used to study the uncertainties
involved in a single-rupture scenario calculation. For instance you
can change the parameters of the base rupture, generate a bunch of
ruptures and then run a single multi-rupture scenario
calculation. This is much more convenient than running multiple
independent calculations like it was necessary in the past.

## Risk calculators

A much requested feature from our users was the ability to compute
statistics for `scenario_risk` and `scenario_damage` calculations in
presence of multiple GMPEs. Now that is possible and it actually
enabled by default, as a consequence of the event_based/scenario
unification.

We optimized the `scenario_damage/event_based_damage` calculators for
the case of many sites by returning one big output per task instead of
thousands of small outputs. The effect is significant when there are
thousands of sites.

We reduced the time required to read the GMFs and we avoided sending
multiple copies of the risk model to the workers, resulting in a good
speedup for calculations with a large risk model.

Risk calculators are now logging the mean portfolio loss, for user convenience.

We added an exporter for the `src_loss_table` output giving the cumulative
loss generated by each hazard source.

We made more hazard and risk outputs readable by pandas. Since the GMFs
are readable with pandas we have removed the GMF npz exporter which was
slow and inconvenient.

We made the scenario damage and classical damage outputs consistent with the
event based risk outputs by removing the (unused) stddev field. See
https://github.com/gem/oq-engine/issues/5802.

The event based damage calculator, introduced experimentally in release
3.9, is now official.  We fixed a bug in the number of buildings in
the `no_damage` state, which was incorrect. We fixed
a bug in the calculation of the average damage, which is now
correctly computed by dividing by the investigation time. We restored
the ability to perform damage calculations with fractional asset
numbers, by using the same algorithm as in engine 3.8 and previous versions.
Finally, we added an official demo for the event based damage calculator
and we documented it in the engine manual.

## Other new features/improvements

The logic tree sampling logic has been revised and the seed algorithm
changed, therefore in engine 3.10 you should not expect to get the
same branches sampled as in engine 3.9. The changed was needed to
implement four new sampling methods which are documented here:
https://docs.openquake.org/oq-engine/advanced/sampling.html

The new sampling methods will receive more work and experimentation in the
future.

It is possible to introduce a ``custom_site_id`` unique integer parameter
in the site model. The most common use case for this feature is to
associate a site to a ZIP code when computing the hazard on a city.

The magnitude-dependent maximum distance feature has been restored and
it is documented here:
https://docs.openquake.org/oq-engine/advanced/common-mistakes.html#maximum-distance

The rupture-collapsing feature now works also for nonparametric ruptures.
It is still experimental and disabled by default.

The engine was parsing the `source_model_logic_tree` and the
the source models multiple times: it has been fixed.

There was additional work on the amplification of hazard curves with
the convolution method and on the amplification of GMFs. Various bugs
have been fixed, and we added an experimental and slow implementation
of the kernel method for computing PSHA using amplification
functions. Such features are still experimental.

We included in the engine some code to compute earthquake-induced
secondary perils, like liquefaction and landslides.  This part is
still in an early stage of development and will be extended/improved
in the future.

## hazardlib/HTMK

F. J. Bernales contributed the Gulerce et al. (2017) GMPE,
Stewart et al. (2016) GMPE, Bozorgnia & Campbell (2016) GMPE.

G. Weatherill contributed the heteroskedastic standard deviation model for
Kotha et al. (2020). He also fixed a bug in mixture models in logic trees
with multiple GMPEs and he added PGV coefficients to USGS CEUS GMPE tables,
where possible.

M. Pagani contributed a [ModifiableGMPE class](
https://docs.openquake.org/oq-engine/advanced/parametric-gmpes.html#modifiablegmpe)
which is able to modify the `inter_event` parameter of a GMPE. He also
contributed an implementation for the Zalachoris & Rathje (2019)
GMPE. Finally, he fixed a bug in the ParseNDKtoGCMT parser in the HMTK
and ported the method `serialise_to_hmtk_csv` implemented in the
corresponding class of the catalogue toolkit.

M. Simionato fixed a subtle bug that caused a syntax error when reading
stored GSIMs coming from subclasses of ``GMPE`` redefining
``__str__`` (signalled by our Canadian users).

The `sourcewriter` has been improved. Now it calls
`check_complex_fault` when serializing a complex fault source, so that
incorrect sources cannot be serialized, as it was happening before.
Moreover, it automatically serializes nonparametric `griddedRuptures`
in a companion HDF5 file with the same name of the XML file. The
source reader can read the companion file, but it also works with the
previous approach, when everything was stored in XML. Since
`griddedRuptures` are big arrays the serialization/deserialization in
HDF5 format is much more efficient than in XML format.

## Bugs

We fixed a serious numeric issue affecting classical calculations with
nonparametric ruptures. The effect was particularly strong around Bucaramanga
in Colombia (see https://github.com/gem/oq-engine/issues/5901). The
hazard curves were completely off and the disaggregation was producing
negative probabilities.

In some situations - for logic trees using `applyToSources` and sampling -
there was a bug so that the logic tree could not be deserialized from its
HDF5 representation in the datastore. That affected the calculation of
the hazard curves and maps.

We fixed an issue with `noDamageLimit` not being honored in continuous
fragility functions.

We fixed a h5py bug in large ShakeMap calculation, manifesting as the
random error `'events' not found`.

We fixed an issue withe `minimum_magnitude` parameter not being honored
in UCERF calculations.

We fixed a bug when a rupture occurs more than 65535 times, affecting
scenario calculations with a large number of simulations. Similarly,
the fields `year` and `ses_id` in the events table have been extended
to support 4-byte integers instead of 2-byte integers.

We fixed a bug affecting Windows users preparing CSV exposures with
Excel, which introduces a spurious Byte Order Mark (BOM).

We fixed a bug when saving arrays with string fields in npz format.

## New checks and warnings

Now the number of intensity measure levels must the same accross
intensity measure types, otherwise an error is raised. In the past
there was simply a deprecation warning.

We added a warning about suspiciously large complex fault sources, so that
the user can fix the `complex_fault_mesh_spacing` parameter.

We added a warning against numeric errors in the total losses for the
`ebrisk` and `event_based_risk` calculators, like "Inconsistent total
losses for structural, rlz-96: 54535864.0 != 54840944.0".

If a source model contains different sources with the same ID a warning
is now printed. In the future this will likely become an error and the source
model will have to be fixed with the command `oq renumber_sm`. Then the
source ID will become a true ID and it will become possible to implement
source-specific logic trees.

We added parameter a `max_num_loss_curves` with a default of 10,000. Without
this limit it would be easier for the user to accidentally generate millions
of aggregate loss curves, causing the calculation to go out of memory. You
can raise the limit, if you really need.

At user request, we raised the limit on the asset ID length from 20 to
50 characters.

We added a check for missing `intensity_measure_types` in event based
calculations, otherwise a calculation would complete successfully but without
computing any ground motion field.

## oq commands

`oq plot` has been improved for disaggregation outputs, making it possible
to plot all kinds of outputs and also to compare disaggregation plots.

We added a command `oq plot vs30?` to plot the vs30 field of the
site collection.

We added a command `oq nrml_to` to convert source models into CSV and/or
geopackage format. This is useful to plot source models with
QGIS and it is meant to replace the command `oq to_shapefile` which has
many limitations.

We added a command `oq recompute_losses <calc_id> <aggregate_by>`: this is
useful if you want to aggregate an ebrisk calculation with respect to
different tags and you do not want to repeat the whole calculation.

We fixed a 32 bit/64 bit bug in `oq prepare_site_model` affecting the case
when the file `sites.csv` is the same as the `vs30.csv` file.

The semantic of the command ``oq engine --run --reuse_hazard`` has
been changed: before it was finding an existing hazard calculation (if
any) from the checksum of the input files and using it, now it is just
reusing the cached source model, if present. The change was necessary
since the checksum of the calculation often changes between version;
moreover reusing the GMFs generated with a previous version of the
engine is often inconsistent, i.e. it will not give the same results
since the details of the seed generation may change.

The `oq engine` command has been enhanced and it is now possible to run
multiple jobs in parallel as follows:
```
$ oq engine --multi ---run job1.ini job2.ini ... jobN.ini
```
This is useful if you have many small calculations to run
(for instance many scenarios). Without the ``--many`` flag the
calculations would be run sequentially, as in previous versions of the engine.

## WebUI/WebAPI/QGIS plugin

When running a classical calculation with the parameter `poes`
specified, the engine now produces hazard maps in .png format that are
visible through the WebUI by clicking the button on the bottom left
side called "Show hazard map".  This is meant for debugging purposes
only, the recommended way to visualize the hazard maps is still to use
the QGIS plugin.

There is a new API for storing JSON information inside .npz files, which
is being used to store metadata. The QGIS plugin has been adapted to take
advantage of the new API and the command `oq extract` has been changed
to save in .npz format and not in .hdf5 format.

We changed the call to `/extract/events` to return only the relevant events,
i.e. the events producing nonzero GMFs, in case a `minimum_intensity` is
specified.

The `/extract/sitecol` API has been extended so that it is possible to
extract selected columns of the site collection, for instance
`/extract/sitecol?param=custom_site_id`, if a `custom_site_id` is defined.

## Packaging

We removed the dependency from PyYAML and added a dependency
for GDAL.
