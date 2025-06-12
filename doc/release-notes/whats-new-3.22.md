Release notes v3.22
===================

Version 3.22 is the culmination of 3 months of work involving over 240 pull requests.
It is aimed at users wanting the latest features, bug fixes and maximum performance.
Users valuing stability may want to stay with the LTS release instead
(currently at version 3.16.8).

The complete set of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.22/debian/changelog

A summary is given below.

Note: this is the first release to support Python 3.12. Python 3.9
still works but we are not testing it anymore and therefore is
deprecated and will be forbidden in the future.

Rapid Impact Assessment Platform
--------------------------------

Most of the work went into our internal platform for Rapid Impact
Assessment. There is a single codebase with three different interfaces
depending on the kind of user:

- level 0 users: can only see results of computations performed by other users and shared
- level 1 users: can only perform ShakeMap-based damage and loss calculations starting from a ShakeMap ID
- level 2 users: can do everything including uploading custom ruptures, performing
                 calculations with conditioned GMFs, etc.

Many new features have been added, such as the possibility of sharing/unsharing calculations
from level 2 users to level 0 users. The level 2 interface is still under active development, with additional features/customizations being expected.

For ShakeMap-based calculations, by default the engine takes the most recent ShakeMap
if more than one version is available.

For rupture-based calculations the range of possible calculations has been extended significantly.
For instance, before calculations using GMMs defined only for the total
standard deviation `sigma` could not be performed. However now the engine
automatically sets the parameter `with_betw_ratio = phi/tau` to 1.7, so that
it is possible to define `phi` and `tau` starting from the total standard deviation.
In future versions we will give advanced users the ability to tune that parameter from the WebUI.

We manage properly several corner cases, like invalid ShakeMap ID,
missing station data files, station data files with incorrect data
and/or duplicated data, missing rupture file, case with point
ruptures, case with finite faults. The corner case of a job not
producing an aggrisk output (due to low hazard) is managed by
displaying an informative message instead of the loss table.

We fixed inefficiencies like `plot_assets` being called 3 times. Moreover,
internally we replaced the slow tests we had with fast tests.

Now we manage the `time_event` field, i.e. by looking at the date of the event
and at the local time zone we are able to determine if `time_event` is "day", "night"
of "transit"; moreover, the user can override this value with a dropdown menu
in the WebUI. That required a new dependency, the `timezonefinder` wheel.

On top of the page displaying the outputs for a calculation, we are
also reporting the date and time of the event and the amount of time
passed between the event itself and when the job results were
computed. This makes it easier to compare results computed before and
after new data become available from the USGS service.

Now an event affecting assets belonging to countries with
different taxonomy mappings can be managed with a single calculation, while before
a calculation per country had to be performed, which was vastly inefficient.

We extended the plotting facility to display not only the assets but also the rupture
if available, or the hypocenter if not available. Moreover for level 2 users
there is an advanced rupture plotter plotting the geometry of the rupture in 3D.
We experimented with plotting the names of the world cities.

We also did some work on downloading and displaying the
ShakeMap from the USGS website if available.

Level 2 users have a mosaic-model selector that can be used to select the 
hazard model to use in case there are multiple models covering the event.

There was also a substantial amount of backend work. For instance now Aristotle
calculations can be launched by a watchdog process killing calculations
which are too slow (according to the parameter `calc_timeout` in the
file `openquake.cfg`). This is a safety net against hanging calculations,
however the feature is still experimental and disabled by default.

We made sure that restarting the WebUI (typically after an out-of-memory
situation) correctly resets the status of the `executing` calculations to
`failed`, which was not the case in production mode with nginx.

There is also a monitoring mechanism (implemented with zabbix)
to signal out of memory situations and to manage them.

We added a SUPPRESS_PERMISSION_DENIED_WARNINGS flag to the WebUI settings
to avoid flooding the logs with unwanted messages.

We had to fix check on the dependencies at the WebUI startup to manage
properly dependencies without a `__version__` such as timezonefinder.

We are monitoring the time spent in downloads and in validations before starting
the calculation, making sure that the same files are not downloaded twice.

We are properly getting the parameters `from_email` and `reply_to email`
from the WebUI settings: they are used in password reset functionality.

New hazard features
-------------------

We extended the rupture exporter to also export the source IDs,
a much requested feature. This source IDs are also visible in the QGIS plugin.

We made it possible to store multiple logic trees in the same gsim_logic_tree file.

There is now a function `readinput.read_source_models` to read source model files
directly without calling `readinput.get_composite_source_model` which requires
the logic tree structure.

There is now an official and documented getter to read event based ruptures from the datastore,
the function `openquake.calculators.getters.get_ebruptures(dstore)`.

Global Stochastic Event Set
---------------------------

GEM plans to release a set a ruptures computed from the GEM mosaic
models covering the entire world, to be used as starting point to
compute ground motion fields and risk on specific regions.

In the context of this project, a new functionality has been
implemented in the event based calculator: it is now possible
to specify in the `job.ini` file a parameter
```
rupture_model_file = file-with-ruptures.hdf5
```
pointing to an HDF5 file containing a set of ruptures, site parameters
and Ground Motion Models and then perform the calculation of the GMFs.
The functionality is still experimental and the details will change
in the future.

In the context of this project we changed the storage of the rupture geometries
to use 32 bit floats instead of 64 bit floats, to save disk space.

hazardlib
---------

Our users at USGS requested an easy way to override coefficients in
the coefficient table, to be used in the NGA-West2 and NGA-Sub
ground motion models ([#10011](https://github.com/gem/oq-engine/issues/10011)).
We implemented a classmethod
`CoeffsTable.from_toml` to be used in code like the following
```python
self.COEFFS = self.COEFFS | CoeffsTable.fromtoml('''\
["SA(0.01)"]
a1 = 0.11
''')
```
which is overriding the coefficient `a1` for the IMT `SA(0.01)`.
Using this new feature the implementation of several GMMs in hazardlib
could be simplified and we refactored most of them.

A huge amount of work went into supporting the 2023 version of the
National Seismic Model for the United States. In particular, we
had to extend several GMMs to accept quite advanced basin terms.

After a general refactoring of the basin terms, we implemented the
USGS basin scaling for several GMMs such as the NGAWest2 GMMs and the
NGASub GMMs. For the NGASUB GMMs we also provided the ability to use
the M9 basin term. For the NGAWest2 GMMs we also implemented the
CyberShake adjustments. For the NGAEast GMMs we added the ability to
apply a period-dependent bias adjustment and the Coastal Plains
amplification adjustment.

[Ilaria Oliveti](https://github.com/IlariaOliveti) contributed a 
fix ([#9994](https://github.com/gem/oq-engine/pull/9994))
to the GMM Tusa, Langer, Azzaro (2019), since the coefficient table 
was inverting frequencies with periods.

Risk
----

Recently the USGS has extended the ShakeMap framework to
generate values for the IMT SA(0.6), accepting a GEM request. Thus we
extended the ShakeMap parser to take into account the new IMT when
available.

A large amount of work was devoted to the refactoring of the taxonomy
mapping and of the risk functions, i.e. vulnerability, fragility and
consequence functions, with the final goal of making it possible to support
multi-peril calculations ([#10162](https://github.com/gem/oq-engine/issues/10162)).

It is now possible to enter in the job.ini file something like the
following:

earthquake_fragility_file = {'structural': "fragility_model_structural.xml"}
liquefaction_fragility_file = {'structural': "fragility_model_liquefaction.xml"}
landslide_fragility_file = {'structural': "fragility_model_landslide.xml"}

and the same for vulnerability files. Consequence files have been extended
to accept a `peril` field so that it is possible to define different coefficients
for different perils.

The storage of the risk functions in the datastore has been extended
to manage multiple perils, and all risk calculators have been
refactored. During this process we removed the XML format for
consequences, which has been deprecated for over 4 years.
The method computing the consequences (`compute_csq`) has been
vectorized by asset with a good speedup.

Multi-peril calculations are still not ready for prime time and
more work will follow in the near future.

It is now possible to export the asset collection via the command
line, but not from the WebUI.  This is done on purpose, since the
exposure may contain sensitive data and it should not be exposed on
the Internet.

The parameter `gmfs_file` can now point to a list of .hdf5 files. This feature
is experimental and may be removed in the future. The issue is that it works
by importing the files into a single gmf_data dataset and that import can be
extremely slow, thus making the approach non-viable for large models.

Finally, we parallelized `get_mean_covs` when conditioning the GMFs, thus making
scenario calculations conditioned by seismic stations much faster. We also 
reduced the default value of the parameter `conditioned_gmf_gb` from 10 to 8 GB,
which is a good value if you have 32 GB of available memory and hope to avoid
out of memory situations.

Bug fixes
---------

The realizations exporter was truncating the name of the GMM
for scenario calculations. This is now fixed.

Large risk calculations (with over 1 million assets)
were failing on macOS with an HDF5 error 
([#10244](https://github.com/gem/oq-engine/issues/10244)). 
This is now fixed.

Event based calculations with very few events could fail due
to an implementation error in view delta_loss. This is now fixed.

Exporting the names of the assets could produce invalid unicode
strings due to the truncation to 100 characters. This is now fixed,
while keeping the truncation.

Calculations with characteristicFaultSource containing
griddedSurfaces failed when computing Rjb distances. This is
now fixed.

In `event_based` calculations starting from predetermined sites (i.e. with the
`--hc` option) now the sites are correctly associated to the parent sites.

New checks
----------

There is now an early check testing that the user `datadir` and `scratch_dir`
are writeable: this avoids hard to diagnose errors in HPC clusters.

It was very easy for a user to specify too many disaggregation bins
and thus causing an out of memory situation. There is now a check comparing the
available memory with the required memory and raising an error
*before* starting the calculation.

Some calculation may produce non-invertible hazard curves around a given PoE, causing bogus
numbers to be generated when disaggregating or when computing the uniform hazard spectrum.
There is now a check raising a clear error in such situations.

If the installation is missing the geospatial libraries, there is now a clear error message
point the user to the GEM wheelhouse. This happens to users not using
the GEM installer.

We improved the validation of OqParam objects and there is now a method
`oqparam.to_ini()` which is able to generate .ini files from a dictionary
of parameters, tested with the demos.

oq commands
-----------

We removed the redundant command `oq dbserver upgrade`; you should use
`oq engine --upgrade-db` instead.

We added the command `oq info usgs_rupture <ShakeMapID>` to download a rupture
from the USGS site, if available, and to display the associated parameters.

We added the command `oq info loss_types` showing the recognized loss types.

We extended the command `oq reset` to also cleanup the `custom_tmp` directory, if defined.

We fixed the calculation_mode in `oq sensitivity_analysis` which was stored incorrectly
as "custom".

We added the commands `oq plot ebruptures` and `oq filter_around`. Use the --help
flag to see their documentation.

QGIS plugin
-----------

We changed the workflow for displaying ground motion fields in the
plugin: before it was necessary to specify first the event and then
the realization, now we follow the reverse order. In this way
we avoid an event selector that could involve thousands of events.

When selecting the aggregate curves to visualize the plugin could not
manage properly the total loss curves
(i.e. structural+nonstructural+contents). This is now fixed.

Finally, we removed the plugin features related to social vulnerability and
integrated risk, since they were very infrequently used and hadn't been updated
in nearly a decade.
