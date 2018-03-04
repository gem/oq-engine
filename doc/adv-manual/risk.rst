Tips for running large risk calculations
========================================

Running large risk calculations, especially ones with large logic
trees, is an art, and there are various techniques that can be used to
reduce an impossible calculation to a feasible one.

Split the calculation in hazard part + risk part
------------------------------------------------

The first thing to do when you have a large calculation is to reduce it
so that it can run. The simplest way to do that is to reduce the exposure,
for instance by considering a small geographics portion of it, of by
sampling the assets. Once the calculation has been reduced, you can run
it and determine if is dominated by the hazard or by the risk part.

Most of the times, the calculation will be dominated by the hazard part.
If that is the case, your best option is to split your `job.ini` configuration
file into a `job_hazard.ini` and a `job_risk.ini` file. Once you have
computed the hazard with

``$ oq engine --run job_hazard.ini``

and got a calculation ID you can then run the risk with

``$ oq engine --run job_risk.ini --hc <calc_id>``

This approach is convenient because you can run the heaviest
calculation only once and then run different risk calculations, tuning
the risk parameters, all starting from the same hazard. This is akin
to caching the heavy part of the calculation.

In some cases (for instance if there are millions assets aggregated on
few hazard sites) the risk part can dominate over the hazard part. In
`scenario_risk` or `scenario_damage` calculations the risk part
normally dominates the hazard part, unless you have a lot of hazard
sites and correlation of ground motion fields. In such situations
there is no much point in splitting the `job.ini` file.

Having ran the reduced calculation, once can estimate how long the full
calculation will take. If the estimate gives you an impossibly large number
(for instance if you discover thatf it takes 1 day to run 1/100th of the
calculation) then you must use some optimization techniques.

The most common techniques involves splitting the exposure in
carefully chosen regions, aggregating the assets in such a way to
reduce the number of hazard sites, and using the right hazard model
for the task at hand.

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
