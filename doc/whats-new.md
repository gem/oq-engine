Release notes for the OpenQuake Engine, version 2.2
===================================================

This release has focused on memory and performance optimizations, especially
in the event based and scenario calculators. Moreover we have significantly
improved our exports, by providing more information (especially for the
event based ruptures) and/or using more efficient export formats, like the
.npz format.

As usual lots of small bugs have been fixed. More than 50 pull requests were
closed in oq-hazardlib and more than 150 pull requests were closed in
oq-engine. For the complete list of changes, please 
see the changelogs: https://github.com/gem/oq-hazardlib/blob/engine-2.2/debian/changelog and https://github.com/gem/oq-engine/blob/engine-2.2/debian/changelog.

A summary follows.

General improvements
====================================

Python 3 support
-------------------

The engine have been supporting Python 3 for several months and
hazardlib for more than one year. The novelty is that
since a couple of months ago our production environment has become
Python 3. Nowadays Python 3 is more tested than Python 2. Python 2.7
is still fully supported and we will keep supporting it for a while, but
it will be eventually deprecated.

Simplified the installation and dependency management
-----------------------------------------------------

Starting with release 2.2 the OpenQuake libraries are pure Python.
We were able to remove the need for the C speedups in hazardlib and
now we are as fast as before without requiring a C extension, except
in rare cases were the performance penalty is very minor.

There are of course still C extensions, but they are only in third
party code (i.e.  numpy), not in the OpenQuake code base. Third party
extensions are not an issue because since 2.2 we manage the Python
dependencies as wheels and we have wheels for all of our external
dependencies, for all platforms. This binary format has the big
advantage of not requiring compilation on the client side, which was
an issue, especially for non-linux users.

The recommended way to install the packages is still via the official
packages released by GEM for Linux, Windows and Mac OS X. However,
the engine is also installable as any other Python software: create a
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
that do not need to change the OpenQuake code. Users that want to
develop with the engine or with hazardlib (i.e. develop a new GMPE)
should not install anything, thye should just clone the git repositories
and set the PYTHONPATH, as in any other Python project.

The nrml_converters are not needed anymore
------------------------------------------

For as long as there has been an engine, there has been a repository
of scripts called [nrml_converters]
(https://github.com/GEMScienceTools/nrml_converters) written and
maintaned by our scientific staff. With the release 2.2 such tools
are be deprecated, since now the engine includes all the required
functionality. This will make life a lot easier for the final user.
For instance, instead of producing a (large) XML file with the engine
and convert it into CSV with the nrml_converters, now the engine can
produce the CSV directly in a more efficient way, sometimes *a lot* more
efficient way.
The `nrml_converters` repository will not be removed, since it is still
useful for users with an old version of the engine.

Improvements to hazardlib
=========================================

In release 2.2 several changes entered in hazardlib. Finally the
oq-hazardlib repository has become self-consistent. In particular
the parallelization libraries are now in oq-hazardlib, as well as
the routines to read and write source models in NRML format. As
a consequence now the [Hazard Modeler Toolkit]
(https://github.com/GEMScienceTools/hmtk) depends solely on
hazardlib: users are not forced to install the engine if they do
not need to run engine-style computations. This reduces the cognitive load.

Among the improvements:

- the function `calc_hazard_curves` of hazardlib is able to parallelize a
  computation if you say so
- it is possible to correctly serialize to NRML and to read back all kind
  of hazardlib sources, including nonparametric sources
- the format NRML 0.5 for hazard sources is now fully supported both in
  hazardlib and in the engine side
- it is (optionally) possible to filter hazard sources with the rtree library,
  which is a lot faster than using the old system

As usual, new GMPEs were added:

- Kale et al (2015)
- ...

Finally, the documentation of hazardlib (and of the engine too) has
been overhauled and it is better than it ever was. There is still room
for improvement, and users are welcome to submit documentation patches
and/or tutorials.

Improvements to the engine
=========================================

Task distribution improvements
-------------------------------

There have been a few changes affecting all calculators. In particular
the splitting and weighting of complex fault sources has been
changed and a bug fixed.

Right now a complex fault source is split by magnitude bin [1]:
if there are N magnitude bins, the same source is sent N times to
the workers, each time with a different single-bin MFD. This works
well if there are many bins; unfortunately there are cases of large
complex fault sources (i.e. sources generating several thousands of ruptures)
that have a single-bin MFD. Such sources cannot
be split and they end up producing tasks which are extremely slow to run
and dominate the total computation time. The solution was to split
such sources by slices of ruptures: the same source is sent multiple
times to the workers, but each time a different slice of the ruptures
is taken into consideration.

The number of slices is governed by the MAXWEIGHT parameter which
currently is hard-coded to 200, so that there are at most 50 ruptures
per split source, since the weight of a complex fault rupture is
currently 4. Such numbers are implementation details that change with
nearly every new release and should not be relied upon; an user should
just know that a lot is going on in the engine when processing the
sources. At each version we try to have a better (i.e. more
homogeneous) task distribution, to avoid slow tasks dominating the
computation.

In release 2.2 we have increased the number of tasks generated by the
engine by default. More tasks means smaller tasks and less
problems with slow tasks dominating the computation. You can still (as
always) control the number of generated tasks by setting the parameter
`concurrent_tasks` in the job.ini file.  In spite of our best efforts,
there will always be tasks slower than others; if your calculation is
totally dominated by a slow task, please sent us your files and we
will try to improve the situation, as always.

[1] Technically an MFD (Magnitude Frequency Distribution) object coming
from hazardlib has a method `get_annual_occurrence_rates()` returning
a list of pairs `(magnitude, occurrence_rate)`: those are the magnitude bins
I am talking about.

Correlated GMFs
---------------------

The engine has always been able to compute correlated GMFs by setting
the parameter `ground_motion_correlation_model = JB2009` in the
job.ini file.  Unfortunately, computing correlated GMFs has always
been slow and memory consuming. With the engine 2.2 the computation of
correlated GMFs is still slow and memory consuming, but less so.
In particular in a real life example submitted by one of our
sponsors we were able to achieve a speed up of 44 times, by caching
the computation of the correlation matrix. Since the algorithm has changed,
the produced GMFs in some cases can be slightly different than the ones
produced in the past. Don't worry, and see
https://github.com/gem/oq-engine/pull/2409 for an explanation.

Scenario calculators improvements
---------------------------------

The calculators `scenario_risk` and `scenario_damage` were extremely
slow and memory consuming, even in absence of correlation, for large
numbers of assets and large values of the parameter
`number_of_ground_motion_fields`. This has been fixed: now they use
half of the memory than before, and the computation is a lot
faster. The performance bug was in the algorithm reordering the GMFs
and affected both the case of correlated and non-correlated GMFs.

Classical and disaggregation calculators improvements
------------------------------------------------------

There was some work on the disaggregation calculator: with engine 2.2 it
is now possible to set a parameter `iml_disagg` in the `job.ini` file
and have the engine disaggregate with respect to that intensity measure
level. This was requested by one of our users (Marlon Pirchiner). Moreover,
now the disaggregation matrix is stored directly in the datastore - before
it was stored in pickled format - and it is possible to export it directly
in CSV format; before it had to be exported in XML format and converted into
CSV with the nrml_converters.

We discovered (thanks to Céline Beauval) that the engine was giving bogus
numbers for the uniform hazard spectra for calculation with intensity measure
types different from PGA and SA. The bug has been in the engine at least
from release 2.0, but now it has been finally fixed.

Finally, the improvements in the task distribution have improved the
performance of several classical calculations too.

Event based calculators improvements
-------------------------------------

There is a new and much wanted feature in the event based hazard calculator:
now it is possible to export information about the ruptures directly in CSV
format. Before one had to export it in XML format and than convert the XML
into CSV by relying on the `nrml_converters` tools. In order to be able to
export, however, one must set the parameter `save_ruptures=true` in the
`job.ini` file. By default, the parameter is false. The reason is that
storing the ruptures is time-consuming - it can dominated the computation
times - so if you are not interested in exporting the stochastic event set
you should not pay the price for it. Information about the ruptures is
still stored even if `save_ruptures` is false: such information is not
enough to reconstruct completely the ruptures but it is enough for most uses.
To get that information you should just export the `rup_data` CSV file.

At user request, we have added the year information to each seismic
event. This is included also in the exported event loss table. In
release 2.1 the stochastic set index was used instead. The two
approaches are equivalent if the investigation time is of 1 year, so
in engine 2.1 in order to know the year, an user had to use an
investigation time of 1 year, which is inefficient.  It is a lot
better to have a long investigation time (say 10,000 years) and a
single stochastic event set, with the years marked independently from
the stochastic event sets, as it is now.

Several changes went into the event based risk calculators, in
particular the management of the epsilons is now different [2]. While
before the engine was using the multivariate normal distribution,
which a covariance matrix coming from the `asset_correlation`
parameter and, now the engine does a lot less. Actually, it is only
able to address the special cases of `asset_correlation=0` and
`asset_correlation=1`: any intermediate case is an error. The reason
is that computing the full covariance matrix and all the epsilons at
the same time was too memory intensive. Moreover, the data transfer of
the epsilons from the master node to the workers was too big, except
in toy models. This is why now only the cases of no correlation and
full correlation are supported, in a lot more efficient way than they
were supported before. No covariance matrix is needed, since the
engine uses the standard normal distribution to generate the
epsilons. It means that now it is possible to run much larger
computation.

Also, a configuration parameter `ignore_covs` has been added. If the
computation is so large that it does run out of memory even with the
new improved mechanism, you can still run it by setting
`ignore_covs=true` in the `job.ini` file: with this trick the epsilons
will not be generated at all, even if your vulnerability functions
have nonzero coefficients of variation. You will lose the effects of
asset correlation, but an imperfect computation that runs has been
deemed better than a perfect computation that does not run.

Another big change is that the computation of loss curves has been moved in
a postprocessing phase and it is a lot more efficient than before, especially
in terms of data transfer. Also, loss maps are now dynamic outputs, i.e.
they are computed only on demand at export time. Before you had to pay
for them even if they were not exported.

[2] When the vulnerability functions have nonzero coefficients of variations,
the engine (versions <= 2.1) compute a matrix of (A, E) floats (the epsilons)
where A is the number of assets and E the number of seismic events.

.npz exports
-------------

We started using the `.npz` export format for numpy arrays. This is
extremely convenient for Python applications, since an `.npz` file can be
managed as a dictionary of arrays (just call `numpy.load('data.npz')`).
In particular our QGIS plugin is able to read the exported `.npz` files
and display things liks hazard curves, hazard maps and uniform hazard
spectra. We also have a tool to convert `.npz` files into `.hdf5` files,
if you prefer that format, just run

```bash
$ oq to_hdf5 *.npz
```

and all of you `.npz` files will be converted into `.hdf5` files.
In the future a lot more outputs are expected to be exported into
`.npz` format.

Other
------

As usual the internal representation of several data structures has
changed in the datastore (users should not rely on that). In
particular, the ruptures are now stored as a nice HDF5 structure and
not as pickled objects, something that we wanted to achieve for
years.

Also, we fixed the storing of the composite risk model object
which now can be extracted from the datastore (before it could only be
saved). This allowed some simplifications in the risk calculators.

A lot of refactoring of the risk calculators (all of them) went
in. The code for computing the statistical outputs of the risk
calculators has been completely rewritten and it is now 90% shorter
than before and more efficient.

Finally, a lot of work went into the UCERF calculators. However,
the should still be considered experimental and there are a few known
limitations about those. This is why they are still undocumented.
