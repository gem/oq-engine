OpenQuake 1.5 is a major release and a big improvement with respect
to OpenQuake 1.4. More than 110 bugs/feature
requests were fixed/implemented. Everybody is invited to upgrade,
by following the [usual procedure](Installing-the-OpenQuake-Engine.md).

New features of the OpenQuake Engine, version 1.5
--------------------------------------------------

1. The most important new feature is the *support for the HDF5
technology*. Starting from this release the scientific calculators
are starting to save their inputs and outputs in a single HDF5 file,
called the datastore. The HDF5 file format is a well known standard in
the scientific community, can be read/written by a variety of
programming languages and with different tools and it is a
state-of-the-art technology when it comes to managing large numeric
datasets. The change to HDF5 provides *huge* performance benefits 
compared to the earlier approach used by the engine, which involved 
storing arrays in PostgreSQL.

2. Related to the first point, in OpenQuake 1.5 *the event based
calculators (both hazard and risk) based on Postgres are officially 
deprecated*. They are still present and work as before, but they are 
being replaced with new versions of the calculators based on the 
HDF5 technology.  The replacement of the old calculators with the 
new ones will start from OpenQuake 1.6. This change will have no impact 
on regular users, who will simply notice large improvements in performance 
of the calculators. But this change will affect power users who are 
performing queries on the OpenQuake database, since there will be nothing 
in the database once we replace the old calculators based on Postgres 
with the new versions based on HDF5.

3. In order to make the transition easier, OpenQuake 1.5 already includes 
the new versions of the event based calculators based on HDF5, so it 
is possible to use them right now. The new calculators can be run in 
OpenQuake 1.5 with the command ``$ oq-engine --lite --run job.ini``.
If you do not pass the ``--lite`` flag the old calculators will be
run by default. In future releases all of the old calculators will be 
progressively replaced by the new calculators based on HDF5. At the end of 
this process, which will be spread over the upcoming releases, 
the ``--lite`` flag will be removed. All of the old calculators 
relying on the database will be replaced internally by the newer 
"lite" versions based on HDF5 and the old calculators based on Postgres 
will not be available anymore. The OpenQuake database will only contain 
accessory information (essentially a table with the users and references 
to the outputs of each user) but nothing relevant for the scientific 
computation will be stored in the database going forward.

4. The ``--lite`` versions of the calculators are not all fully 
functional yet; for instance, among the hazard calculators, 
the disaggregation ``--lite`` calculator is absent in OpenQuake 1.5. 
Work on this calculator is in progress, and it will be added in a 
future release; for the moment you will have 
to use the old calculator, which is not deprecated in OpenQuake 1.5.
The ``--lite`` versions of the other hazard calculators 
(scenario hazard, classical hazard, and event based hazard) are complete. 
The ``--lite`` version of the classical_tiling calculator is also complete 
but relatively new and has not been battle tested yet. The ``--lite`` 
versions of the risk calculators are at different levels of completion; 
the only ``--lite`` risk calculator we recommended using in this release 
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
thus avoiding the large amount of time wasted in saving/reading 
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

7. For the first time, *hazardlib officially supports Python 3*.  We
are testing it with Python 3.4 using the Travis continuous integration
system and we are committed to keep it compatible both with Python 2.7
and Python 3.4 and higher for the foreseeable future. There is no plan
to abandon Python 2.7 any time soon, but there is a plan to extend
the support for both Python 2.7 and Python 3.4+ to risklib and the
engine. However, this will be a long term and low priority process: do not
expect anything definitive before 2016.

8. It is now possible to pass string parameters to GSIM classes,
directly from the XML representation of the logic tree. This is
of interest only to users writing GSIMs, and they can 
read the related pull request for the relevant details:
https://github.com/gem/oq-risklib/pull/346

9. The passing-parameters-to-GSIMs feature has been used to implement
the Canada hazard model, which has GMPE based on a set of binary tables.
Several other features have been implemented in hazard and you can
see the full list in the [changelog](https://raw.githubusercontent.com/gem/oq-hazardlib/engine-1.5/debian/changelog)

10. The oq-lite command-tool has been enhanced; it is possible to use
it to execute the same calculations that you would run with the command
``oq-engine --lite``. The difference is that ``oq-lite`` only works
on a single machine, not on the cluster. On the plus side, it does
not require having a celery instance up and running. ``oq-lite``
is also especially useful to perform some preliminary analysis before you 
run a large computation on the engine. Running 
``$ oq-lite info --report <my_job.ini>``
will generate a text file with a report on the expected size
of your computation before you start anything large. Currently
the functionality only works for hazard calculations
but it is expected to grow in the future.

11. Several other improvements have been made to oq-lite, too many to list
them all here; please see the [changelog](https://raw.githubusercontent.com/gem/oq-risklib/engine-1.5/debian/changelog) for the complete list.

10. We added a functionality `write_source_model` to serialize sources in XML.
Also we improved the reading of XML files and the error message in case of
invalid files. Finally, we have removed the dependency on lxml, thus making
the OpenQuake suite more portable across different platforms and much easier
to install.

11. We added a check on the site parameters distance. If a site model
file is provided in a hazard calculation, and if no site parameters are
available within a radius of 5 km for a particular site, a
warning is raised. The goal is to signal the user if she used an
incorrect site model file with respect to the sites she is using. The
calculation still runs and complete, since sometimes you may not have
site parameters data close enough to the sites of interests.

12. We have parallelized the source splitting procedure with a good
performance boost. There is also a flag
`parallel_source_splitting` in openquake.cfg to disable this
feature (default: true)

Support for different platforms
----------------------------------------------------

OpenQuake 1.5 fully supports both Ubuntu 12.04 and Ubuntu 14.04
and we provide packages for both platforms. However
starting from OpenQuake 1.6 *we will release packages only for Ubuntu 14.04*.
Ubuntu 12.04 will still be supported but you will have to install some
dependencies which are not in the repositories of Ubuntu 12.04. The reason
for the change is that the HDF5 libraries for Ubuntu 12.04 are
too old (over 4 years old), buggy and less efficient compared to 
the ones for Ubuntu 14.04, which is now our official development platform.
It is too expensive for us to mantain compatibility with such ancient
software, so users wishing to use OpenQuake 1.6 on Ubuntu 12.04
will have to install manually the library h5py (version 2.2.1)
and its dependencies. We will provide instructions for that in
the next release, since for the moment this is not necessary.

We have detailed instructions for installing the engine on CentOS 7
and Fedora and in general of [Red Hat Enterprise Linux clones]
(Installing-the-OpenQuake-Engine-from-source-code-on-Fedora-and-RHEL.md)
The engine works on several Linux distributions, even recent ones
like Ubuntu 15.04, and it has less dependencies than it used to have in
the past and it is easier to install.

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
fixed. The list of bug-fixes is so long that is has been moved to a separated
document that you can find [here](event-based-bugs.md).

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
honored; in earlier versions it was read from the openquake.cfg file, 
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
the job.ini file only for those site parameters that are actually used
by your calculation. In earlier versions, users were asked to specify 
site parameters even if they weren't required for the calculation.

11. We fixed a bug with the ``oq-engine --load-curve`` command, such
that is was impossible to load a hazard curve.

12. We improved the error reporting on the engine; earlier, an error in
the cleanup phase could hide the real underlying error.

13. We fixed an error for the degenerate case of hazard curves
containing all zeros, as this corner case was reported by some users 
on the OpenQuake users group.
