New features of the OpenQuake Engine, version 2.1
-------------------------------------------------

This release has focused on memory optimizations, with the goal of
making the engine able to tackle extremely large calculations.

For small calculations you will not see big differences (for instance
the demos runs at the same speed of the previous release) however for
large calculations, with logic trees of thosands of realizations,
this release provide *huge* improvements. With engine 2.0 all the
realizations had to be kept in memory, now only one realization at the
time need to be kept in memory.

1. Previously extremely large classical calculations where impossible, because
the engine would run out of memory when generating the hazard curves from
the hazard probabilities. Now this has been fixed, and we could run large
calculations such as the SHARE model with 3,200 realizations and 127,000 sites.

2. Also large event based risk calculations were impossible, because
of memory issue. This release, for a computation with thousands of
realizations, needs thousand of times less memory than before.

* Improved the parallelism of the disaggregation calculator by
splitting then heavy sources; also added some checks on the job.ini

  * Added an optimized event based calculator ebrisk
5. We reduced the data transfer, especially for computations with a lot
of realizations, in three ways:

   - we reduced the RlzsAssoc object
   - we removed the automatic tiling functionality from the classical
     calculator;
   - we reduced the source splitting
     
  * Finalized the HDF5 export for hazard curves, hazard maps and uniform
    hazard spectra
* Added an HDF5 export for scenario GMFs

  * Changed the event loss table exporter: now a single file per realization
  is exported, containing all the loss types

- we reduced the split of sources and the weights;

4. The task distribution has been improved. There are still tasks that are
slower than others, but less so than in the past, so it is less likely to
have a computation waiting forewer because there is a single slow task which
has not finished yet.

4. We improved the distribution infrastructure

5. Now the complete source model is prefiltered with the rtree library
if available. That makes it possible to remove sources which are outside
of the integration distance even before sending them to the workers,
so that the data transfer is reduced. If you do not have the rtree
library installed, a slower filtering will be used. This makes no
practical difference for small computations, but a huge difference for
large computations. If you have several thousands of sources and sites
you should really install rtree.

4. Several small improvements and fixes were made to the Web UI. Now
it is also possible to download the full datastore.

6. The database server is now independent from the Django ORM.
* Now the dbserver can be stopped correctly with CTRL-C

5. We added an header to the exported CSV files for the hazard curves,
maps and spectra

6. It is now possible to recompute hazard curves/hazard maps/hazard spectra
without repeating the whole computation. Just edit the job.ini file and
pass to the engine the ID of the original calculation:

```bash
$ oq engine --run job.ini --hc <calc_id>
```

7. We start to port some of the features of the repository `nrml_converters`
into the engine. The plan for the future is to make the `nrml_converters`
obsolete, but this is not the case yet. For the moment we ported the
converters from NRML to shapefile and back; the command to use are

```bash
$ oq to_shapefile [-o OUTPUT] input_nrml_file
$ oq from_shapefile [-o OUTPUT] input_shp_files [input_shp_files ...]
```

9. The format NRML 0.5 has been introduced for source models since it will be
used by the Japan model in the future. The old format NRML 0.4 is still used
and there is no intention to deprecated it.

8. We improved the XML parsing utilities in speed, memory, portability and
easy of use.
  
10. As usual a lot of bug fixes were implemented. For the complete list
see the changelogs: https://github.com/gem/oq-hazardlib/blob/engine-2.0/debian/changelog and https://github.com/gem/oq engine/blob/engine-2.0/debian/changelog.
Over two hundred pull requests were closed in the GEM repositories.


---- Deprecation ----

 "we no longer provide deb binary packages for *Ubuntu 12.04* LTS (Precise)"
