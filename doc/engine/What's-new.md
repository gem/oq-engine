Here are the new features of the OpenQuake Engine, version 1.5.

1. The event based calculators have been completely rewritten, both
for hazard and risk. Now they do not rely on the database; the ground
motion fields and the corresponding hazard curves are stored directly
in a HDF5 file. The risk calculator computes the GMFs on the fly and
that means an improvement of order of magnitudes both in the running
time and the memory occupation. The Event Based BCR calculator has
been removed; same for the event based disaggregation feature. They
were buggy and they will be reintroduced in the future within the new
system.

2. Longitude and latitude are now rounded to 5 digits directly from Python;
before the rounding happened inside PostGIS. As a consequence, if the
locations of your assets have more than 5 digits, there
are small differences in the numbers produced by the engine, compared
to previous versions

3. Fixed a very subtle bug in the vulnerability functions, potentially
affecting calculations with nonzero coefficients of variation and
nonzero minIML; the numbers produced by the engine were incorrect;
see https://bugs.launchpad.net/oq-engine/+bug/1459926

4. `investigation_time` has been replaced by `risk_investigation_time` in
risk configuration files

5. Removed the bin/openquake wrapper: now only bin/oq-engine is
available

6. The parameter concurrent_tasks is read from the .ini file and
honored; before it was read from the openquake.cfg file, but
ignored by several calculators.

7. Parallelized the source splitting procedure and added a flag
parallel_source_splitting in openquake.cfg (default: true)

8. A lot of improvements have been made on oq-lite, too many to list
them all; see the [changelog](https://raw.githubusercontent.com/gem/oq-risklib/engine-1.5/debian/changelog)

9. The most important new feature is the command
`oq-lite info --report job.ini` which generates a `report.rst` file containing
precious information about a calculation; for the moment it only addresses
hazard calculation

10. Added a functionality `write_source_model` to serialize sources in XML


10 Added vulnerability functions with Probability Mass Function

12. Overall in this release more than XXX bugs/feature requests were fixed/implemented.