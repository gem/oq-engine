Architecture of the OpenQuake Engine v2+
=========================================

The OpenQuake Engine version 2 is a complete rewrite of version
1.0, so a new document describing the overall architecture is
needed. Whereas in the past the Engine was database-centric and
structured as a Web application with an Object Relational Mapper, now
it is calculation-centric and structured as a scientific application:
everything is done in memory and in the core
engine there is no database, nor ORM. Intermediate results are stored
in HDF5 format. In the calculators we work as much as possible in
terms of arrays which are efficiently manipulated at C/Fortran speed
with a stack of well established scientific libraries (numpy/scipy).

Design principles
-----------------

The main design principle has been *simplicity*: everything has to be
as simple as possible (but not simplest). The goal has been to keep
the engine simple enough that a single person can understand it, can
debug it and can extend it without tremendous efforts. All the rest
comes from simplicity: transparency, ability to inspect and debug, modularity,
adaptability of the code, etc. Even efficiency: in the last three
years most of the performance improvements came from free, just from
removing complications. When a thing is simple it is easy to make it
fast. The battle for simplicity is never ending, so there are still
several things in the engine that are more complex than they should:
we are working on that.

After simplicity the second design goal has been *performance*: the
engine is a number chrunching application after all, and we need to run
massively parallel calculations taking days or weeks of
runtime. Efficiency in terms of computation time and memory
requirements is of paramount importance, since it makes the difference
between being able to run a computation and being unable to do it.
Being too slow to be usable should be considered as a bug.

The third requirement is *reproducibility*, which is the
same as testability: it is essential to have a suite of tests checking
that the calculators are providing the expected outputs against a set
of predefined inputs.  With respect to OpenQuake Engine 1.0 we have at
least tripled the number of scientific tests. We are testing a lot more
corner cases and a lot more functionalities. On the other hand several
programming unit tests have been removed: they were testing
implementations details of an implementation that has been removed and
replaced with a simpler one.

Components of the OpenQuake Engine
-----------------------------------

The OpenQuake Engine suite is composed of several components:

- a set of *support libraries* addressing different concerns like reading the
  inputs and writing the outputs, implementing basic geometric manipulations,
  managing distributed computing and generic programming utilities
- the *hazardlib* and *risklib* scientific libraries,
  providing the building blocks for hazard and
  risk calculations, notably the GMPEs for hazard and the
  vulnerability/fragility functions for risk
- the hazard and risk *calculators*, implementing the core logic
  of the engine
- the *datastore*, which is an HDF5 file working as a short term storage/cache
  for a calculation; it is possible to run a calculation starting from an
  existing datastore, to avoid recomputing everything every time; there is a
  separate datastore for each calculation
- the *database*, which is a SQLite file working as a long term storage for the
  calculation metadata; the database contains the start/stop times of the
  computations, the owner of a calculation, the calculation descriptions,
  the performances, the logs, etc; the bulk scientific data
  (essentially big arrays) are kept in the datastore
- the *database server*, which is a service mediating the interaction
  between the calculators and the database
- the *Web UI* is a web applications that allows to run and monitor
  computations via a browser; multiple calculations can be run in parallel
- the *oq* command-line tool; it allows to run computations
  and provides an interface to the underlying
  database and datastores so that it is possible to list and export the results
- the engine can run on a cluster of machines: in that case
  you have to start the *rabbitmq* and *celery* components which
  are not required on a single machine installation. In that case a
  minimal amount of configuration is needed, whereas in single machine
  installations the engine works out of the box

This is the full stack of internal libraries used by the engine: each of those
is a Python package containing several modules or event
subpackages. The stack is a dependency tower where the higher levels
depend on the lower levels but not viceversa:

- level 8: commands (commands for oq script)
- level 7: server (database and Web UI)
- level 6: engine (command-line tool, export, logs)
- level 5: calculators (hazard and risk calculators)
- level 4: commonlib (configuration, logic trees, datastore, I/O)
- level 3: risklib (risk validation, risk models, risk inputs)
- level 2: hazardlib (validation, read/write XML, source and site objects, geospatial utilities, GSIM library)
- level 1: baselib (programming utilities, parallelization, monitoring, Python 3 compatibility)

`baselib` and `hazardlib` are very stable and can be used outside of the
engine; the other libraries are directly related to the engine and
are likely to be affected by backward-incompatible changes in the future,
as the code base evolves.

The GMPE library in `hazardlib` and the calculators are designed
to be extensible, so that it is easy to add a new GMPE class or a new
calculator. We routinely add several new GMPEs per release; adding new
calculators is less common and it requires more expertise, but it is possible
and it has been done several times in the past. In particular it is
often easier to add a specific calculator optimized for a given use case rather
than complicating the current calculators.

The results of a computation are automatically saved in the datastore
and can be exported in a portable format, such as XML or CSV.  You can
assume that the datastore of version X of the engine *will not work*
with version X + 1: on the contrary, the exported files will likely be
same across different versions. It is important to export all of the
outputs you are interested in before doing an upgrade, otherwise you
would be forced to downgrade in order to be able to export the previous
results.

The WebUI provides a REST API that can be used in third party
applications: for instance a QGIS plugin could download the maps
generated by the engine via the WebUI and display them. There is lot
of functionality in the API which is documented here:
https://github.com/gem/oq-engine/blob/master/doc/web-api.md. It is
possible to build your own user interface for the engine on top of it,
since the API is stable and kept backward compatible.
