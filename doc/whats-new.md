Release notes for the OpenQuake Engine, version 2.5
===================================================

This release reintroduces the tiling calculator for large classical
PSHA hazard calculation that we removed in the past. The reason is
that the filtering of point sources has been significantly improved
and it is now suitable to run it multiple times (one per tile)
while before this was a bottleneck of the tiling calculator.

Moreover we introduced a new `MultiPointSource` object in hazardlib, with
its own XML serialization protocolo. Ordinary point sources were stored
very inefficiently, due to a large amount of redundancy in the common
case of have thousands of sources with a large amount of identical
parameters, in particular the nodal plane distributions and the
hypocenter distributions. Using MultiPointSource is up to an order of magnitude
more compact than using equivalent PointSources, in terms of size of the XML.
MultiPointSource are also more efficient to pickle and to transfer.
The computational performance is more or less the same as before, though.

This is the first release with hazardlib included in the engine: there
are no more separated hazardlib packages. The change is transparent to
the user and the upgrade procedure will automatically do the right thing.
However, developers using the oq-hazardlib repository should know that
it has been deprecated, as it is included in engine repository now.
In order to avoid confusion, we suggest to remove the oq-hazardlib
repository if you have one.

Several bugs have been fixed.

More than 40 pull requests were closed in oq-hazardlib and more than
200 pull requests were closed in oq-engine. For the complete list of
changes, please see the changelog:
and https://github.com/gem/oq-engine/blob/engine-2.5/debian/changelog.


WebUI
-------------------


Bugs
----


Experimental new features
------------------------------

In this release the work on the UCERF calculators has continued,
even if they are still officially marked as experimental and left
undocumented on purpose.

There `ucerf_classical` calculator has been extended to work with
sampling of the logic tree. The rupture filtering logic has been
refactored and made more consistent with the other calculators.

The `ucerf_rupture` calculator has been extended so that we can
parallelize by number of stochastic event sets. This improvement made
it possible to run mean field calculations in parallel: before such
calculations used a single core.

The data transfer has been hugely reduced in the calculator
`ucerf_risk`: now we do not return the rupture objects from the
workers, but only the event arrays, which are enough for the purposes
of the calculator. This saved around 100 GB of data transfer in large
calculations for California.

We fixed a bug in `ucerf_risk` that prevented the average losses
from being stored. Now this works out of the box, provided you
set `avg_losses=true` in the `job.ini` file.

There is a brand new time-dependent UCERF classical calculator.

We started working on an event based calculator starting from Ground
Motion Fields provided by the user. The current version is still very
preliminary and requires the GMFs to be in NRML format, but we plan
to extend it to read the data from more efficient formats (CSV, HDF5)
in the near future.

We added a facility to serialize `Node` objects into HDF5 files. This is
the base for a future development that will allow to serialize point sources
into HDF5 datasets efficiently (scheduled for engine 2.5).

We introduced some preliminary support for the Grid Engine. This is useful
for people running the engine on big clusters and supercomputers. Unfortunately,
since we do not have a supercomputer, we are not able to really test this 
feature. Interested users should contact us and offer some help, like giving
us access to a Grid Engine cluster.

Internal changes
--------------------

As always, there were several internal changes to the engine. They are invisible
to regular users, so I am not listing all of the changes here. However, I
will list some changes that may be of interests to power users and people
developing with the engine.


Deprecations
------------------------------

As of now, all of the risk XML exports are officially deprecated and
will be removed in the next release. The recommended exports to use are
the CSV ones for small outputs and the .npz/HDF5 ones for large outputs.

[Our roadmap for abandoning Python 2](https://github.com/gem/oq-engine/issues/2803) has been updated.
