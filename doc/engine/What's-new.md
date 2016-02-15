OpenQuake 1.8 is a major release and a big improvement with respect
to OpenQuake 1.7. Everybody is invited to upgrade,
by following the [usual procedure](Installing-the-OpenQuake-Engine.md).

New features of the OpenQuake Engine, version 1.8
---------------------------------------------------

1. The most important new feature of the engine is that the
celery/rabbitmq combo is now optional. That means that the engine
works even without celery/rabbitmq; actually, this is the recommended way to run
the engine on a single machine.  If you are using a cluster, you must
still use celery/rabbitmq. But the big majority of the users, including
everybody using the official virtual machines will have a much simpler
experience. The most common error for newbies was to forget starting
celery or running it from the wrong directory. Now this barrier is
gone. Also, the engine is more efficient without celery/rabbitmq,
especially for calculations with a large data transfer.

2. The other big change is that now all the old calculators based on
PostgreSQL are gone. There is no distinction between the oq-lite
calculators and the engine calculators: they are all the same.
All the calculators use an HDF5 file (the datastore) as data
storage. This has a large performance impact on calculations heavy
on data storage.

3. The classical hazard calculator has been completely rewritten. Now
it automatically splits the site collection in tiles of size
`sites_per_tiles` (the default is 1,000 sites per tile). This has an
huge performance benefit, especially for continental scale calculation
with tens or hundreds of thousand of sites.

4. The logic for splitting the sources has changed: now only the so-called
*heavy* sources are split, thus reducing a lot the split time and the
data transfer.

5. The algorithm to read the source model has been changed and it is now
faster, since it does not require anymore to parse the same file more
than once, which was the case for nontrivial logic trees.

6. The algorithm to generate seeds for the event based calculator has
changed to ensure that the results are not affected by the splitting
procedure. Because of the change in the algorithm, the ruptures
produced by the event based calculator are slightly different than
before, and all the dependent quantites are different as well.
The difference however is stochastically insignificant, akin to
a change of seeds and in the limit of a large number of Stochastic
Event Sets the results are equivalent.

7. The storage of the results in the datastore has been significantly
improved. In particular a lots of outputs that previosly were stored
as pickled Python objects are now being stored as proper HDF5 arrays.
Specifically, the datastore contains the following new arrays,
previously only pickled:

   sitecol: contains the hazard sites and their parameters
   assetcol: contains the exposure
   riskmodel: contains the vulnerability/fragility functions

However the HDF5 format is still NOT stable and actually is guaranteed
to change in the next version. For instance, if you want to write
your our routines your our routines to extract/plot the hazard curves
or the loss curves from the datastore, you can, but you should be
aware that you will have to change your code with the next release
of the engine.

8. 

7. 

4. The validation of the risk models in the engine has been
improved.

6. Some work has been going on hazardlib, as usual, and you can have a
look at the [changelog]
(https://github.com/gem/oq-hazardlib/blob/engine-1.8/debian/changelog).

7. The following new GMPEs have been added:


10.

13. The .rst report of a calculation has been improved and more information is
  displayed. Moreover, you can also run
  ```bash
  $ oq-lite show fullreport <calc-id>
  ```
  to get information about a calculation which has already run.


19. Countless small improvements and additional validations have been
added. This release has seen more than 200 pull
requests reviewed and merged.

Bug fixes and changes with respect to OpenQuake 1.7
----------------------------------------------------

1. We removed several switches from the `oq-engine` command:
all the commands that have been deprecated for over two years, all
the commands that have become obsolete (i.e. the one specific
to PostgreSQL), and all the commands that never worked properly.

2. We temporarily removed the ability to compute insured loss curves from
the classical risk calculator. The reason is that doubts were
raised about the algorithm used. The plan is to restore such functionality
in the next version of the engine with a better and more tested algorithm.

3. The parameter `asset_hazard_distance` was not honored for the
calculators `classical_risk` and `classical_bcr`: this has been
fixed now.

18. We fixed a few export bugs. Now the XML exporter for mean and
quantile loss curves and maps work properly in all situations/

6. We are not storing anymore the epsilon matrix in event based and
scenario risk calculations. There was no strong reason to persist it,
and since it can be rather large, it was artificially making the
datastore larger than needed.

8. Some unused and undocumented configuration parameters like `statistics`
have been removed.

9. The demos have been revisited and updated.

11. We fixed a subtle bug that made it impossible to make a deepcopy
of source objects.

12. Since all the classical calculators use the datastore, the
export has changed slightly with respect to the past. Everything
is now more consistent.


Support for different platforms
----------------------------------------------------

OpenQuake 1.8 supports Ubuntu from release 12.04 up to 15.10.  We
provide official packages for the long term releases 12.04 and 14.04.
*Ubuntu 12.04 has been deprecated for a long time and this is the last
release to support it*.

We have official packages also for CentOS 7
and in general for [Red Hat Enterprise Linux clones]
(Installing-the-OpenQuake-Engine-from-source-code-on-Fedora-and-RHEL.md).

While the engine is not supported on Windows and Mac OS X, we are
happy to report that the underlying libraries and the
`oq-lite` command-line tool run just fine. We do not offer
any automatic tool to perform the installation, but there is
a [guide for Windows](Installing-OQ-Lite-on-Windows.md) and
a [guide for Mac OS X](Installing-OQ-Lite-on-MacOS.md) to help you
to install the necessary dependencies.

Other
------

Depending on the version of the HDF5 libraries you are using,
you may get a warning like the following:

```
HDF5: infinite loop closing library
      D,G,A,S,T,F,D,A,S,T,F,FD,P,FD,P,FD,P,E,E,SL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL,FL
```

Please ignore it, it is a quirk on the underlying library. The engine
is working correctly.
