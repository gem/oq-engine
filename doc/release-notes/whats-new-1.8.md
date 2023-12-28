Release notes v1.8
==================

We are pleased to announce the release of OpenQuake 1.8.
This is a major release and contains numerous improvements with respect
to OpenQuake 1.7.

New features of the OpenQuake Engine, version 1.8
---------------------------------------------------

1. The most important feature is that the calculators based on
PostgreSQL are all gone. There is now no distinction between the oq-lite
calculators and the engine calculators: they are all the same.
All the calculators use an HDF5 file (the datastore) as data
storage. This has a large performance impact on calculations heavy
on data storage.

2. Thanks to the new calculators, the celery/rabbitmq combo is now
optional. Actually, the recommended way to run the engine on a single
machine is *without* celery/rabbitmq. This means that the majority
of the users, including everybody using the official virtual machines
will have a simpler experience. The most common error for newbies was
to forget starting celery or running it from the wrong directory. Now
this barrier is gone. Also, the engine is more efficient without
celery/rabbitmq, especially for calculations with a large data
transfer.

3. In a cluster situation, the combo celery/rabbitmq is still needed. In this
case you should edit the file `openquake.cfg` and
set the parameter `use_celery` to `True`. Then, a dynamic default for the
parameter `concurrent_tasks` will be determined by asking celery how many
cores are available and by multiplying that number by 2. This is done
at each new calculation. This mechanism solves another common error for users
setting a bad `concurrent_tasks`.

4. The classical hazard calculator has been completely rewritten. Now
it automatically splits the site collection in tiles of size
`sites_per_tiles` (the default is 1,000 sites per tile). This has an
huge performance benefit, especially for continental scale calculation
with tens or hundreds of thousand of sites.

5. The storage of the results in the datastore has been significantly
improved. There is now a serialization protocol *to* and *from* HDF5:
thanks to that several pickled Python objects have been removed from the
datastore and replaced with proper arrays. Among them:

   *sitecol*:
     contains the hazard sites and their parameters
   
   *assetcol*:
     contains the exposure
   
   *riskmodel*:
     contains the vulnerability/fragility functions

   *csm_info*:
      contains information about the composition of the source model

8. There is now an HTTP API to validate NRML files, implemented on top
of the engine server. This API is used by the new Risk Input
Preparation Toolkit in the platform.

8. We enabled Zip64 extensions and now we can export zip files
larger than 4 GB on 64 bit machines.

9. The validation of the risk models in the engine has been
improved. In particular if the user writes "SA" instead of "SA(...)" the
error is flagged early. If the risk wants some Intensity Measure Type
which is not available, a clear error is displayed early.

10. A few CSV exporter were improved. In particular we added a
taxonomy column to the CSV output of the scenario damage calculator
in presence of a consequence model. Moreover, now the hazard map
CSV exporter also exports the PoEs as column headers. Finally,
we changed the column names in the header to be `lon` and `lat`
for longitude and latitude fields: this makes it easier to import
the data in QGIS.

11. We improved the algorithm to determine the required data transfer
for the source model. Moreover, now we also report the figures for
the task with the highest data transfer back.

14. `hazardlib` now contains an arbitrary MFD, in which the magnitudes
and rates are input as a pair of lists.

15. Several new GMPEs have been added:

   + GMPE of Gupta (2010) for intraslab earthquakes in the Indo-Burmese subduction zone
   + GMPE of Nath et al. (2012) for interface subduction in in the Shillong plateau of India
   + GMPE of Kanno et al. (2006) for shallow and deep earthquakes in Japan
   + Two GMPEs for weighted mean epistemic uncertainty NSHMP NGA
   + Fixed the GMPETable class: this was needed for the Canada model
   + GMPE of Raghukanth & Iyengar (2007) for stable continental regions of peninsular India
   + GMPE of Sharma et al. (2009) for active shallow crust in Himalayas
   + GMPE of Drout (2015) for Brazil
   + GMPE of Moltalva et al (2015)

16. Other improvements entered in hazardlib, such as making clearer
the error message in several validity checks for the GMPEs, or adding
a method `split_in_tiles` to the SiteCollection class.

17. The .rst report of a calculation has been improved and more information is
displayed. The command `oq-lite info --report job.ini` allows to generate
a partial report without running the full computation, whereas the command
`oq-lite show fullreport <calc_id>`` displays the full report after the
computation has been executed.

Bug fixes and changes with respect to OpenQuake 1.7
----------------------------------------------------

1. We removed several switches from the `oq-engine` command:
all the commands that have been deprecated for over two years, all
the commands that have become obsolete (i.e. the one specific
to PostgreSQL), and all the commands that never worked properly:

  + --list_inputs
  + --lite
  + --list-hazard-outputs/--lho
  + --list-risk-outputs/--lro
  + --export-hazard-output/--eh
  + --export-risk-output/--er
  + --export-hazard-outputs/--eho
  + --export-risk-outputs/--ero
  + --export-stats/--es
  + --save-hazard-calculation/--shc
  + --load-hazard-calculation
  + --load-curve
  + --list-imported-outputs

2. `--delete-hazard-calculation` and `--delete-risk-calculation` have
been unified into a single `--delete-calculation`.

3. A lot of obsolete code (over 12,000 lines) has been removed from the engine
and the code base is now smaller and manageable: more will be removed in the
next release.

4. The logic for splitting the sources has changed: now only the so-called
*heavy* sources are split, thus reducing a lot the split time and the
data transfer.

5. The algorithm to read the source model has been changed and it is
faster, since it does not require to parse the same file more
than once anymore. This was the case for nontrivial logic trees.

6. The algorithm to generate seeds for the event based calculator has
changed. The new algorithm ensures that the results are not affected
by the splitting procedure. Because of the change in the algorithm,
the ruptures produced by the event based calculator are slightly
different than before, and all the dependent quantites are different
as well. The difference however is stochastically insignificant, akin
to a change of seeds and in the limit of a large number of Stochastic
Event Sets the results are equivalent.

7. A subtle bug in the scenario risk calculator, affecting calculations
with nonzero coefficients of variations, was discovered. The epsilons
were associated to the assets in a random order. The issue has been
fixed and this is the reason why the numbers are (slightly) different
from before in the ScenarioRisk demo.

7. There was a possible bug when reading GMFs from a NRML file,
if longitude and latitude has more than 5 digits. This has been fixed
now. The coordinates are still rounded to 5 digits, but we removed
the need for the ordering check, so any file can be imported, even
if the coordinates are not ordered after rounding.

8. We temporarily removed the ability to compute insured loss curves from
the classical risk calculator. The reason is that doubts were
raised about the algorithm used. The plan is to restore such functionality
in the next version of the engine with a better and more tested algorithm.

9. The parameter `asset_hazard_distance` was not honored for the
calculators `classical_risk` and `classical_bcr`: this has been
fixed now.

10. Several structures in the HDF5 datastore have changed.
The HDF5 format continues to be *not* stable and it will keep
changing in the next version of the engine. If you want to write
your our routines your our routines to extract/plot the hazard curves
or the loss curves from the datastore, you can, but you should be
aware that you will have to change your code with future releases
of the engine.

11. We fixed a bug in the exporter for the average losses in the event based
risk calculator: in presence of multiple loss types, the numbers were
mixed up.

12. We fixed a few XML export bugs. Now the XML exporters for mean and
quantile loss curves and maps work properly in all situations. Also,
the XML exporters for the Uniform Hazard Spectra have been rewritten
to export from the datastore, not from the database.

13. We are not storing anymore the epsilon matrix in event based and
scenario risk calculations. There was no strong reason to persist it,
and since it can be rather large, it was artificially making the
datastore larger than needed.

13. We removed a check that was too strict: now the exposure does not
need to provide costs if you are doing damage calculations, since the
classical damage and scenario damage calculators depends on the
numbers and the occupancies, not on the costs.

14. Some unused and undocumented configuration parameters like `statistics`
have been removed.

15. The demos have been revisited and updated.

16. We fixed a subtle bug that made it impossible to make a deepcopy
of source objects.

17. Since all the classical calculators use the datastore, the
export has changed slightly with respect to the past. Everything
is now more consistent.

18. We added a check on classical damage calculation: now if there is
a PoE = 1, the error is raised early in the pre_execute phase and not
during the parallel calculation.

19. The `oq-lite` command-line tool has been enhanced and the order of
arguments for the commands `oq-lite show` and `oq-lite export` have changed.
The tool is still experimental and could disappear in the next release;
it could be merged with the `oq-engine` command-line tool.

20. Countless small improvements and additional validations have been
added. This release has seen 159 pull requests reviewed and merged.

Support for different platforms
----------------------------------------------------

OpenQuake 1.8 supports Ubuntu from release 12.04 up to 15.10.  We
provide official packages for the long term releases 12.04 and 14.04.
*Ubuntu 12.04 has been deprecated for a long time and this is the last
release to support it*.

We have official packages also for CentOS 7
and in general for [Red Hat Enterprise Linux clones]
(Installing-the-OpenQuake-Engine-from-source-code-on-Fedora-and-RHEL.md).

While the engine is not supported on Windows and Mac OS X, we are
happy to report that the underlying libraries and the
`oq-lite` command-line tool run just fine.

Other
------

Depending on the version of the HDF5 libraries you are using,
you may get a warning like the following:

```
HDF5: infinite loop closing library
      D,G,A,S,T,F,D,A,S,T,F,FD,P,FD,P,FD,P,E,E,SL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL
```

Please ignore it, it is a quirk on the underlying library. The engine
is working correctly.
