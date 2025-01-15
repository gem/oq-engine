Release notes v3.20
===================

Version 3.20 is the culmination of 3 months of work involving over 220
pull requests. It is aimed at users wanting the latest features, bug fixes
and maximum performance. Users valuing stability may want to stay with
the LTS release instead (currently at version 3.16.8).

The complete set of changes is listed in the changelog:

https://github.com/gem/oq-engine/blob/engine-3.20/debian/changelog

A summary is given below.

New Hazard Models
-----------------

Last year we integrated the UCERF3 model inside the USA model by
reimplementing it in terms of multifault sources. We recently realized
that (non-intuitively) in the case of few intensity measure types the
calculation was running out of memory, using more than 4 GB of RAM per
core.

Solving the issue required a lot of work (over 200 man-hours) on the
classical calculator, including changing the internal storage of the
multifault sources in HDF5-format, compressing the transferred data,
transferring 32 bit rates instead of 64 bit probabilities, storing the
rates more efficiently, changing the postprocessing phase producing
the statistical hazard curves by taking advantage of the tiling
functionality and more. Hower, not the memory usage of the classical
calculator, depending on the calculation, is down from 0% to 50%.

Moreover, we were able to add
support for the 2022 revision of the New Zealand National Seismic 
Hazard Model ([NZ NSHM 2022](https://nshm.gns.cri.nz/)), which
also features multifault sources. While the model had been implemented
with the OpenQuake engine from the very beginning, its calculation was
extremely challenging and required several tricks for it to run. 
It is only with engine 3.20 that the calculation runs out-of-the-box 
and efficiently.

Since we improved the way the logic tree is stored in memory and we
implemented a better algorithm for computing the means if the
parameter `use_rates` is set (we measured a 133x speedup in a
calculation with ~260,000 sites) we can now run
calculations with millions of realizations. Therefore, it is quite
possible to run the New Zealand model - which has "_only_" 979,776
realizations - on a single machine. Computing the quantiles is still
impossible in practice, since you will run out of memory during the
postprocessing phase.

hazardlib
---------

The major thing in hazardlib was a refactoring removing `**kwargs`
from the signature of hundreds of GMPEs. As a consequence, now each
GMPEs knows the arguments it requires and if there is a typo in the
gmpe logic tree file a clear error is raised. Before, any mispelled
parameter was silently ignored. In particular, we discovered that in
the seismic hazard model for Europe, the parameter
`theta6_adjustment` was mispelled as `theta_6_adjustment` and that
went unnoticed for years
([#9486](https://github.com/gem/oq-engine/issues/9486)).  Most sites
are unaffected by the parameter, but some are. If you have an incorrect
version of the EUR model now you will immediately get an error
```sh
ValueError: FABATaperSFunc.__init__() got an unexpected keyword
argument 'theta_6_adjustment' in file EUR/in/gmmLT.xml
```
that you can solve by renaming `theta_6_adjustment` -> `theta6_adjustment` in
the file `gmmLT.xml`.

We also fixed the passing of parameters in the `NRCan15SiteTerm`, without
any impact on the results, since currently all models in the GEM mosaic do not
require passing parameters to the underlying GMPE via the `NRCan15SiteTerm`.

[Marco Pagani](https://github.com/mmpagani) added a new uncertainty 
in the logic tree processor, called moment `maxMagGRRelativeNoMoBalance`; 
an example of usage is in the test logictree/case_84.

He also extended the `ChiouYoungs2014` class to accept many optional
parameters, notably `use_hw`, `add_delta_c1`, `alpha_nm`,
`stress_par_host`, `stress_par_target`, `delta_gamma_tab` as
specified by Boore et al. (2022).

[Fatemeh Alishahiha](https://github.com/FatemehAlsh) contributed a new class
`AbrahamsonSilva1997Vertical` adding a vertical component to the
classical Abrahamson Silva GMPE and also an entirely new class
`GhasemiEtAl2009` implementing the Ghasemi et Al. GMPE for Iran.

Risk
----

We saved a lot of memory and disk space in conditioned GMFs scenarios,
making them also faster in many situations. This is a HUGE improvement
since many calculations that before were impossible are now possible.
We also improved the error checking for calculations with too many sites.

We implemented a first version of Post-Loss Amplification (PLA). 
The feature is documented, but it is in the experimental stage for the moment.
See https://github.com/gem/oq-engine/issues/9633 for more.

We fixed the `avg_losses-stats` exporter in the case of a single realization
for classical_risk calculation: [#9579](https://github.com/gem/oq-engine/issues/9579)

Bug fixes
---------

We fixed a bug when importing a file `gmf_data.csv`: in rare situations
with filtered site collections one could end up with site IDs in
not present in the site mesh.

In the engine, longitude and latitude are rounded to 5 digits. However,
sometimes they were rounded by using `numpy.round` and sometimes by
using Python round. That causes surprises in rare situations, producing
a different a different rounding depending if the sites were listed
directly in the `job.ini` file or read from a `sites.csv` file.
This has been fixed.

We fixed a long standing bug, so that the full logic tree object could
not be properly serialized in the datastore in some cases, i.e. when modifying
`simpleFaultGeometryAbsolute`, `complexFaultGeometryAbsolute` and
`characteristicFaultGeometryAbsolute`). The bug was a low priority since
such features are not used in any hazard model in the mosaic, however
now it has been finally fixed.

Using some special characters in the branchID tags of the source model
logic tree caused some tricky errors, as it was happening in the New
Zealand model. We have solved the issue by raising an early error if any
of the forbidden characters `.:;` is found.

When using a magnitude-dependent maximum distance with a missing
tectonic region type, the engine was giving a fake error. Now the
engine simply ignores the missing tectonic region type if there are no
sources associated to it, consistent with the behavior of version 3.16.

The mixture-model feature (tested in classical/case_47) was introduced
4 years ago and nearly immediately broken by a refactoring since the
test was not actually testing due to a typo. The problem has now been fixed and
the feature is working as intended.

There was an error when running scenarios with a ModifiableGMPE over a
table-based GMPE, since the `mags_by_trt` dictionary was not passed properly.
It is now fixed.

Finally, we removed two error-prone caches for the gsim logic tree and
the exposure, by avoiding the need for them.

New checks
----------

In the presence of millions of assets and events, calculating the
average losses can send the server out of memory; there is now
an early check warning the user of the problem and suggesting a workaround.

If the user forgets to specify the `residents` field in the exposure `fieldMap`,
there was a clear error message but only after computing the GMFs, i.e. too
late. Now the error is raised before starting the calculation.

When a required site parameter is not provided, the engine is now raising
a clear error message instead of giving NAN results.

There were rare situations where complex fault sources were deemed
invalid even when correctly specified. This has been fixed in
https://github.com/gem/oq-engine/pull/9596.

If the user forgets to specify the gsim parameter or the gsim_logic_tree_file
parameter in a scenario calculation, he could get a misleading error message.
Now the message is very clear.

We added a check to forbid having `individual_rlzs=true` and
`collect_rlzs=true` at the same time. Before, `collect_rlzs` was
automatically set for sampling calculations and overriding
`individual_rlzs=true`, in a way very surprising for the final
user. Now he gets an error such as

```InvalidFile: you cannot have individual_rlzs=true with collect_rlzs=true```

The `classical_risk` and `classical_damage` calculators are able to
start from imported hazard curves stored as CSV files. Such files must
contain probabilities, i.e. floats in the range 0 to 1. However, that
was not checked, causing NaN values to be generated in the outputs.
Now the user gets a clear error message at import time.

Aristotle project
-----------------

[Aristotle](https://www.globalquakemodel.org/proj/aristotle) is a
project to provide Multi-Hazard advice to the European Research
Coordination Centre in case of disasters. Currently, it is in
a development/experimental status and it is meant to be tested
but not trusted.

To support the needs of the project, the WebUI has grown an
APPLICATION_MODE="ARISTOTLE" which allows users to submit a ShakeMap
ID and to produce the associated scenario risk outputs by using GEM's exposure,
vulnerability functions and ground motion models. The users are
automatically notified when the calculations are done (currently
for a single ShakeMap ID the engine can perform multiple calculations,
since the earthquake can affect countries with different taxonomy mappings).

In ARISTOTLE mode, a couple of simple plots are generated: for the
moment, one with the (geometric) average GMFs and one with the
assets. They are used for debugging and are subject to changes in future
versions of the tool.

The procedure for downloading the USGS rupture parameters has been enhanced
so that if the file "rupture.json" is missing (because the USGS has not
generated it yet) the "finite-fault" parameters are used instead.
Moreover, it is possible to upload a custom file `rupture_model.xml`,
if the user possesses additional or different information than the USGS
or is interested in trying alternative models.

`oq` commands
-------------

We added a command `oq mosaic aristotle`, which is used
to run multiple ARISTOTLE calculations in a batch in our
automatic tests.

We improved the commands `oq info imt` and `oq info gsim`: now it is
possible to specify the IMT/GSIM and get information about it (i.e. the
docstring of the corresponding class).

We improved the command `oq info mfd`, which is now able to also print
the docstring of the specified MFD class, and added a command `oq info msr`
with similar features for the MSR classes.

We improved the command `oq plot avg_gmf`, which is now also displaying
country borders. Moreover, it is not showing the seismic stations in case of
conditioned GMFs calculations, since they were confusing.

We fixed the command `oq zip` that was not zipping the exposure.csv files.

The command `oq show delta_loss` has been enhanced and documented in the manual.

We now raise a clear `NotImplementedError` when trying to convert
griddedSurfaces with the command `oq nrml to csv|gpkg`.

Documentation
-------------

There was a lot of work on the documentation, in particular about
Windows installations and event-based outputs, which were both
severely outdated.

Many features implemented years ago have been finally
documented, including a description of all site parameters, a description
of Gridded ruptures, an explanation of the disaggregation outputs and how
to convert them into the traditional Bazzurro and Cornell view.

A function `calc_gmf_simplified` has been added to explain how
GMFs are computed.

A demo ScenarioCase3 documenting the new feature `rupture_dict` (introduced
in engine-3.19) has been added.

Other
-----

There was as usual some work for the
[AELO](https://www.globalquakemodel.org/proj/aelo) project. In
particular, in AELO mode, we changed the hazard curves and UHS
exporters into a format more Excel-friendly, at user request.

We added to the WebUI the ability to disable the warning about
newer engine releases being available with a flag DISABLE_VERSION_WARNING
in ``settings.py``.

We added to the WebUI outputs page buttons to display ``avg_gmf``
plots for all the available IMTs. 

Finally, there were a couple of changes affecting development installations:

1. we introduced a maximum limit of 90 lines of code and 16 arguments per
function/method. The limits are enforced by the tests every time a
user makes a pull request to the engine repository. They are meant to
avoid excessive degradation of the code base quality.

2. at the start of the WebUI a warning is printed if the
installed dependencies are different from the expected ones, to point
out possible problems while developing.
