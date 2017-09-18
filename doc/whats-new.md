Release notes for the OpenQuake Engine, version 2.6
===================================================

Several new features where introduced in this release. Moreover, now the engine
installer includes three web applications previously only available
on the OpenQuake Platform: the Input Preparation Toolkit (IPT), the
Taxonomy application and XXX.

Several bugs have been fixed, some outputs were changed and there were
a few improvements to the Web User Interface(WebUI) and to the engine
itself.

More than 100 pull requests were closed. For the complete list of
changes, please see the changelog:
and https://github.com/gem/oq-engine/blob/engine-2.5/debian/changelog.


New features
--------------

Implemented aggregation by asset tag in the risk calculators

There is a new experimental calculator called `gmf_ebrisk` which is able to
perform an event based risk calculators starting from ground motion fields
provided as a CSV file. In order to implement this feature we changed the
export format of the ground motion fields so that it is the same as the
input format of the new calculator. Moreover the GMF CSV export format is
now the same both for event based and scenario calculators.

We added three new `oq` commands:

- `oq extract <what> <calc_id>` allows to save a specified output into an .hdf5 file
- `oq dump <dump.zip>` allows to dump the database of the engine and all
  the datastores into a single .zip file
- `oq restore <dump.zip> <oqdata>` allows to restore a dump into an empty directory

`oq extract hazard/rlzs` solves the problem of generating a single .hdf5 file with all
hazard curves, maps and uniform hazard spectra for all realizations; this
was requested by some power users and it is documented in
https://github.com/gem/oq-engine/blob/master/doc/oq-commands.md

Added an exporter gmf_scenario/rup-XXX working also for event based
Implemented risk statistics for the classical_damage calculator
Implemented risk statistics for the classical_bcr calculator
  

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
Fixed bug in the exported outputs: a calculation cannot export the results
of its parent
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

[Our roadmap for abandoning Python 2](https://github.com/gem/oq-engine/issues/2803) has been updated.
