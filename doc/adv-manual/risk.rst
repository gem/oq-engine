Tips for running large risk calculations
========================================

Scenario risk calculations are usually not a performance problem,
since they involve a single rupture. The problem are event based risk
calculations, where they may have millions of ruptures. This section
deals with running large event based risk calculations, especially
ones with large logic trees, and explains various techniques that can
be used to reduce an impossible calculation to a feasible one.

Understanding the hazard
------------------------------------------------

Usually event based calculations are dominated by the hazard component
(unless there are lots of assets aggregated on few hazard sites) and
therefore the first thing to do is to estimate the size of the hazard,
i.e. the number of GMFs that will be produced. Since we are talking about
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
around 750 GB of GMFs, which is a huge amount. Even if you
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

The ebrisk calculator
---------------------------------------

Even with all the tricks in the book, some problems cannot be solved
with the traditional ``event_based_risk`` calculator, in particular
when there are too many sites. Suppose for instance (this is a real
life example) that you have a very detailed exposure for Canada,
with 462,000 hazard sites, and also a very detailed site model capable
of covering all the sites. It would be a pity to lose such detailed
information by aggregating the assets on a larger grid, but this is
only viable option for the ``event_based_risk`` calculator.

The issue is that the ``event_based_risk`` cannot work well with
so many sites, unless you reduce your investigation time to something
which is not significative. If the  investigation time is long enough,
you will have issues like

1. running out of memory when computing the GMFs
2. running out of disk space when saving the GMFs
3. running out of memory when reading the GMFs
4. having an impossibly slow risk calculation

The solution - in theory - would be to split Canada in regions, but it
is even worse because

1. one has to compute the ruptures on all Canada in a single run, to
   make sure that the seeds are consistent for all regions
2. then one has to run several calculation starting from the pregenerated
   ruptures, one per each subregion
3. finally one had to aggregate the results from the different
   calculations

Such steps are annoying, time consuming and very much error prone.

In order to solve such issues a new calculation ``ebrisk`` has been
introduced in engine 3.4. For small calculations the ``ebrisk`` calculator
will not be much better than the ``event_based_risk`` calculator, but
the larger your calculation is, the better it will work, and in situations
like the Canada example here it can be orders of
magnitude more efficient, both in speed an memory occupation.
There are two reasons why the ``ebrisk`` calculator is so efficient:

1. it ignores the coefficient of variations in the vulnerability functions
2. it computes the GMFs in memory instead of reading them for the datastore

Let me explain better the first point. Suppose there are 10 assets of the same
taxonomy on a given hazard site and suppose that the vulnerability function
for that taxonomy has coefficients of variations are all zeros. Then the
risk for all those assets will be exactly the same: still, the
``event_based_risk`` will perform 10 times more calculations than needed
and will keep in memory 10 times more data than needed.
The ``ebrisk`` instead does not make that error. On the other hand, if
the coefficients of variations are nonzero, the ``ebrisk`` calculator
will give the wrong answer while the ``even_based_risk`` will give the right
one.

However, you should bear in mind that risk calculations are affected
by so many uncertainties that asset correlation is the least of your
worries, especially for global scale calculations: ignoring the
coefficients of variations is a good enough strategy. Probably the
answer you will get will be significative and certainly better than no
answer at all, given than considering the coefficients will likely
cause an out of memory error.

Now, let's discuss the second point. The ``event_based_risk`` calculator
works by storing the GMFs in the hazard phase of the calculation and
by reading them in the risk phase. This approach has his advantages:

1. if the GMFs calculation is expensive, it is good to avoid repeating
   it when you change a risk parameter without changing the hazard parameters
2. it is convenient to have the GMFs saved somewhere to debug issues
   with the calculation
3. except for huge calculations, writing and reading the GMFs is fast,
   since they stored in a very optimized HDF5 format
   
On the other hand, there are other things to consider for the
specific case of global risk calculations:

1. computing the GMFs is not expensive, because in global risk calculations
   we never consider GMF-correlation, that would be computationally prohibitive
2. global risk calculations are huge, and typically are dominated by the
   reading time of the GMFs, which happens concurrently
3. saving disk space matters, running the entire world would generate
   tens of terabytes of GMFs that we cannot store.

So, in practice, in very large calculations the strategy of computing the
GMFs on-the-fly wins over over the strategy of saving them and this is
why the ``ebrisk`` calculator exists.

Differences with the event_based_risk calculator
------------------------------------------------

The ``event_based_risk`` calculator parallelizes by hazard sites: it splits
the exposure in spatial blocks and then each task reads the GMFs for each site
in the block it gets.

The ``ebrisk`` calculator instead parallelizes by ruptures: it splits
the ruptures in blocks and then each task generates the corresponding GMFs
on the fly.

Since the amount of data in ruptures form is typically two orders of
magnitude smaller than the amount of data in GMFs, and since the GMF-generation
is fast, the ``ebrisk`` calculator is able to beat the ``event_based_risk``
calculator.

Moreover, since each task in the the ``ebrisk`` calculator gets the entire
exposure, it is able to aggregate the losses without problems, while the
``event_based_risk`` calculator cannot do that: event if each task has access to
all events, it only receives a subset of the exposure, so it cannot aggregate
on the assets. The ``event_based_risk`` can produce the loss curves for the
assets on a given site, but not the aggregate loss curves on a region, because
the algorithm used to compute them is not extensive::

  loss_curves([site1]) + loss_curves([site2]) != loss_curves([site1, site2])

On the other hand the ``ebrisk`` calculator has no problem with aggregated
loss curves, so you *must* use it if you are interested in such outputs.
Aggregated losses instead are computed simply by summing values, the algorithm
is linear and you can compute them both with the ``event_based_risk``
calculator and the ``ebrisk`` calculator.

In order to compute aggregate loss curves with the ``ebrisk`` you must
set the ``aggregate_by`` parameter in the ``job.ini``. If you do not
set it, you will still able to compute the total aggregate loss curve
(and aggregate asset losses) which could be computed with the old
calculator ``event_based_risk`` too. The interesting bit is when you
want to compute aggregate loss curves by region. In order to do so
your exposure must contain some tag specifying the region to which
each asset belongs. We have an example for Nepal in our event based risk demo.
The exposure there contains various tags and in particular a geographic
tag called NAME1 with values "Mid-Western", "Far-Western", "West", "East",
"Central", and the ``job_eb.ini`` file defines

``aggregate_by = NAME_1``

When running the calculation you will see something like this::

   Calculation 23060 finished correctly in 11 seconds
     id | name
    182 | Aggregate Asset Losses
    186 | Aggregate Event Losses
    180 | Aggregate Loss Curves
    181 | Aggregate Loss Curves Statistics
    183 | Average Asset Losses
    188 | Earthquake Ruptures
    184 | Full Report
    185 | Input Files
    187 | Realizations
    189 | Seismic Source Groups

Exporting the *Aggregate Loss Curves Statistics* output will give
you the mean and quantile loss curves in a format like the following one:

 .. code-block:: csv

    annual_frequency_of_exceedence,return_period,loss_type,loss_value,loss_ratio
    5.00000E-01,2,nonstructural,0.00000E+00,0.00000E+00
    5.00000E-01,2,structural,0.00000E+00,0.00000E+00
    2.00000E-01,5,nonstructural,0.00000E+00,0.00000E+00
    2.00000E-01,5,structural,0.00000E+00,0.00000E+00
    1.00000E-01,10,nonstructural,0.00000E+00,0.00000E+00
    1.00000E-01,10,structural,0.00000E+00,0.00000E+00
    5.00000E-02,20,nonstructural,0.00000E+00,0.00000E+00
    5.00000E-02,20,structural,0.00000E+00,0.00000E+00
    2.00000E-02,50,nonstructural,0.00000E+00,0.00000E+00
    2.00000E-02,50,structural,0.00000E+00,0.00000E+00
    1.00000E-02,100,nonstructural,0.00000E+00,0.00000E+00
    1.00000E-02,100,structural,0.00000E+00,0.00000E+00
    5.00000E-03,200,nonstructural,1.35279E+05,1.26664E-06
    5.00000E-03,200,structural,2.36901E+05,9.02027E-03
    2.00000E-03,500,nonstructural,1.74918E+06,1.63779E-05
    2.00000E-03,500,structural,2.99670E+06,1.14103E-01
    1.00000E-03,1000,nonstructural,6.92401E+06,6.48308E-05
    1.00000E-03,1000,structural,1.15148E+07,4.38439E-01
