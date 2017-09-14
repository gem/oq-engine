Release notes for the OpenQuake Engine, version 2.6
===================================================

Several new features where introduced in this release. Now the engine
installer includes three web applications previously only available
on the OpenQuake Platform: the Input Preparation Toolkit (IPT), the
Taxonomy application and XXX.

Several bugs have been fixed and there were a few improvements to the
Web User Interface(WebUI) and to the engine itself.

More than 100 pull requests were closed. For the complete list of
changes, please see the changelog:
and https://github.com/gem/oq-engine/blob/engine-2.5/debian/changelog.

Major new features
------------------------------


Bugs fixed
----------------


Other improvements
---------------------

- The engine was calling the routine computing the statistics even when
  not needed. This was inefficient and has been fixed.
- The error checking when parsing source models in format NRML 0.5 has been
  improved: now in case of error one gets the name of the incorrect node and
  its line number, just like for NRML 0.4.
- There is now a clear error message if the user does not set the
  `calculation_mode` in the `job.ini` file.
- We improved the error message when the rupture mesh spacing is too small.
- We added a new `.npz` exporter for the output `dmg_by_asset_npz`.
- There is a new `.csv` exporter for the aggregate loss curves, replacing
  the deprecated XML exporter.
- Some preliminary work for the Python 3 installers has been done.

As always, there were several internal changes to the engine. Some of
them may be of interests to power users and people developing with the
engine.

- It is now possible to use the engine with backends different from rabbitmq,
  for instance with redis; we did some experiment in this direction, but
  rabbitmq is still the official backend to use.
- The AreaSource class in hazardlib is no more a subclass
  of PointSource (that was an implementation accident).
- The syntax of the command `oq db` has been improved.
- The `composite_source_model` has been removed from the datastore:
  this was the last pickled object remaining there for legacy reasons.
- We changed the way the logic tree reduction works in event based calculators:
  now it works the same as in classical calculators. The change may affect
  rare corner cases, when there are source groups producing zero ruptures;
  see https://github.com/gem/oq-engine/pull/2840 for the details.

Deprecations
------------------------------

The obsolete `nrmlSourceModelParser` in the Hazard Modeller Toolkit has been
removed.

The repository https://github.com/gem/oq-hazardlib has been deprecated
and new pull requests for hazardlib should be opened towards the engine
repository.

[Our roadmap for abandoning Python 2](https://github.com/gem/oq-engine/issues/2803) has been updated.
--------------------------------------------------------------------------------


  * Added a documentation page `oq-commands.md`
  * Fixed bug in the exported outputs: a calculation cannot export the results
    of its parent


-- webui

Visualized the calculation_mode in the WebUI
Removed an excessive check from the WebUI: now if an output exists,
it can be downloaded even if the calculation was not successful
Show to the user the error message when deleting a calculation
in the WebUI fails



-- changes
Changed the generation of loss_maps in event based risk, without the option
`--hc`: now it is done in parallel, except when reading the loss ratios
Replaced the agg_curve outputs with losses by return period outputs
Changed the storage of the GMFs; as a consequence the exported .csv
has a different format
Changed the sampling logic in event based calculators
Imported GMFs from external file into the datastore
Changed the GMF CSV exporter to export the sites too; unified it with the
event based one
Changed the source weighting algorithm: now it is proportional to the
the number of affected sites
Renamed `--version-db` to `--db-version`, to avoid
confusions between `oq --version` and `oq engine -version`
    
--- bugs

Extended the `sz` field in the rupture surface to 2 bytes, making it
possible to use a smaller mesh spacing
Fixed the export by realization of the hazard outputs
Fixed `oq export hcurves-rlzs -e hdf5`
Fixed a bug in the statistical loss curves exporter for classical_risk
(bogus numbers)
Fixed a bug when computing the rjb distances with multidimensional meshes
Fixed a bug introduced by a change in Django 1.10 that was causing
the HTTP requests log to be caught by our logging system and
then saved in the DbServer
Fixed a bug: if there are multiple realizations and no hazard stats,
it is an error to set hazard_maps=true or uniform_hazard_spectra=true
Fixed a small bug in the HMTK (in `get_depth_pmf`)
Fixed correct_complex_sources.py
  
-- new features

Added two commands `oq dump` and `oq restore`
First version of the calculator gmf_ebrisk
Added an exporter gmf_scenario/rup-XXX working also for event based
Implemented risk statistics for the classical_damage calculator
Added a .csv importer for the ground motion fields
Implemented risk statistics for the classical_bcr calculator
  
-- packaging/installation

Added support for Django 1.11 too
Added the 'celery-status' script in 'utils' to check the
task distribution in a multi-node celery setup
Extended the 'oq reset' command to work on multi user installations
  
--- hazardlib

Implemented the Munson and Thurber 1997 (Volcanic) GMPE
Adapts CoeffsTable to be instantiated with dictionaries as well as strings


--- new checks

Added a check that on the number of intensity measure types when
generating uniform hazard spectra (must be > 1)
Better error message when running a risk file in absence of hazard
calculation

-- new features
  * Implemented aggregation by asset tag in the risk calculators

-- other improvements
Changed the 'CTRL-C' behaviour to make sure that all children
processes are killed when a calculation in interrupted

--- internals
Added a command `oq show dupl_sources` and enhances `oq info job.ini`
to display information about the duplicated sources
Added a flag `split_sources` in the job.ini (default False)
Turned the DbServer into a multi-threaded server
Used zmq in the DbServer
Extended the demo LogicTreeCase1ClassicalPSHA to two IMTs and points
Removed the automatic gunzip functionality and added an automatic
checksum functionality plus an `oq checksum` command

Changed the format of array `all_loss_ratios/indices`
The size in bytes of the GMFs was saved incorrectly
