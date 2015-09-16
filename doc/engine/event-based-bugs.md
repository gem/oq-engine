During the development of OpenQuake 1.5, a lot of effort went in checking
the correctness of the event based calculation and a lots of bugs were
fixed. As a consequence, *you cannot expect the numbers produced by
OpenQuake 1.5 to be the same as the numbers of OpenQuake 1.4 in all
situations*. Here we will document all the differences and the reasons
for these differences.

Also, it should be mentioned that *you cannot use the hazard calculated
with an OpenQuake 1.4 installation to run an event based risk
calculation with OpenQuake 1.5*. Generally speaking, this is never
possible, since we do not guarantee cross-version consistency.
In this case, there is also a change in the database schema between
OpenQuake 1.4 and OpenQuake 1.5.

*If you install OpenQuake 1.5, your database will be updated in a
destructive way and you will not be able to revert back to OpenQuake
1.4*. In particular, it will not be possible to run event based risk 
and scenario risk calculations with OpenQuake 1.4 once you have 
upgraded your database to OpenQuake 1.5. Conversely, it won't be 
possible to use OpenQuake 1.5 with a database using the older schema 
of OpenQuake 1.4.

If you wish to compare the results from OpenQuake 1.4 and OpenQuake 1.5, 
we suggest using two different machines (they can be virtual machines). 
If you need to keep your old calculations, please make a backup of the 
database before upgrading to OpenQuake 1.5. Usually one does not to keep old
calculations, but only the results: then exporting everything from
your old database, dropping it and starting from scratch with a new
database is a good migration strategy.

Cases where you should expect different numbers
-----------------------------------------------

1. Longitude and latitude coordinates are now rounded directly in Python to a 
precision of 5 digits after the decimal point; in earlier versions, this 
rounding was done inside PostGIS in an inaccessible manner. As a consequence, 
if the locations of your assets have more than 5 digits, you might notice 
minor differences in the numbers produced by the engine compared to previous 
versions. This change has nothing to do with the event based calculator 
specifically, but as it affects all calculators, its effects are visible in 
the event based calculator too. If the longitudes and latitudes of your sites 
have less than 6 digits after the decimal points, this change will have no 
effect on your numbers.

2. The source splitting procedure is now performed in parallel and only for 
sources with high magnitudes. This change affects the event based hazard 
calculator. In order to guarantee reproducibility of the calculations, we 
generate a random seed for each source, in a specific way. If the source 
splitting mechanism changes and there are more sources after splitting, 
more seeds are generated. The computed ground motion fields will be slightly 
different. Of course in the limit of infinite stochastic event sets there 
will be convergence, but in practice for real calculations you should 
expect a minor seed dependency and some small changes in your numbers. Since 
the hazard is different, the risk numbers will also be slightly different.

3. A very subtle bug in the vulnerability functions was fixed, potentially
affecting calculations using vulnerability functions with nonzero 
coefficients of variation and nonzero minIML; the numbers produced by 
previous versions of the engine were incorrect. See 
https://bugs.launchpad.net/oq-engine/+bug/1459926 for the details.

4. A bug in the epsilon sampling was found, so that in some situations
the same epsilons were used more than once. This potentially
affects calculations with nonzero coefficients of variation, with minor
changes in the numbers for the loss curves.

5. A bug in the ordering of the epsilons with respect to the ordering
of the ruptures was found. The problem was subtle and not visible in
all calculations, but only in cases when the different SES Collections
read from the database were ordered incorrectly. The effect was again only 
on calculations with nonzero coefficients of variation in the vulnerability 
functions, with very minor changes in the final numbers.

6. The algorithm to compute average losses and average insured losses
has been changed: it is now more robust since it does not rely on the
discretization of the loss curves, but directly on the underlying
loss tables. As a consequence the numbers for the average losses are
different than in previous versions of OpenQuake. This does not
affect the numbers for the loss curves, which, however, may be
affected by the bugs mentioned before.
