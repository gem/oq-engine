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

Major new features
------------------------------

The major new feature is the return of the tiling calculator. We had
this feature in the past, but the current version is a lot more
efficient than the old one.  The reason is that the filtering of
point sources has been significantly improved and it is no more a
bottleneck of the calculator.

The tiling starts automatically if there are more than 20,000 hazard
sites, but you can change the default: just set the parameter
`sites_per_tile` in your `job.ini` file.

The MultiPointSources are a new experimental feature and as such thet are
not documented in the manual (yet); however they are documented [in the engine
doc folder](https://github.com/gem/oq-engine/blob/engine-2.5/doc/multipoint.md)
and you are invited to use them.

There were several small improvements to the Web UI:

- the command `oq webui start` now open a browser window if possible
- we added the commands `oq webui createsuperuser` and `oq webui collectstatic`
  which are useful for system administrators setting a multiuser instance of
  the WebUI (see https://github.com/gem/oq-engine/blob/engine-2.5/doc/installing/server.md).
- there is a confirmation dialog before removing a calculation

Bugs fixed
------------------


- Getting the version of the engine required having git installed on macOS,
  but now this has been fixed

- Disaggregation outputs: `disagg_outputs = Mag_Dist`
- Fixed an encoding error when logging filenames with non-ASCII
  character affecting macOS users
  
- Removed the deprecated XML risk outputs
- Raise an early error if there are missing taxonomies in the consequence model
Do not skip writing the `ruptureId` for the first event  bug
Removed excessive logic tree reduction in event based bug


Added dmg_by_asset_npz exporter enhancement

Added an end point `v1/calc/XXX/oqparam` to extract the calculation parameters as a JSON dictionary  enhancement

Fixed a bug in `oq export hcurves-rlzs --exports hdf5`

Raised a clear error if the user does not set the `calculation_mode` 
Improved the error message when the rupture mesh is too small
Exposed hmaps also in event based
Fixed some packaging issues in the Red Hat packager
Fixed bug in dbserver.different_paths in presence of symlinks 

- We fixed a bug in `oq plot`, signaled by a power user;

Other improvements
---------------------

- Small improvements: if no stats should be generate, no data transfer

- The error checking when parsing source models in format NRML 0.5 has been
  improved: now in case of error one gets the name of the incorrect node and
  its line number, just like for NRML 0.4
  
- Some preliminary work for Python 3 installers has been done

As always, there were several internal changes to the engine. Some of
them may be of interests to power users and people developing with the
engine.

- it is now possible to use the engine with backends different from rabbitmq,
  for instance with redis; we did some experiment in this direction, but
  rabbitmq is still the official backed to use with the engine
- the AreaSource class in hazardlib is no more a subclass
  of PointSource (that was an implementation accident)
- the 

- Improved the `oq db` command 
- Removed the `composite_source_model` from the datastore

Deprecations
------------------------------

As of now, all of the risk XML exports are officially deprecated and
will be removed in the next release. The recommended exports to use are
the CSV ones for small outputs and the .npz/HDF5 ones for large outputs.

[Our roadmap for abandoning Python 2](https://github.com/gem/oq-engine/issues/2803) has been updated.
