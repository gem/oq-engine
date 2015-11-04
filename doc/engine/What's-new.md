OpenQuake 1.6 is a major release and a big improvement with respect
to OpenQuake 1.5. Everybody is invited to upgrade,
by following the [usual procedure](Installing-the-OpenQuake-Engine.md).

New features of the OpenQuake Engine, version 1.6
--------------------------------------------------

1. The following six calculators have been completely rewritten and now
use the HDF5 technology that in previous versions was still experimental:

  1. scenario hazard
  2. scenario risk
  3. scenario_damage
  4. event_based_rupture
  5. event_based
  6. event_based_risk

As a consequence all such calculators are now much faster and use a
lot less memory than before. Even the disk space occupation has been
drastically reduced, and large computations that before took terabytes
of disk space now require few gigabytes of disk space. Such
calculators do not store anymore anymore their outputs in the
database, but in an HDF5 file located by default in
``$HOME/oqdata/calc_XXX.hdf5``.

2. The other calculators are unchanged and they are still using PostgreSQL.
They will be replaced with HDF5-based versions in future releases of the
OpenQuake Engine. For some calculator the HDF5-based implementation is
already available in the engine and can be accessed by using the ``--lite``
flag. For instance the classical hazard calculator is supported and can be
run with

``$ oq-engine --lite --run job.ini``

However the calculators accessible with the ``--lite`` flag should be
considered experimental, previews of things to come, they are still
subject to change.

3. OpenQuake 1.6 supports officially the format NRML 0.5 for the risk
models, which before was supported in a limited and experimental for
for vulnerability functions. Now all kind of risk models are supported:
vulnerability models, fragility risk models and consequence models.
Consequence models are brand new, introduced for the first
time in this release. The new format is simpler than before and more
convenient to use, since the OpenQuake platform offers a web tool to
prepare risk models in NRML 0.5. Beware that the web tool does not
support validation of the risk models yet.

4. The validation of the risk models in the engine has been
improved. In particular now an user confusing a fragility model with a
vulnerability model or a consequence model or any other combination
will get a clear error message. Moreover, each risk model has a
`lossCategory` attribute which must be set consistently with the name
of the key in the job.ini file (see the user manual for the details).

5. NRML 0.4 is still supported and works just fine, however it is deprecated
and a deprecation warning is printed every time you use a risk model in
the old format. To get rid of the warning you must upgrade the risk model
files to NRML 0.5. There is a command to do that recursively on a directory.
Just write

``$ oq-lite upgrade_nrml <some-directory>``

and all of your risk models will be upgraded. The original files will be
kept, but with a `.bak` extension appended on the right. Notice that due
to the validation discussed before, you will need to set the `lossCategory`
to the correct value. This is easy to do, since if you try to run a computation
you will get a clear error message telling which is the expected value for
the `lossCategory` for each risk model file.

6. OpenQuake 1.6 can use the consequence model files to compute consequence
ratios from a set of fragility models. This is a very important feature
which is documented in the [manual](http://www.globalquakemodel.org/openquake/support/documentation/engine/)

7. On the technological point of view, the OpenQuake project is even
more open than before. From this release we are using GitHub as our
official bug tracker, which makes it easier to follow the development
process (before the bug tracker was Launchpad, which is less popular
than GitHub and not integrated with the code base). Moreover from this
release our libraries (both oq-hazardlib and oq-risklib) are test by
using a public Continuous Integration system, Travis. Before our
builds were internal on Jenkins and visible only to our staff.
The engine is still built with Jenkins for various technical reasons.

8. Some work has been going on hazardlib, as usual, and you can
have a look at the [changelog](https://github.com/gem/oq-hazardlib/blob/engine-1.6/debian/changelog).


Support for different platforms
----------------------------------------------------

OpenQuake 1.5 supports Ubuntu from release 12.04 up to 15.10. 
We provide official packages for the long term releases 12.04 and 14.04.
Contrarily to our expectations, we were able to extend the support to
Ubuntu 12.04 by backporting the package `python-h5py` from Ubuntu 14.04.
So *Ubuntu 12.04 is still supported, even if it is deprecated*.

We have detailed instructions for installing the engine on CentOS 7
and Fedora and in general on [Red Hat Enterprise Linux clones]
(Installing-the-OpenQuake-Engine-from-source-code-on-Fedora-and-RHEL.md)

While the engine is not supported on Windows and Mac OS X, we are
happy to report that the underlying libraries and the
`oq-lite` command-line tool run just fine. We do not offer
any automatic tool to perform the installation, but there is
a [guide for Windows](Installing-OQ-Lite-on-Windows.md) and
a [guide for Mac OS X](Installing-OQ-Lite-on-MacOS.md) to help you
to install the necessary dependencies.

Bug fixes and changes with respect to OpenQuake 1.5
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
