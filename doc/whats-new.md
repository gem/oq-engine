Release notes for the OpenQuake Engine, version 2.3
===================================================

The major change in this release is technological: we improved significantly
out packaging strategy and now we provide packages that works for nearly
every operating system, by using the exact same versions of the libraries
on every platform.

We also added some new features on the hazard side. Now it is possible
to perform hazard computations taking into account the topography of
the region of interest, i.e. it is possible to consider earthquake
occurring above the level of the sea. Before the altitude of the
hazard site was ignored.

It is also possible to use magnitude-dependent integration distances.
This has a very positive impact on the calculation time, since small
magnitude ruptures will affects a lot less sites than before. In order
to use that feature the user has to specify 


has focused on memory and performance optimizations, especially
in the event based and scenario calculators. Moreover we have significantly
improved our exports, by providing more information (especially for the
event based ruptures) and/or using more efficient export formats, like the
.npz format. As of now, the XML exports are deprecated, even if there is
no plan to remove them at the moment.

As usual, lots of small bugs have been fixed. More than 60 pull requests were
closed in oq-hazardlib and more than 160 pull requests were closed in
oq-engine. For the complete list of changes, please 
see the changelogs: https://github.com/gem/oq-hazardlib/blob/engine-2.2/debian/changelog and https://github.com/gem/oq-engine/blob/engine-2.2/debian/changelog.

A summary follows.

General improvements
====================================

Simplified the installation and dependency management
-----------------------------------------------------

Starting with release 2.2 the OpenQuake libraries are pure Python.
We were able to remove the need for the C speedups in hazardlib and
now we are as fast as before without requiring a C extension, except
in rare cases, where the performance penalty is very minor.

There are of course still a few C extensions, but they are only in third
party code (i.e.  numpy), not in the OpenQuake code base. Third party
extensions are not an issue because since 2.2 we manage the Python
dependencies as wheels and we have wheels for all of our external
dependencies, for all platforms. This binary format has the big
advantage of not requiring compilation on the client side, which was
an issue, especially for non-linux users.

The recommended way to install the packages is still via the official
packages released by GEM for Linux, Windows and Mac OS X (see
https://github.com/gem/oq-engine/blob/master/doc/installing/overview.md).
However, the engine is also installable as any other Python software: create a
[virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/)
and run `pip install openquake.engine`:

```bash
$ python3 -m venv oq-engine
$ source oq-engine/bin/activate
(oq-engine) $ pip install openquake.engine
```

This will download all of the dependencies (wheels) automatically. If
you only need hazardlib, run `pip install openquake.hazardlib`
instead. This kind of installation is meant for Python-savvy users
who do not need to modify the OpenQuake code. Users that want to
develop with the engine or with hazardlib (eg. implement a new GMPE)
should not install anything; they should clone the git repositories
and set the PYTHONPATH, or install it from sources using 
`pip install -e`, as in any other Python project.

Improvements to hazardlib
=========================================

In release 2.2 several changes entered in hazardlib. Finally the
oq-hazardlib repository has become self-consistent. In particular
the parallelization libraries are now in oq-hazardlib, as well as
the routines to read and write source models in NRML format. As
a consequence now the [Hazard Modeller's Toolkit]
(https://github.com/GEMScienceTools/hmtk) depends solely on
hazardlib: users are not forced to install the engine if they do
not need to run engine-style computations. This reduces the cognitive load.

Among the improvements:

- the function `calc_hazard_curves` of hazardlib has been extended and it
  is now able to parallelize a computation, if specified
- it is possible to correctly serialize to NRML and to read back all types
  of hazardlib sources, including nonparametric sources
- the format NRML 0.5 for hazard sources is now fully supported both in
  hazardlib and in the engine

As usual, a few new GMPEs were added:

- site adjusted Pezeshk et al. 2011


Finally, the documentation of hazardlib (and of the engine too) has
been overhauled and it is better than it ever was. There is still room
for improvement, and users are welcome to submit documentation patches
and/or tutorials.

Improvements to the engine
=========================================

There a new CSV exporter for all calculators except the scenario based.
It is called `sourcegroups.txt`.


The event loss table exporter has been improved and it is now faster
than in release 2.2. However, it is not exporting the tectonic region
type string anymore; still, you can infer it from the event_tag
which contains the source group. Also, the `source_id` has been stripped
from the `event tag` since it was taking a lot of memory in the case of
extra-large calculations (UCERF).

Changes
------------

The calculation of quantiles hazard curves used different algorithms
in the case of logic tree full enumeration and logic tree sampling.
Now, for consistency sake, we use always the same algorithm, the
one of full enumeration. This change may produce small differences in
the quantile curves if you were doing computations with sampling of
the logic tree.


Other
------

We removed a warning about missing rtree that was too noisy.

A bug in the logic tree storage was fixed. Now it possible to run a
computation on a machine, copy the datastore on a different machine
and to export the results from there.

There is an experimental command `run_tiles` to split a `sites.csv`
file in tiles and run multiple calculations at once. This for expert
use only and not recommended.

The parallelization library is now more robust against unexpected
exceptions.

As usual the internal representation of several data structures has
changed in the datastore. Thus, we repeat our regular reminder that
users should not rely on the stability of the internal datastore formats.
In particular, the ruptures are now stored as a nice HDF5 structure and
not as pickled objects, something that we wanted to achieve for
years.

NRML 0.5 work and read; added GriddedSurface;

occupants:float32.

We changed the port of the DbServer;

`oq engine --make-html-report` now works with Python 3

`oq info` and `oq info -r` have been improved

Fixed the installation `pip openquake.engine`: now the `openquake.cfg`
file is included in the installation.

UCERF
-----------
Finally, a lot of work went into the UCERF calculators. However,
the should still be considered experimental and there are a few known
limitations about those. This is why they are still undocumented.

There is a new time-dependent calculator and the old calculators were
substantially improved.
