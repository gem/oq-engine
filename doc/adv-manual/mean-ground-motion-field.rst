The concept of "mean" ground motion field
============================================

The engine has at least three different kinds of *mean ground motion
field*, computed differently and used in different situations:

1. *Mean ground motion field by GMPE*, used to reduce disk space and
   make risk calculations faster.

2. *Mean ground motion field by event*, used for debugging/plotting
   purposes.

3. *Single-rupture hazardlib mean ground motion field*,
   used for analysis/plotting purposes.

Mean ground motion field by GMPE
--------------------------------

This is the most useful concept for people doing risk calculations.
To be concrete, suppose you are running a `scenario_risk` calculation
on a region where you have a very fine site model (say at 1 km
resolution) and a sophisticated hazard model (say with 16 different
GMPEs): then you can easily end up with a pretty large calculation.
For instance one of our users was doing such a calculation with an
exposure of 1.2 million assets, 50,000+ hazard sites, 5 intensity
measure levels and 1000 simulations, corresponding to 16,000 events
given that there are 16 GMPEs.  Given that each ground motion value
needs 4 bytes to be stored as a 32 bit float, the math tells us that
such calculation will generate 50000 x 16000 x 5 x 4 ~ 15 GB of data
(it could be a but less by using the ``minimum_intensity`` feature,
but you get the order of magnitude). This is very little for the
engine that can store such an amount of data in less than 1 minute,
but it is a huge amount of data for a database.  If you a
(re)insurance company and your workflow requires ingesting the GMFs in
a database to compute the financial losses, that's a big issue.  The
engine could compute the hazard in just an hour, but the risk part
could easily take 8 days. This is a no-go for most companies. They
have deadlines and cannot way 8 days to perform a single analysis. At
the end they are interested only in the mean losses, so they would
like to have a single effective mean field producing something close
to the mean losses that more correctly would be obtained by
considering all 16 realizations. With a single effective realization
the data storage would drop under 1 GB and more significantly the
financial model software would complete the calculation in 12 hours
instead of 8 days, something a lot more reasonable.

For this kind of situations hazardlib provides an ``AvgGMPE`` class,
that allows to replace a set of GMPEs with a single effective GMPE.
More specifically, the method ``AvgGMPE.get_means_and_stddevs``
calls the methods ``.get_means_and_stddevs`` on the underlying GMPEs
and performs a weighted average of the means and a weighted average
of the variances using the usual formulas:

.. math::

   μ &= ∑_i w_i μ_i \\
   σ^2 &= ∑_i w_i (σ_i)^2

where the weights sum up to 1. It is up to the user to check how big
is the difference in the risk between the complete calculation and
the mean field calculation. A factor of 2 discrepancies would not be
surprising, but we have also seen situations where there is no difference
withing the uncertainty due to the random seed choice.


Mean ground motion field by event
---------------------------------

Using the `AvgGMPE` trick does not solve the issue of visualizing the
ground motion fields, since for each site there are still 1000 events.
A plotting tool has still to download 1 GB of data and then one has
to decide which event to plot. The situation is the same if you are
doing a sensitivity analysis, i.e. you are changing some parameter
(it could be a parameter of the underlying rupture, or even the random
seed) and you are studying how the ground motion fields change. It is
hard to compare two sets of data of 1 GB each. Instead, it is a lot
easier to define a "mean" ground motion field obtained by averaging
on the events and then compare the mean fields of the two calculations:
if they are very different, it is clear that the calculation is very
sensitive to the parameter being studied. Still, the tool performing the
comparison will need to consider 1000 times less data and will be
1000 times faster, also downloding 1000 times less data from the remote
server where the calculation has been performed.

For this kind of analysis the engine provides an internal output ``avg_gmf``
that can be plotted with the command ``oq plot avg_gmf <calc_id>``. It is
also possible to compare two calculations with the command

``$ oq compare avg_gmf imt <calc1> <calc2>``

Since ``avg_gmf`` is meant for internal usage and for debugging it is
not exported by default and it is not visible in the WebUI. It is also
not guaranteed to stay the same across engine versions. It is
available starting from version 3.11. It should be noted that,
consistently with how the ``AvgGMPE`` works, the ``avg_gmf`` output
*is computed in log space*, i.e. it is geometric mean, not the usual
mean. If the distribution was exactly lognormal that would also coincide
with the median field.

However, you should remember that in order to reduce
the data transfer and to save disk space the engine discards ground
motion values below a certain minimum intensity, determined explicitly
by the user or inferred from the vulnerability functions when
performing a risk calculation: there is no point in considering ground
motion values below the minimum in the vulnerability functions, since
they would generate zero losses. Discarding the values below the threshould
breaks the log normal distribution.

To be concrete, consider a case with a single site, and single intensity measure
type (PGA) and a ``minimum_intensity`` of 0.05g. Suppose there are 1000
simulations and that you have a normal distribution of the logaritms
with μ=-2 and σ=.5; then the ground motion values that you could obtain
would be as follows:

>>> import numpy
>>> numpy.random.seed(42) # fix the seed
>>> gmvs = numpy.random.lognormal(mean=-2.0, sigma=.5, size=1000)

As expected, the variability of the values is rather large, spanning
more than one order of magnitude:

>>> gmvs.min(), numpy.median(gmvs), gmvs.max()
(0.026765710489091852, 0.1370582013790309, 0.9290114132955762)

Also mean and standard deviation of the logarithms are very close to
the expected values μ=-2 and σ=.5:

>>> numpy.log(gmvs).mean()
-1.9903339720888376
>>> numpy.log(gmvs).std()
0.4893631038736771

The geometric mean of the values (i.e. the exponential of the mean
of the logarithms) is very close to the median, as expected for a lognormal
distribution:

>>> numpy.exp(numpy.log(gmvs).mean())
0.13664978061122787

All these properties are broken when the ground motion values
are truncated below the ``minimum_intensity``:

>>> gmvs[gmvs < .05] = .05
>>> numpy.log(gmvs).mean()
-1.9876078473466177
>>> numpy.log(gmvs).std()
0.48280630467779523
>>> numpy.exp(numpy.log(gmvs).mean())
0.13702281319482504

In this case the difference is minor, but if the number of simulations is
small and/or the σ is large the mean and standard deviation obtained
from the logarithms of the ground motion fields could be quite different
from the expected ones.

Finally, it should be noticed that the geometric mean can be orders of
magnitude different from the usual mean and it is purely a coincidence
that in this case they are close (~0.137 vs ~0.155).


Single-rupture estimated median ground motion field
---------------------------------------------------

The mean ground motion field by event discussed above is an *a posteriori*
output: *after* performing the calculation, some statistics are performed
on the stored ground motion fields. However, in the case of a single
rupture it is possible to estimate the geometric mean and the geometric
standard deviation  *a priori*, using hazardlib and without performing
a full calculation. It is enough to instantiate the rupture, the site
collection and the GMPE (that can be an ``AvgGMPE`` in the case of
multiple GMPEs`) and to call directly the method ``.get_mean_and_stddevs``.
That is easy and nice but it should be noticed that it comes with some
limitation:

1. it only works when there is a single rupture
2. you have to manage the ``minimum_intensity`` manually if you want to compare
   with a concrete engine output
3. it is good for estimates, it gives you the theoretical ground
   ground motion field but not the ones concretely generated by the
   engine fixed a specific seed

It should also be noticed that there is a shortcut to compute the
single-rupture hazardlib "mean" ground motion field without writing
any code; just set in your ``job.ini`` the following values::

  truncation_level = 0
  ground_motion_fields = 1

Setting ``truncation_level = 0`` effectively replaces the lognormal
distribution with a delta function, so the generated ground motion fields
will be all equal, with the same value for all events: this is why you
can set ``ground_motion_fields = 1``, since you would just waste time and space
by generating multiple copies.

Finally let's warn again on the term hazardlib "mean" ground motion
field: in log space it is truly a mean, but in terms of the original
GMFs it is a geometric mean - which is the same as the median since the
distribution is lognormal - so you can also call this the hazardlib
*median* ground motion field.
