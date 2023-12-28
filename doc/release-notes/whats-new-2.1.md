Release notes v2.1
==================

This release has focused on memory optimizations, with the goal of
making the engine able to tackle extremely large calculations.

We were able to successfully run event based risk calculations
two orders of magnitudes larger than ever attempted before and
classical hazard calculations one order of magnitude larger.

Moreover, as usual, new ground motion prediction equations entered in
hazardlib, various improvements were made to the Web UI and several
bugs were fixed. Over two hundred pull requests were closed in the GEM
repositories.

For the complete list of changes, please 
see the changelogs: https://github.com/gem/oq-hazardlib/blob/engine-2.1/debian/changelog and https://github.com/gem/oq-engine/blob/engine-2.1/debian/changelog.

A brief summary follows.

New features in OQ-Hazardlib
-----------------------------

- Added several new magnitude scaling relations including that of
  Leonard (2014) as well as locally calibrated magnitude-area scaling
  relations for Western Canada. We wish to acknowledge contributions
  from Jonathan Griffin (Geoscience Australia) and Trevor Allen
  (Geological Survey of Canada).

- Introduced new distance calculators for use with the multi-surface
  rupture class based on the Generalised Coordinate System GC2. This
  redefines distance metrics for ground motion model hanging wall
  terms (Rx and Ry0) for compatibility with multi-surface faults,
  allowing for discontinuity and/or discordance in the rupture
  geometry.

- Added the European regionalised GMPE of Kotha, Bindi and Cotton (2016).
   
- Added the GMPE of Travasarou, Bray and Abrahamson (2003) for Arias
  Intensity (credit Cigdem Yilmaz).

- Added the GMPE of Hong & Goda (2007) for SaRotD100 (the
  directionally adverse envelope of ground motion).

New engine optimizations
-----------------------------

- Previously very large classical calculations were impossible,
  because the engine would run out of memory when generating the hazard
  curves from the hazard probabilities. Now this has been fixed, and we
  could run large calculations such as the SHARE model with 3,200
  realizations and 127,000 sites in just 9 hours.

- Large event based risk calculations were impossible, because we could
  not keep in memory the ground motion fields. Now this has been fixed
  and we are able to run models with thousands of realizations and thousands
  of sites in a few hours.

- Now the complete source model is prefiltered with the rtree library
  if available. That makes it possible to remove sources which are
  outside of the integration distance even before sending them to the
  workers. This makes no practical difference for small computations,
  but makes a huge difference for large computations.

- The task distribution has been improved by improving the source
  splitting and source weighting. There are still tasks that are slower
  than others, but less so than in the past, so it is less likely to
  have a computation waiting forever because there is a single slow
  task which has not finished yet.

- We reduced the data transfer, especially for computations with a lot
  of realizations, by performing several refactorings and cleanups of the
  code.

- We improved the parallelism of the disaggregation calculator and we added
  more correctness checks on the input configuration file.

- We improved the parallization infrastructure and now we are ready
  to support the IPython parallization mechanism.

- The database server is now independent from the Django ORM, it does
  not use threads anymore and it can be stopped correctly with CTRL-C.

- We improved the XML parsing utilities in speed, memory, portability and
  ease of use.

New engine features
-------------------

- There is a new experimental calculator called `ebrisk` which is a lot
  faster than the official `event_based_risk` calculator. However, it is
  not able to compute loss curves or insured losses, and does not take
  into consideration asset correlation.

- It is now possible to recompute hazard curves/hazard maps/hazard spectra
  without repeating the whole computation. Just edit the job.ini file and
  pass to the engine the ID of the original calculation:

```bash
$ oq engine --run job.ini --hc <calc_id>
```

- We refined the HDF5 exports for hazard curves, hazard maps and uniform
  hazard spectra and added an experimental HDF5 export for scenario GMFs.

- The format NRML 0.5 has been introduced for source models since it will be
  used by the Japan model in the future. The old NRML 0.4 format is still used
  and there is no intention to deprecate it.

- We started to port some of the features of the repository
  `nrml_converters` into the engine. The plan for the future is to make
  the `nrml_converters` obsolete, but this is not the case yet. For the
  moment we ported the converters from NRML to shapefile and back; the
  commands to use are:

```bash
$ oq to_shapefile [-o OUTPUT] input_nrml_file
$ oq from_shapefile [-o OUTPUT] input_shp_files [input_shp_files ...]
```

- Several small improvements and fixes were made to the Web UI. Now
  it is also possible to download the full datastore.

Changes and deprecations
------------------------

- We added a header to the exported CSV files for the hazard curves,
  hazard maps and uniform hazard spectra.
- We changed the event loss table CSV exporter: now a single file per
  realization is exported, containing all the loss types; moreover, there
  is an additional column with the number of the event-set to which the event
  belongs.
- We no longer provide deb binary packages for Ubuntu 12.04 LTS (Precise).

