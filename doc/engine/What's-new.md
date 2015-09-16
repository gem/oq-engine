OpenQuake 1.5 is a major release and a big improvement with respect
to OpenQuake 1.4. Overall in this release more than 110 bugs/feature
requests were fixed/implemented and everybody should upgrade.

New features of the OpenQuake Engine, version 1.5.
--------------------------------------------------

1. The most important new feature is the *support for the HDF5
technology*. Starting from OpenQuake 1.5 the scientific calculators
are starting to save their inputs and outputs into a single HDF5 file,
called the datastore. The HDF5 file format is a well known standard in
the scientific community, can be read/written by a variety of
programming languages and with different tools and it is a
state-of-the-art technology when it comes to manage large numeric
datasets. The change has *huge* performance benefits compared to
storing arrays in PostgreSQL, as we did until now.

2. Related to the first point, in OpenQuake 1.5 *the event based
calculators (both hazard and risk) are officially deprecated*. They
are still there, but they will be replaced with new calculators based
on the HDF5 technology in OpenQuake 1.6. The change will
have no impact on regular users (they will just see better
performances) but it will change things for power users doing queries
on the OpenQuake database (there will be nothing in the database!).

3. In order to make the transition easier, OpenQuake 1.5 includes the
new calculators, so that it is possible to use them right now.
The new calculators can be run in OpenQuake 1.5 with the
command

  $ oq-engine --lite --run job.ini

If you do not pass the ``--lite`` flag the old calculators will be
run. In future releases the old calculators will be progressively
removed and at the end of the process (which will take several
releases) the ``--lite`` flag will be removed. All calculators
will be lite and all the calculators relying on the database will disappear.
The OpenQuake database will only contains accessory informations
(essentially a table with the users and references to the outputs
of each user) but nothing relevant for the scientific computation.

4. The ``--lite`` calculators are not fully functional yet; for
instance, among the hazard calculators, the disaggregation calculator
is completely missing. It will be added in future releases; for the
moment you will have to use the old calculator, which is not deprecated.
The other hazard calculators (classical, event based and scenario) are
complete; the classical_tiling calculator is complete but relatively
new and not battle tested yet. The risk calculators are at different
level of completion; the only one which is recommended is the
event based one.

5. Internally, the ``--lite`` calculators are totally different from
the old calculators based on Postgres , *however they produce
identical results*.  They implement the same science and any
difference should be reported as a bug. There could be minimal
discrepancies due to numerical errors, but nothing more than that. The
event based ``--lite`` calculators are faster by order of magnitudes,
especially in large calculation, both because of the HDF5 technology
and also because they compute the ground motion fields on the fly,
thus avoiding any wasted time in saving/reading large amount of data,
as the old calculators did. It is recommended that you start using
them in preference to the engine ones.

6. OpenQuake 1.5, as a special preview of the future, is able to
manage a new kind of vulnerability functions, in which you you can
specify the Probability Mass Function (PMF) numerically.  This is a
feature that will enter officially in the new version of our XML data
format, NRML 0.5, but it is already available unofficially. For the
moment NRML 0.4 is not deprecated.  In OpenQuake 1.6 we will support
other kinds of vulnerability and fragility functions in the format
NRML 0.5 and NRML 0.4 may be deprecated. In that case a conversion
script will be provided to convert input files from NRML 0.4 to
NRML 0.5.

7. For the first time, *hazardlib officially supports Python 3*.  We
are testing it with Python 3.4 using the Travis continuous integration
system and we are committed to keep it compatible both with Python 2.7
and Python 3.4 and higher for the foreseeable future. There is no plan
to abandon Python 2.7 any time soon, but there is plan is to extend
the support both Python 2.7 and Python 3.4+ to risklib and the
engine. However, this is long term and low priority process: do not
expect anything before 2016.

8. It is now possible to pass string parameters to GSIM classes,
directly from the XML representation of the logic tree. This is
of interest only to users writing GSIMs, and they can just
read the related pull request for the details:
https://github.com/gem/oq-risklib/pull/346

9. The passing-parameters-to-GSIMs feature has been used to implement
the Canada hazard model, which has GMPE based on a set of binary tables.
Several other features have been implemented in hazard and you can
see the full list in the changelog](https://raw.githubusercontent.com/gem/oq-hazardlib/engine-1.5/debian/changelog)
10. The oq-lite command-tool has been enhanced; it is possible to use
it to execute the same calculations that you would run with the command
``oq-engine --lite``. The difference is that ``oq-lite`` only works
on a single machine, not on the cluster. On the plus side, it does
not require having a celery instance up and running. ``oq-lite``
is also especially useful to perform analysis before you run a large
computation on the engine. It is recommended to run

$ oq-lite info --report <my_job.ini>

to generate a text file with a report on the expected size
of your computation before you start anything large. Currently
the functionality only works for hazard calculation
but it is expected to grow in the future.

8. A lot more improvements have been made to oq-lite, too many to list
them all; see the [changelog](https://raw.githubusercontent.com/gem/oq-risklib/engine-1.5/debian/changelog) for the complete list.

10. We added a functionality `write_source_model` to serialize sources in XML.
Also we improved the reading of XML files and the error message in case of
invalid files. Finally, we have removed the dependency on lxml, thus making
the OpenQuake suite more portable across different platforms and easier
to install.

11. We added a check on the site parameters distance. If the site
parameters for a site are read from a site model file, and the
distance of the parameters from the site is larger than 5 km, a
warning is raised. The goal is to signal the user if she used an
incorrect site model file with respect to the sites she is using. The
calculation still runs and complete, since sometimes you may not have
site parameters data close enough to the sites of interests.

12. We have parallelized the source splitting procedure with a good
performance boost. There is also a flag
`parallel_source_splitting` in openquake.cfg to disable the
feature (default: true)

Support for different platforms
----------------------------------------------------

OpenQuake 1.5 fully supports both Ubuntu 12.04 and Ubuntu 14.04
and we provide packages for both platforms. However
starting from OpenQuake 1.6 *we will release packages only for Ubuntu 14.04*.
Ubuntu 12.04 will still be supported but you will have to install some
dependency which is not in the repositories of Ubuntu 12.04. The reason
for the change is that the HDF5 libraries for Ubuntu 12.04 are
too old (over 4 years old), buggy and less performants than
the ones for Ubuntu 14.04, which is now our official development platform.
It is too costly for us to mantain compatibility with such ancient
software, so users wanting to use OpenQuake 1.6 on Ubuntu 12.04
will have to install manually the library h5py (version 2.2.1)
and its dependencies. We will provide instructions for that in
the next release, since for the moment this is not necessary.

We have detailed instructions to install the engine on CentOS 7
and Fedora and in general of [Red Hat Enterprise Linux clones]
(Installing-the-OpenQuake-Engine-from-source-code-on-Fedora-and-RHEL.md)

While the engine is not supported on Windows and Mac OS, we are
happy to report that the underlying libraries and the
`oq-lite` command-line tool run just fine. We do not offer
any automatic tool to perform the installation, but there is
a guide to help you to install the necessary dependencies

Bug fixes and changes with respect to OpenQuake 1.5
----------------------------------------------------

1. Over 30 new tests have been added for the event based risk
calculator, and a few new tests have been added also for the event
based hazard calculator. It was a *huge* effort on the part of
both our scientific team and IT team. The net result is that
a lot of subtle and hard-to-find bug have been discovered and
fixed. The list is so long that is has been moved to a separated
document that you can find [here](event-based-bugs.md).

2. The algorithm to compute average losses and average insured losses
in the event based risk calculator has been changed: it is now
more robust since it does not rely on the discretization of
the loss curves, but directly on the underlying losses. As a
consequence the numbers for the average losses are different than in previous
versions of OpenQuake. The difference is compatible with the error
that we had before.

3. The event based disaggregation feature has been removed; same for
the Event Based Benefit Cost Ratio calculator. They were buggy and
they will be reintroduced in the future within the new system, in
the engine codebase or as part of the Risk Modeller Toolkit.

4. Longitude and latitude are now rounded to 5 digits after the
decimal point directly from Python; before the rounding happened
inside PostGIS. As a consequence, if the locations of your assets have
more than 5 digits, there are small differences in the numbers
produced by the engine, compared to previous versions.

5. The parameter `investigation_time` has been replaced by
`risk_investigation_time` in risk configuration files

6. Removed the `bin/openquake` wrapper, which has been deprecated
for ages: now only `bin/oq-engine` is available

7. The parameter `concurrent_tasks` is read from the .ini file and
honored; before it was read from the openquake.cfg file, but
ignored by the risk calculators.

8. We changed the convention to generate the rupture tags; now
the tags do not contain pipes "|" anymore. This character caused problems
on Windows, since one of the NRML converters was using the tag to
generate a file with the same name containing the corresponding
ground motion field.
