New features of the OpenQuake Engine, version 1.9
=================================================

1. We have worked on several CSV exporters. The CSV exporters are
still experimental and this is why they are are not yet documented in the
manual. In the future we will likely change the names of the exported
files. Nevertheless the CSV file format is now more or less decided for the
following CSV exporters in this release:

  - exporter for scenario ground motion fields
  - exporter for asset losses for scenario risk
  - exporter for scenario damage distribution by asset
  - exporter for scenario damage distribution by taxonomy
  - exporter for scenario damage distribution total

2. There is no CSV exporter for GMFs for the event based calculator. This is
on purpose, since exporting all of the GMFs for large calculations often takes longer
than the whole computation. You can export the GMFs generated by
specific ruptures with oq-lite, but this feature is still experimental
and undocumented.

3. The existing XML exporters have been improved. Now the loss curve and loss map
exporters list both the hazard investigation time and the risk investigation
time.

4. When exporting a result comprising multiple files, the engine now prints the path names of
all of the exported files. In previous versions of the engine, only the export directory was listed.

5. The memory occupation and data transfer of the event based risk
calculator have been substantially reduced. The asset loss table is
not built anymore, unless explicitly requested in the configuration
file by setting the parameter `asset_loss_table` to `true`. Moreover,
insured average losses are now trasferred and stored only when the
flag `insured_losses` in the configuration file is set to `true`.
In previous versions of the engine, `NaNs` were transferred and stored.

6. The most important thing from the technological point of view is
that we removed the dependency from PostGIS. Right now the engine uses
only four relational tables; the plan for the future (for release 2.0)
is to remove PostgreSQL entirely and to use sqlite as the internal
database. This is possible since after the changes in engine 1.8 all
of the calculation data are stored in an HDF5 file, and only a minimal
amount of data is stored in the relation tables. We store the job
ID, the start time and stop time, the path to the underlying HDF5
file, some logs and some performance information. The change is
compatible with the past and will not affect your existing tables if
you are upgrading from a previous version.

7. More pickled objects have been replaced by proper arrays in the datastore:
in particular the `CostCalculator` object and the `time_events` list. There
are still more objects to remove.

8. For what concerns hazardlib, we added regionalization for Japan to the
GMPE of Atkinson & Boore (2003). 

9. We changed the routine producing the ground motion fields to return
32 bit numpy arrays, to save memory, disk space and data transfer.


Bug fixes
---------

1. In release 1.8 some risk calculations were incorrectly flagged as hazard
calculations; this has been fixed by looking directly at the
`calculation_mode` parameter.

2. In release 1.8 there was an error in the event based risk
calculator when trying to compute mean and quantile loss maps in
absence of `conditional_loss_poes`: now there is no error, the statistics
are not computed, because there are no loss maps.

3. When reading a datastore, the engine correctly discriminates between
the "file not found" and "no permission" errors. Earlier,
you got a "file not found" error even if the file existed but you did not
have permission to traverse the containing directories.

4. If the job description contained a non-ASCII character, the .rst
report could not be generated. This has been fixed.

5. In engine 1.8 in some situations the lines of logs on `stderr` were
duplicated. Moreover the logs were not ordered chronologically in the WebUI.
Both issues have been fixed.

6. The default job status has changed from `pre_executing` to `executing`.
This reads better in the Web UI.

7. We removed a misleading error message referring to the obsolete option
`--hazard-output-id` that was removed in release 1.8.

8. We fixed a bug with the export of the uniform hazard spectra, which
occurred only in cases with a single PoE specified in the job.ini file.

9. We fixed a 32 bit/64 bit casting error, occurring in some cases
when reading the hazard from a datastore in the presence of a site model.