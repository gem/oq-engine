Tips for running large risk calculations
========================================

Scenario calculations are usually not a performance problem, since
they involve a single rupture. The problem is with event based
calculations, where it is very much possible to have millions of
ruptures. This section deals with running large event based risk
calculations, especially ones with large logic trees, and explains
various techniques that can be used to reduce an impossible
calculation to a feasible one.


Understanding the hazard
------------------------------------------------

Usually event based calculations are dominated by the hazard component
(unless there are lots of assets aggregated on few hazard sites) and
therefore the first thing to do is to estimate the size of the hazard,
i.e. the number of GMFs that will produced. Since we are talking about
a large calculation, first of all we need reduce it so that it can
run. The simplest way to do that is to reduce the parameters affecting
the number of ruptures, i.e.

- investigation_time
- ses_per_logic_tree_path
- number_of_logic_tree_samples

For instance, if you have ``ses_per_logic_tree_path = 10,000`` reduce
it to 10, run the calculation and you will see in the log something
like this::

  [2018-12-16 09:09:57,689 #35263 INFO] Received
  {'gmfdata': '752.18 MB', 'hcurves': '224 B', 'indices': '29.42 MB'}

The amount of GMFs generated is 752.18 MB; since the calculation has
been reduced by a factor of 1000, the full computation will generate
around 750 GB of GMFs, which is a huge amount of data. Even if you
will not run out of disk space, most likely you will run out of
memory; even if you have enough memory to complete the hazard
parte of the calculation, most likely the risk part will fail: 750 GB
of GMFs are just too much for the current capabilities of the engine
(I am writing around the time of version 3.3). You will have to reduce
the calculation someway.

The most common techniques to reduce a risk calculation involves
splitting the exposure in carefully chosen regions, aggregating the
assets in such a way to reduce the number of hazard sites, and using
the right hazard model for the task at hand.

Collapsing of branches
----------------------

When one is not interested so much in the uncertainty around the loss
estimates, but more interested in the mean estimates, all of the
source model branches can be "collapsed" into one branch. Using the
collapsed source model should yield the same mean hazard or loss
estimates as using the full source model logic tree and then computing
the weighted mean of the individual branch results. For instance, for
many GEM calculations in the US, we're often only interested in the mean
Average Annual Loss estimates, or the mean Aggregate Loss Curve, so we
used the "collapsed" or "true-mean" source models that our hazard scientists
have produced for different source zones in the US.

Similarly, the GMPE logic tree for each TRT can also be "collapsed"
into a single branch. Using a single collapsed GMPE for each TRT
should also yield the same mean hazard estimates as using the full
GMPE logic tree and then computing the weighted mean of the individual
branch results. Usually we don't do this at GEM, but this can be
common in the proprietary vendor models. OpenSHA also has this option
for the GMPE logic tree for the Western US.


Calculation by region
---------------------

If one is interested in propagating the uncertainty in the source
models or ground motion models to the hazard or loss estimates,
collapsing the logic trees into a single branch to reduce
computational expense is not an option. But before going through the
effort of trimming the logic trees, there is an interim step that must
be explored, at least for large regions like entire Canada, entire
India, or the entire continental United States. This step is to
geographically divide the large region into logical smaller
subregions, such that the contribution to the hazard or losses in one
subregion from the other subregions is negligibly small or even
zero. For example, the continental US could be divided into seven
subregions, based on the seismic sources. The effective
realizations in each of the subregions will be much fewer than when
trying to cover the entire large region in a single
calculation. Eg. whereas the effective realizations for all of Canada
are around 13,122, for British Columbia they reduce to just 81.


Trimming of the logic-trees or sampling of the branches
-------------------------------------------------------

Trimming or sampling becomes necessary only if the following two
conditions hold:

1. You are interested in propagating the full uncertainty to the
   hazard and loss estimates; only the mean or quantile results are
   not sufficient for your analysis requirements, AND
2. The region of interest cannot be logically divided further as
   described above; the logic-tree for your chosen region of interest
   still leads to a large number of effective realizations. Eg. the
   logic-tree for the city of San Francisco still leads to 7,200
   effective realizations.

Sampling is the easier of the two options now. You only need to ensure
that you sample a sufficient number of branches to capture the
underlying distribution of the hazard or loss results you are
interested in. The drawback of random sampling is that you may still
need to sample hundreds of branches to capture well the underlying
distribution of the results.

Trimming can be much more efficient than sampling, because you pick a
few branches such that the distribution of the hazard or loss results
obtained from a full-enumeration of these branches is nearly the same
as the distribution of the hazard or loss results obtained from a
full-enumeration of the entire logic-tree.
