Here are the new features of the OpenQuake Engine, version 1.5.

1. The most important new thing is the support for the HDF5
technology. Starting from OpenQuake 1.5 the oq-lite calculators are
able to save their input and outputs on a single HDF5 file, called the
datastore. The HDF5 file format is a standard in the scientific
community, can be read/written by a variety of programming languages and
with different tools and it is the best technology there is to manage
large numeric datasets.

2. Related to the first point, *the engine calculators are officially
deprecated* and they will replaced with the oq-lite calculators
starting from OpenQuake 1.6. This will have no impact on regular users
(they will just see better performances) but it will change everything
for power users doing queries on the OpenQuake database. In the future
there will be nothing left in database, since everything will be
stored in the datastore.

3. In order to help our power users, OpenQuake 1.5 does not remove
the old calculators but it includes the new calculators, so
that it is possible to have a glimpse of the future. The new
calculators can be run in OpenQuake 1.5 with the command

  $ oq-engine --run job.ini --lite

If you do not pass the ``--lite`` flag the old calculators will be
run. In future releases the old calculators will be progressively
removed and at the end of the process (which will take several
releases) the ``--lite`` flag will be removed. All calculators
will be lite and all the current calculators will have disappeared.
The OpenQuake database will only contains accessory informations
(essentially a table with the users and references to the outputs
of each user).

4. The oq-lite calculators are not yet fully functional; for
instance, among the hazard calculators, the disaggregation calculation
is completely missing. It will be added in future releases; for the
moment you will have to use the old calculator, which is not deprecated.
The othe hazard calculators (classical, event_based and scenario) are
complete; the classical_tiling calculator is complete but relatively
new and not battle tested yet. The oq-lite risk calculators are at different
level of completion; the only ones which are recommended are the
event based ones.

4. The oq-lite event based calculators have been rewritten, both
for hazard and risk. The risk calculator computes the GMFs on the fly.
That means an improvement of order of magnitudes both in the running
time and the memory occupation with respect to the old engine calculator.
It is recommended that you start using it in preference to the engine one.

5. The event based disaggregation feature has been removed; same for
the Event Based BCR. They were buggy and they will be reintroduced in
the future within the new system.

2. Longitude and latitude are now rounded to 5 digits after the
decimal point directly from Python; before the rounding happened
inside PostGIS. As a consequence, if the locations of your assets have
more than 5 digits, there are small differences in the numbers
produced by the engine, compared to previous versions

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
