Release notes for the OpenQuake Engine, version 2.5
===================================================

This release (re)introduces a tiling mechanism for classical PSHA
hazard calculations. The tiling increases the performance of
calculations dominated by distance computations and reduces the
memory consumption of continental scale calculations.

There is a new `MultiPointSource` object in hazardlib, with its own
XML serialization protocol. Regular point sources are stored very
inefficiently, due to a large amount of redundancy for identical
parameters. Using MultiPointSources the XML source model can be up
to an order of magnitude smaller than using equivalent
PointSources. MultiPointSource are also more efficient to read, to
write and to transfer. The computational performance is more
or less the same as before, though, do not expect miracles.

This is the first release with hazardlib included in the engine: there
are no more separated hazardlib packages. The change is transparent to
the user and the upgrade procedure will automatically do the right thing.
However, developers using the oq-hazardlib repository should know that
it has been deprecated, since it is included in engine repository now.
In order to avoid confusion, we suggest to remove the oq-hazardlib
repository if you have one.

Several bugs have been fixed and there were a few improvements to the
Web User Interface(WebUI) and to the engine itself.

More than 70 pull requests were closed. For the complete list of
changes, please see the changelog:
and https://github.com/gem/oq-engine/blob/engine-2.5/debian/changelog.

New features
------------------------------

The major new feature is the return of the tiling calculator. We had
this feature in the past, but the current version is a lot more
efficient than the old one.  The reason is that the filtering of
point sources has been significantly improved and it is no more a
bottleneck of the calculator.

The tiling starts automatically if there
are more than 20,000 hazard sites, but you can change the default:
just set the parameter `sites_per_tile` in your `job.ini` file.

We introduced some preliminary support for the Grid Engine. This is useful
for people running the engine on big clusters and supercomputers. Unfortunately,
since we do not have a supercomputer, we are not able to really test this 
feature. Interested users should contact us and offer some help, like giving
us access to a Grid Engine cluster.


WebUI
-------------------

oq webui start now open a browser window if possible

added commands 

oq webui createsuperuser and

oq webui collectstatic

- Fixed a bug in `oq plot`
Confirm Dialog before remove calculation

Bugs
----


Internal changes
--------------------

As always, there were several internal changes to the engine. They are invisible
to regular users, so I am not listing all of the changes here. However, I
will list some changes that may be of interests to power users and people
developing with the engine.

AreaSources are not more PointSources;


Deprecations
------------------------------

As of now, all of the risk XML exports are officially deprecated and
will be removed in the next release. The recommended exports to use are
the CSV ones for small outputs and the .npz/HDF5 ones for large outputs.

[Our roadmap for abandoning Python 2](https://github.com/gem/oq-engine/issues/2803) has been updated.

-----------------------


- The error checking when parsing source models in format NRML 0.5 has been
  improved: now in case of error one gets the name of the incorrect node and
  its line number, just like for NRML 0.4
  
- Getting the version of the engine required having git installed on macOS,
  but now this has been fixed
- Some preliminary work for Python 3 installers has been done

- Disaggregation outputs: `disagg_outputs = Mag_Dist`
- Small improvements: if no stats should be generate, no data transfer
- Fixed an encoding error when logging filenames with non-ASCII
  character affecting macOS users
  
- Removed the deprecated XML risk outputs
- Raise an early error if there are missing taxonomies in the consequence model
Do not skip writing the `ruptureId` for the first event  bug
Removed excessive logic tree reduction in event based bug

- Improved the `oq db` command 

Added dmg_by_asset_npz exporter enhancement

Added an end point `v1/calc/XXX/oqparam` to extract the calculation parameters as a JSON dictionary  enhancement

Fixed a bug in `oq export hcurves-rlzs --exports hdf5`
Fixed parallel.Starmap for non-rpc backends
Raised a clear error if the user does not set the `calculation_mode` 
Removed the composite_source_model from the datastore
Improved the error message when the rupture mesh is too small
Exposed hmaps also in event based
Fixed some packaging issues in the Red Hat packager
Fixed bug in dbserver.different_paths in presence of symlinks 
