During the development of OpenQuake 1.5, a lot of effort went in checking
the correctness of the event based calculation and a lots of bugs were
fixed. As a consequence, *you cannot expect the numbers produced by
OpenQuake 1.5 to be the same as the numbers of OpenQuake 1.4 in all
situations*. Here we will document all the differencies and the reasons
for the differencies.

Also, it should be mentioned that *you cannot use the hazard calculated
with an OpenQuake 1.4 installation to run an event based risk
calculation with OpenQuake 1.5*. Generally speaking, this is never
possible, since we do not guarantee cross-version consistency.
In this case there is even a database schema change between
OpenQuake 1.4 and OpenQuake 1.5.

*If you install OpenQuake 1.5 your database will be updated in a
destructive way and you will not be able to go back to OpenQuake
1.4*. It will be impossible to run event based risk and scenario
risk calculation with OpenQuake 1.4 once you have upgraded your
database to OpenQuake 1.5.

If you want to compare the results of OpenQuake 1.4 and OpenQuake 1.5
use two different machines (they can be even virtual machines). If you
need to keep your old calculations make a backup of the database
before upgrading to OpenQuake 1.5. Usually one does not to keep old
calculations, but only the results: then exporting everything from
your old database, dropping it and starting from scratch with a new
database is a good migration strategy.

Cases in which you should expect different numbers
---------------------------------------------------

1. Longitude and latitude are now rounded to 5 digits after the
decimal point directly from Python; before the rounding happened
inside PostGIS in a hidden way. As a consequence, if the locations of
your assets have more than 5 digits, there are small differences in
the numbers produced by the engine, compared to previous versions.

This change has nothing to do with the event based calculator,
but it affects all calculators, so it is visible even there.
If the longitudes and latitudes of your sites have less than 6 digits,
this change will have no effect on your numbers.

3. We changed the source splitting procedure, which is now performed
in parallel and only for sources of high magnitude. This has an
effect on the event based hazard calculator. In order to guarantee
reproducibility of the calculation, we generate a random seed
for each sources, in a specific why. If the source splitting mechanism
changes and say there are more sources after splitting, we will then
generate more seeds. The ground motion fields at the end will be
slightly different. Of course in the limit of infinite stochastic
event sets there will be convergency, but in practice in real
calculations you must expect a minor seed dependency and some
small changes in your numbers. Since the hazard is different,
the risk is naturally also different.

4. A very subtle bug in the vulnerability functions was fixed, potentially
affecting calculations with nonzero coefficients of variation and
nonzero minIML; the numbers produced by the engine were incorrect;
see https://bugs.launchpad.net/oq-engine/+bug/1459926 for the details.

5. A bug in the epsilon sampling was found, so that in some situations
the same epsilons were used more than once. This potentially
affects calculations with nonzero coefficients of variation, with minor
changes in the numbers for the loss curves.

6. A bug in the ordering of the epsilons with respect to the ordering
of the ruptures was found. The problem was suble and not visibile in
all calculations, but only in cases when different SES Collections
read from the database where ordered incorrectly.  The effect was
still in calculations with nonzero coefficients of variation, with
very minor changes in the final numbers.

7. The algorithm to compute average losses and average insured losses
has been changed: it is now more robust since it does not rely on the
discretization of the loss curves, but directly on the underlying
losses. As a consequence the numbers for the average losses are
different than in previous versions of OpenQuake. This does not
affect the numbers for the loss curves, which however may be
affected by the bugs mentioned before.
