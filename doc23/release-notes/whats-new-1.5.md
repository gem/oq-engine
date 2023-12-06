What's new in engine-1.5
========================

OpenQuake 1.5 is a major release and a big improvement with respect
to OpenQuake 1.4. More than 115 bugs/feature
requests were fixed/implemented.

New features of the OpenQuake Engine, version 1.5
--------------------------------------------------

1. The most important new feature is the *support for the HDF5
technology*. Starting from this release some of the scientific
calculators are saving their inputs and outputs in a single HDF5 file,
called the datastore. The HDF5 format is a well known standard in
the scientific community, can be read/written by a variety of
programming languages and with different tools and it is a
state-of-the-art technology when it comes to managing large numeric
datasets. The change to the HDF5 technology provides *huge*
performance benefits compared to the earlier approach used by the
engine, which involved storing arrays in PostgreSQL.

2. Related to the first point, in OpenQuake 1.5 *the event based
calculators based on Postgres (both hazard and risk) are officially 
deprecated*. They are still present and work as before, but they are 
being replaced with new versions of the calculators based on the 
HDF5 technology.  The actual removal of the old calculators
is scheduled for OpenQuake 1.6. The change will have no impact 
on regular users, who will simply notice a definite improvement in
erformance. Nonetheless, the change will affect power users who are 
performing queries on the OpenQuake database, since there will be nothing 
left in the database once we remove the old calculators.

3. In order to make the transition easier, OpenQuake 1.5 already includes 
the new versions of the event based calculators based on HDF5, so it 
is possible to use them right now. The new calculators can be run in 
OpenQuake 1.5 with the command
``$ oq-engine --lite --run job_haz.ini,job_risk.ini``.
If you do not pass the ``--lite`` flag the old calculators will be
run by default. In future releases of the engine, the remaining
calculators based on Postgres will be 
progressively replaced by the new calculators based on HDF5. At the end of 
this process, which will be spread over several upcoming releases, 
the ``--lite`` flag will be removed. All of the old calculators 
relying on the database will be replaced internally by the newer 
"lite" versions based on HDF5 and the old calculators
will not be available anymore. The OpenQuake database will only contain 
accessory information (essentially a table with the users and references 
to the outputs of each user) but nothing relevant for the scientific 
computation.

4. At the moment, the ``--lite`` flag does not work for all calculators.
For instance, among the hazard calculators, 
the disaggregation ``--lite`` calculator is absent in OpenQuake 1.5. 
Work on this calculator is in progress, and it will be added in a 
future release; for the the time being, you will have 
to use the old calculator, which is not deprecated in OpenQuake 1.5.
The ``--lite`` versions of the other hazard calculators 
(scenario hazard, classical hazard, and event based hazard) are complete. 
The ``--lite`` version of the classical_tiling calculator is also complete 
but relatively new and has not been battle tested yet. The ``--lite`` 
versions of the risk calculators are at different levels of completion; 
the only ``--lite`` risk calculator we recommend using in this release 
is the event based risk calculator.

5. Internally, the ``--lite`` calculators are implemented very 
differently compared to the old calculators based on Postgres, 
*however they produce identical results*. They implement the same 
science and any noticable differences should be reported as a bug. 
There could be minimal discrepancies due to numerical errors, and 
changes in rounding, but nothing more than that. The
event based ``--lite`` calculators are faster by orders of magnitudes,
especially for large calculations, both because of the HDF5 technology
and also because they compute the ground motion fields on the fly,
thus avoiding the time wasted in saving/reading 
large amounts of data, as the old calculators did. It is recommended 
that you start using the ``--lite`` versions of the event based 
calculators in preference to the engine ones.

6. OpenQuake 1.5, as a special preview of the future, is able to
manage a new kind of vulnerability function, in which you can
specify the discrete Probability Mass Function (PMF) of the loss ratio at 
different ground motion intensity levels numerically. This is a
feature that will be officially introduced in the new version of our 
XML data format, NRML 0.5, but it is already available unofficially. 
For the moment NRML 0.4 is not deprecated. In OpenQuake 1.6 we will support
other kinds of vulnerability and fragility functions in the new format
NRML 0.5, and NRML 0.4 may be deprecated. In that case a conversion
script to convert input files from NRML 0.4 to NRML 0.5 will be provided.

7. For the first time, *hazardlib supports Python 3*.  The support is
at the beginning and the C-level speedups do not work yet. However,
we are already testing hazardlib with Python 3.4 by using the Travis
continuous integration system and we are committed to keep it
compatible both with Python 2.7 and Python 3.4+ for the
foreseeable future. There is no plan to abandon Python 2.7 any time
soon, but there is a plan to extend the support for
Python 3.4+ to risklib and the engine. However, this will be a
long term and low priority process: do not expect anything definitive
before 2016.

8. It is now possible to pass string parameters to GSIM classes,
directly from the XML representation of the logic tree. This is
of interest only to users writing GSIMs, and they can 
read the related pull request for the relevant details:
https://github.com/gem/oq-risklib/pull/346

9. The passing-parameters-to-GSIMs feature has been used to implement
support for the definition of ground motion prediction equations using
interpolation ('look up') tables. These allow the user to input
arbitrary GMPEs in the form of tables, rather than the parametric
equations currently supported. The tables, in HDF5 format, provide the
expected ground motion values for given magnitudes and distances, with
the additional option of amplifying the ground motions based on source
or site attributes. To use this option the user need only specify
`GMPETable(gmpe_table=path/to/table.hdf5)` in place of the
conventional GMPE. Further guidance regarding the construction of the
HDF5 files will be provided in the documentation in due course.

10. Near-fault directivity probabilistic seismic hazard
analysis for classical PSHA calculations with simple fault
sources was added to hazardlib. We implemented the most recent NGA-WEST2
directivity model and the associated GMPE which is, up to now,
the only GMPE model explicitly including the effect. More details
can be found in the manual.

11. Several other features have been implemented in hazard and you can
have a look at the [changelog](https://github.com/gem/oq-hazardlib/blob/engine-1.5/debian/changelog).

12. The ``oq-lite`` command-tool has been enhanced; it is possible to use
it to execute the same calculations that you would run with the command
``oq-engine --lite``. The difference is that ``oq-lite`` only works
on a single machine, not on a cluster. On the plus side, it does
not require having a celery instance up and running.

13. ``oq-lite`` is especially useful to perform preliminary analysis before you 
run a large computation on the engine. Running
``$ oq-lite info --report <my_job.ini>``
will generate a text report on the expected size
of the computation. It is recommended to generate such report
before you start anything large. Currently
the functionality only works for hazard calculations
but it is expected to grow in the future.

14. Several other improvements have been made to oq-lite, too many to list
them all; please see the [changelog](https://raw.githubusercontent.com/gem/oq-risklib/engine-1.5/debian/changelog) for the complete list.

15. We added a functionality `write_source_model` to serialize sources in XML.
Also we improved the reading of XML files and the error message in case of
invalid files. Finally, we have removed the dependency on lxml, thus making
the OpenQuake suite more portable across different platforms and easier
to install.

16. We added a check on the site parameters distance. If a site model
file is provided in a hazard calculation, and if no site parameters are
available within a radius of 5 km for a particular site, a
warning is raised. The goal is to signal the user if she used an
incorrect site model file with respect to the sites she is using. The
calculation still runs and complete, since sometimes you may not have
site parameters data close enough to the sites of interests.

17. We have parallelized the source splitting procedure with a good
performance boost. There is also a flag
`parallel_source_splitting` in openquake.cfg to disable this
feature, should the need arise (default: true).

Support for different platforms
----------------------------------------------------

OpenQuake 1.5 fully supports both Ubuntu 12.04 and Ubuntu 14.04
and we provide packages for both platforms. However,
starting from OpenQuake 1.6 *we will release packages only for Ubuntu 14.04*.
Ubuntu 12.04 will still be supported but you will have to install manually some
dependencies which are not in the repositories of Ubuntu 12.04. The reason
for the change is that the HDF5 libraries for Ubuntu 12.04 are
too old (over 4 year old), buggy and less efficient compared to 
the ones for Ubuntu 14.04, which is now our official development platform.
It is too expensive for us to mantain compatibility with such ancient
software, so users wishing to use OpenQuake 1.6 on Ubuntu 12.04
will have to install manually the library h5py (version 2.2.1)
and its dependencies. We will provide instructions for that in
the next release, since for the moment this is not necessary.

We have detailed instructions for installing the engine on CentOS 7
and Fedora and in general on [Red Hat Enterprise Linux clones]
(Installing-the-OpenQuake-Engine-from-source-code-on-Fedora-and-RHEL.md)
The engine works on several Linux distributions, even recent ones
like Ubuntu 15.04. It has less dependencies than it used to have in
the past and it is easier to install, so it should be relatively
simple to install it on any modern Linux distribution.

While the engine is not supported on Windows and Mac OS, we are
happy to report that the underlying libraries and the
`oq-lite` command-line tool run just fine. We do not offer
any automatic tool to perform the installation, but there is
a guide to help you to install the necessary dependencies.

Bug fixes and changes with respect to OpenQuake 1.4
----------------------------------------------------

0. The database schema has changed in a destructive way, by removing
a column in the ``hzrdi.hazard_site`` table and a column in the
``riskr.epsilon`` table. If your database contains important
data, export them or dump the database. You will not be able
to user OpenQuake 1.5 with an OpenQuake 1.4 database. The
upgrade procedure is the usual one ``oq-engine --upgrade-db``.

1. Over 30 new tests have been added for the event based risk
calculator, and a few new tests have been added also for the event
based hazard calculator. It was a **huge** effort on the part of
both our scientific team and IT team. The net result is that
a lot of subtle and hard-to-find bugs have been discovered and
fixed.

2. The algorithm to compute average losses and average insured losses
in the event based risk calculator has been changed: it is now
more robust since it does not rely on the discretization of
the loss curves, but directly on the underlying loss tables. As a
consequence the numbers for the average losses are different than in previous
versions of OpenQuake. The difference is compatible with the error
that we had before.

3. The event-based disaggregation feature has been removed; same for
event-based Benefit-Cost Ratio calculator. They were buggy and
they will be reintroduced in the future within the new system, in
the engine codebase or as part of the Risk Modeller's Toolkit.

4. Longitude and latitude are now rounded to 5 digits after the
decimal point directly from Python; earlier the rounding happened
inside PostGIS. As a consequence, if the locations of your assets have
more than 5 digits after the decimal point, there will be small 
differences in the numbers produced by the engine, 
compared to previous versions.

5. The parameter `investigation_time` has been replaced by
`risk_investigation_time` in risk configuration files

6. The `bin/openquake` wrapper, which has been deprecated
for ages, is now removed. Now only `bin/oq-engine` is available

7. The parameter `concurrent_tasks` is read from the .ini file and
honored; in earlier versions it was read from the *openquake.cfg* file, 
but was being ignored by the risk calculators.

8. We changed the convention used to generate the rupture tags; now
the tags do not contain pipes "|" as the tag separators. 
This character caused problems on Windows, since one of the NRML 
converters was using the tag to generate a file with the same name 
containing the corresponding ground motion field.

9. We changed the export order of the event loss table. Earlier, the values
were ordered by loss size, in decreasing order. Now they are first ordered
by rupture tag, and then by increasing loss size. We feel that this ordering
is more useful.

9. We have added some checks on source IDs and asset IDs, to avoid
having issues such as nonprintable characters or non-ASCII
characters in there. Also, we have limited the maximum length of
an identifier to 100 characters. Notice that descriptions are
unconstrained, as before, so there are no problems if you
want to name your sources using Chinese characters or in any 
other character set. The only restriction is that the XML file 
must be UTF8-encoded, according to the XML standard.

10. If you don't have a site model file, you need to provide values in
the *job.ini* file only for those site parameters that are actually used
by your calculation. In earlier versions, users were asked to specify 
site parameters even if they weren't required for the calculation.

11. We fixed a bug with the ``oq-engine --load-curve`` command, such
that is was impossible to load a hazard curve.

12. We improved the error reporting on the engine; earlier, an error in
the cleanup phase could hide the real underlying error.

13. We fixed an error for the degenerate case of hazard curves
containing all zeros, as this corner case was reported by some users 
on the OpenQuake users group.

14. Now the sites are ordered by longitude, latitude even when they
are extracted from a region, consistently with all other cases.
