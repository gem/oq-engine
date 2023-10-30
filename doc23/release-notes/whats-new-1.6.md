What's new in engine-1.6
========================

OpenQuake 1.6 is a major release and a big improvement with respect
to OpenQuake 1.5. Everybody is invited to upgrade,
by following the [usual procedure](Installing-the-OpenQuake-Engine.md).

New features of the OpenQuake Engine, version 1.6
---------------------------------------------------

1. The following six calculators have been completely rewritten and now
  use the HDF5 technology that in previous versions was still experimental:
  
  1. `scenario`
  2. `scenario_risk`
  3. `scenario_damage`
  4. `event_based_rupture`
  5. `event_based`
  6. `event_based_risk`

  As a consequence all such calculators are much faster and use a lot
  less memory than before. Even the disk space occupation has been
  drastically reduced, and large event based computations that before
  took terabytes of disk space now requires few gigabytes. The new
  calculators do not store their outputs in the
  database, but in an HDF5 file, named the datastore, located by
  default in ``$HOME/oqdata/calc_XXX.hdf5``.

2. The other calculators are unchanged; they are still using PostgreSQL.
  They will be replaced with HDF5-based versions in future releases of the
  OpenQuake Engine. For some calculator the HDF5-based implementation is
  already available in the engine and can be accessed by using the ``--lite``
  flag. For instance the classical hazard calculator is supported and can be
  run with
  
  ``$ oq-engine --lite --run job.ini``
  
  However the calculators accessible with the ``--lite`` flag should be
  considered experimental, previews of things to come, and they are still
  subject to change.

3. The new calculators can run with a single configuration file containing both
the hazard and the risk parameters. This is actually the recommended way to
run such calculators.

6. The `scenario_risk` and `scenario_damage` calculators now support multiple
GSIMs at the same time. This new functionality is documented in the [manual]
(http://www.globalquakemodel.org/openquake/support/documentation/engine/).

8. The `scenario_damage` calculator now supports multiple loss types at
the same time, just as the `scenario_risk` calculator. Again, see the [manual]
(http://www.globalquakemodel.org/openquake/support/documentation/engine/) for
the details.

7. The `event_based_risk` calculator has been optimized and enhanced. Now it
is possible to generate the full event loss table for each
asset and for each realization. Just set the configuration parameter
`asset_loss_table=True` (the default is False).

3. OpenQuake 1.6 supports officially the format NRML 0.5 for all risk
models. In OpenQuake 1.5 it was supported in a limited and experimental way
only for a subset of the vulnerability functions. Now all kind of risk
models are supported: vulnerability models, fragility risk models and
consequence models. Consequence models are brand new, introduced for
the first time in this release. All of that is documented in the [manual]
(http://www.globalquakemodel.org/openquake/support/documentation/engine/).
The new format is simpler than before
and more convenient to use, since the OpenQuake platform offers a web
tool to prepare risk models in NRML 0.5. Beware that the web tool does
not support validation of the risk models yet.

4. The validation of the risk models in the engine has been
improved. In particular now an user confusing a fragility model with a
vulnerability model or a consequence model or any other combination
will get a clear error message. Moreover, each risk model has a
`lossCategory` attribute which must be set consistently with the name
of the key in the job.ini file (see the [manual]
(http://www.globalquakemodel.org/openquake/support/documentation/engine/)
for the details).

6. Some work has been going on hazardlib, as usual, and you can have a
look at the [changelog]
(https://github.com/gem/oq-hazardlib/blob/engine-1.6/debian/changelog). The
most prominent feature is the introduction of new epistemic
uncertainties in the Source Model Logic Tree. Users are now able to
represent alternative geometries for the fault source typologies using
the following uncertainty model definitions:

  1. simpleFaultGeometryAbsolute - Replaces the simple fault geometry with the specified simple fault surface.
  2. complexFaultGeometryAbsolute - Replaces the complex fault geometry with the specified complex fault surface.
  3. characteristicFaultGeometryAbsolute - Replaces the characteristic fault geometry with the specified surface.
  4. simpleFaultDipRelative - Increases or decreases the fault dip with the specified value.
  5. simpleFaultDipAbsolute - Replaces the simple fault dip with the specified value.

  Also added is the ability to replace a given evenly discretised magnitude
  frequency distribution of a source in the logic tree using the
  `incrementalMFDAbsolute` option.

  Documentation on the usage of these features will be added in the forthcoming
  version of the manual.

7. We added an optional attribute `discretization` to the
area source geometry XML description: this means that it is possible to
specify a source-specific discretization step. This is useful in site specific
analysis: area sources with little impact on the site of interest can use
a large discretization step whereas the important area sources can use a
finer discretization step.

10. Two new GMPEs have been added to hazardlib: *Montalva et al. (2015)*
and *Tusa and Langer (2015)*.

11. The .rst report of a calculation has been improved. Now you can run
  
  ```bash
  $ oq-lite show <calc_id> fullreport
  ```
  
  to get information about a given calculation. This only works for the lite
  calculators.

12. Some small improvements to the Engine Web User Interface have been
made and this feature, first introduced in OpenQuake Engine 1.4, is
[now finally documented](https://github.com/gem/oq-engine/blob/engine-1.6/doc/server/OpenQuake-engine-webui.md).

11. We added a script `oq_reset_db` to drop and recreate the engine
database, as well as removing the datastore directories of all users.
This is meant to be used with care by system administrators. See the
instructions printed at the moment of running the script.

9. Countless small improvements and additional validations have been
added. This release has seen more than 150 pull requests reviewed and
merged.

Bug fixes and changes with respect to OpenQuake 1.5
----------------------------------------------------

1. The most important change is the support for NRML 0.5. A
  deprecation warning is printed every time you use a risk model in
  the NRML 0.4 format. To get rid of the warning you must upgrade the
  risk model files to NRML 0.5. There is a command to do that
  recursively on a directory.  Just write
  
  ``$ oq-lite upgrade_nrml <some-directory>``
  
  and all of your risk models will be upgraded. The original files
  will be kept, but with a `.bak` extension appended. Notice that you
  will need to set the `lossCategory` attribute to its correct value
  manually. This is easy to do, since if you try to run a computation
  you will get a clear error message telling which is the expected
  value for the `lossCategory` for each risk model file. For instance,
  you may get an error like this:

   ```python
   ValueError: Error in the file "structural_vulnerability_file=/home/.../vulnerability_model.xml": lossCategory is of type "economic_loss", expected "structural"
  ```
  
  The reason is that in NRML 0.4 the `lossCategory` attribute had no
  special meaning (actually it was ignored by the engine) whereas now
  there is a check on it. It must be consistent with the name of the
  variable used in the configuration file. In this example in the
  job_risk.ini file there was a line `structural_vulnerability_file=`,
  so the `lossCategory` is expected to be of kind `structural`. Edit the
  "vulnerability_model.xml" file and set the `lossCategory` attribute to
  the expected value. 

2. Valid loss categories are `structural`, `nonstructural`, `contents`,
`business_interruption` and `fatalities`.  There is now a strict check
on the categories, both in the risk model files and in the exposure
file. The check is disabled for NRML 0.4 files, so we are fully
backward-compatible.

3. If an user set the parameter `insured_losses=True` but the exposure
does not have the attributes `deductible` and `insuredLimit`, a clear
error is raised early.

4. In very rare circumstances the region constraint was not honored,
i.e.  assets very close to the border of region, but still outside, were
taken in consideration by the risk calculators. This has been fixed.

5. The engine had a self-termination feature: if the controller node
could not access the worker nodes, it assumed a failure in celery
and committed suicide if the configuration parameter 
`terminate_job_when_celery_is_down` was true. We removed such parameter
and such feature because it was too dangerous: sometimes celery was
up and running but incorrectly reported down because too slow to
respond, due to an heavy load. Now if celery appears to not respond
a warning is printed and that user has to see if celery is really dead
and in that case she can kill the computation manually.

6. We removed the epsilon sampling feature from the scenario_risk calculator:
it was a performance hack introducing a gratuitous seed dependency, now
unneeded thanks to the recent performance improvements.

7. We removed the `epsilon_sampling` parameter from the engine
configuration file `openquake.cfg`. Now the parameter can be managed
directly by the users, on a calculation-specific base, by setting it
in the `job.ini` file. This is only relevant for event based risk
calculations. In the future we will remove such parameter completely,
but first further optimizations of the event based risk calculator
are needed.

8. The `specific_assets` feature has been removed from the
`event_based_risk` calculator. It has become useless thanks to the
recent performance improvements. Use `asset_loss_table=True` instead.

9. The demos have been revisited and updated. Also their location has
changed for the users installing OpenQuake from the packages. Now they
are installed in `/usr/share/openquake/risklib/demos`.

10. In some cases the rupture tag was containing spurios commas, thus breaking
a CSV importer in the Risk Modeler Toolkit. This has been fixed.

12. When using a vulnerability function with a Probability Mass Function,
now it is possible to set the seed by changing the `random_seed` parameter
in the configuration file. Before the seed was hard-coded.

13. We introduced the concept of composite outputs, i.e. outputs that
can be exported to a zip file containing a set of output files. For
instance an event based risk calculation with two realizations and
four loss types in the past could print something like the following:

```
  id | output_type | name
 515 | Aggregate Loss Curve | aggregate loss curves. loss_type=contents hazard=430||gmf||GMF rlz-332
 514 | Aggregate Loss Curve | aggregate loss curves. loss_type=contents hazard=431||gmf||GMF rlz-333
 519 | Aggregate Loss Curve | aggregate loss curves. loss_type=fatalities hazard=430||gmf||GMF rlz-332
 518 | Aggregate Loss Curve | aggregate loss curves. loss_type=fatalities hazard=431||gmf||GMF rlz-333
 512 | Aggregate Loss Curve | aggregate loss curves. loss_type=nonstructural hazard=430||gmf||GMF rlz-332
 513 | Aggregate Loss Curve | aggregate loss curves. loss_type=nonstructural hazard=431||gmf||GMF rlz-333
 516 | Aggregate Loss Curve | aggregate loss curves. loss_type=structural hazard=430||gmf||GMF rlz-332
 517 | Aggregate Loss Curve | aggregate loss curves. loss_type=structural hazard=431||gmf||GMF rlz-333
```

Now it will print only one line:

```
  id | output_type | name
 419 | datastore | agg_curve-rlzs
```

When exporting the composite output, 8 XML files will be generated, in
the same format as before, plus a zip file containing all of them.
When using the Web UI the zip file will be available for download.

Support for different platforms
----------------------------------------------------

OpenQuake 1.6 supports Ubuntu from release 12.04 up to 15.10. 
We provide official packages for the long term releases 12.04 and 14.04.
We were able to extend the support to
Ubuntu 12.04 by backporting the package `python-h5py` from Ubuntu 14.04.
So *Ubuntu 12.04 is still supported, even if it is deprecated*.

We have official packages also for CentOS 7
and in general for [Red Hat Enterprise Linux clones].
(Installing-the-OpenQuake-Engine-from-source-code-on-Fedora-and-RHEL.md)

While the engine is not supported on Windows and Mac OS X, we are
happy to report that the underlying libraries and the
`oq-lite` command-line tool run just fine. We do not offer
any automatic tool to perform the installation, but there is
a [guide for Windows](Installing-OQ-Lite-on-Windows.md) and
a [guide for Mac OS X](Installing-OQ-Lite-on-MacOS.md) to help you
to install the necessary dependencies.

Other
------

The OpenQuake project is even
more open than before. From this release we are using
[GitHub](https://github.com/gem) as our
official bug tracker, which makes it easier to follow the development
process (before the bug tracker was Launchpad, which is less popular
than GitHub and not integrated with the code base). Moreover from this
release our libraries (both [oq-hazardlib](https://github.com/gem/oq-hazardlib)
and [oq-risklib](https://github.com/gem/oq-risklib)) are tested by
using a public Continuous Integration system,
[Travis](https://travis-ci.org/gem/). Before our
builds were internal on Jenkins and visible only to our staff.
The engine is still built with Jenkins for various technical reasons.

Finally, depending on the version of the HDF5 libraries you are using,
you may get a warning like the following:

```
HDF5: infinite loop closing library
      D,G,A,S,T,F,D,A,S,T,F,FD,P,FD,P,FD,P,E,E,SL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL
```

Please ignore it. The engine is working correctly.
