Tips for running large risk calculations
========================================

Scenario risk calculations usually do not pose a performance problem,
since they involve a single rupture and a limited geography for analysis. 
Some event-based risk calculations, however, may involve millions of ruptures
and exposures spanning entire countries or even larger regions. This section
offers some practical tips for running large event based risk calculations, 
especially ones involving large logic trees, and proposes techniques that might
be used to make an intractable calculation tractable.

Understanding the hazard
------------------------

Event-based calculations are typically dominated by the hazard component
(unless there are lots of assets aggregated on few hazard sites) and
therefore the first thing to do is to estimate the size of the hazard,
i.e. the number of GMFs that will be produced. Since we are talking about
a large calculation, first of all we need reduce it to a size that is 
guaranteed to run quickly. The simplest way to do that is to reduce the 
parameters directly affecting the number of ruptures generated, i.e.

- investigation_time
- ses_per_logic_tree_path
- number_of_logic_tree_samples

For instance, if you have ``ses_per_logic_tree_path = 10,000`` reduce
it to 10, run the calculation and you will see in the log something
like this::

  [2018-12-16 09:09:57,689 #35263 INFO] Received
  {'gmfdata': '752.18 MB', 'hcurves': '224 B', 'indices': '29.42 MB'}

The amount of GMFs generated for the reduced calculation is 752.18 MB; 
and since the calculation has been reduced by a factor of 1,000, 
the full computation is likely to generate around 750 GB of GMFs. 
Even if you have sufficient disk space to store this large quantity of GMFs, 
most likely you will run out of memory. Even if the hazard part of the 
calculation manages to run to completion, the risk part of the calculation
is very likely to fail — managing 750 GB of GMFs is beyond the current 
capabilities of the engine. Thus, you will have to find ways to reduce the
size of the computation. 

A good start would be to carefully set the parameters 
``minimum_magnitude`` and ``minimum_intensity``:

- ``minimum_magnitude`` is a scalar or a dictionary keyed by tectonic region;
  the engine will discard ruptures with magnitudes below the given threshoulds
- ``minimum_intensity`` is a scalar or a dictionary keyed by the intensity
  measure type; the engine will discard GMFs below the given intensity threshoulds

Choosing reasonable cutoff thresholds with these parameters can significantly
reduce the size of your computation when there are a large number of 
small magnitude ruptures or low intensity GMFs being generated, which may have
a negligible impact on the damage or losses, and thus could be safely discarded.


Collapsing of branches
----------------------

When one is not interested so much in the uncertainty around the loss
estimates, but more interested simply in the mean estimates, all of the
source model branches can be "collapsed" into one branch. Using the
collapsed source model should yield the same mean hazard or loss
estimates as using the full source model logic tree and then computing
the weighted mean of the individual branch results.

Similarly, the GMPE logic tree for each tectonic region can also be "collapsed"
into a single branch. Using a single collapsed GMPE for each TRT
should also yield the same mean hazard estimates as using the full
GMPE logic tree and then computing the weighted mean of the individual
branch results. This has become possible through the introduction of 
`AvgGMPE feature <https://github.com/gem/oq-engine/blob/engine-3.9/openquake/qa_tests_data/classical/case_19/gmpe_logic_tree.xml#L26-L40>`_ in version 3.9.


Splitting the calculation into subregions
-----------------------------------------

If one is interested in propagating the full uncertainty in the source
models or ground motion models to the hazard or loss estimates,
collapsing the logic trees into a single branch to reduce
computational expense is not an option. But before going through the
effort of trimming the logic trees, there is an interim step that must
be explored, at least for large regions like the entire continental United States.
This step is to geographically divide the large region into logical smaller
subregions, such that the contribution to the hazard or losses in one
subregion from the other subregions is negligibly small or even zero. 
The effective realizations in each of the subregions will then be much 
fewer than when trying to cover the entire large region in a single
calculation.


Trimming of the logic-trees or sampling of the branches
-------------------------------------------------------

Trimming or sampling may be necessary if the following two
conditions hold:

1. You are interested in propagating the full uncertainty to the
   hazard and loss estimates; only the mean or quantile results are
   not sufficient for your analysis requirements, AND
2. The region of interest cannot be logically divided further as
   described above; the logic-tree for your chosen region of interest
   still leads to a very large number of effective realizations.

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

Disabling the propagation of vulnerability uncertainty to losses
----------------------------------------------------------------

The vulnerability functions using continuous distributions
(such as the lognormal distribution or beta distribution) to 
characterize the uncertainty in the loss ratio conditional on the
shaking intensity level, specify the mean loss ratios and the corresponding
coefficients of variation for a set of intensity levels.
They are used to build the so called epsilon matrix within the engine,
which is how loss ratios are sampled from the distribution for each asset.

There is clearly a performance penalty associated with the propagation
of uncertainty in the vulnerability to losses. The epsilon matrix has 
to be computed and stored, and then the worker processes have to read it, 
which involves large quantities of data transfer and memory usage.

Setting

``ignore_covs = true``

in your `job.ini` file will result in the engine using just the mean loss
ratio conditioned on the shaking intensity and ignoring the uncertainty.
This tradeoff of not propagating the vulnerabilty uncertainty to the loss
estimates can lead to a significant boost in performance and tractability.


The ebrisk calculator
---------------------

Even with all the tricks in the book, some problems cannot be solved
with the traditional ``event_based_risk`` calculator, in particular
when there are too many hazard sites. Suppose for instance that you
have a very detailed exposure for Canada with 462,000 hazard sites,
and a corresponding site model covering all of the sites. 
It would be a pity to lose such detailed information by aggregating 
the assets onto a coarser grid, but this may be the only viable option 
for the traditional ``event_based_risk`` calculator.

The issue is that the ``event_based_risk`` cannot work well with
so many sites, unless you reduce your investigation_time considerably. 
If the investigation_time is long enough for a reasonable computation,
you will most likely run into issues such as:

1. running out of memory when computing the GMFs
2. running out of disk space when saving the GMFs
3. running out of memory when reading the GMFs
4. having an impossibly slow risk calculation

The solution - in theory - would be to split Canada in regions, but this comes
with its own problems. For instance,

1. one has to compute the ruptures for all Canada in a single run, to
   make sure that the random seeds are consistent for all regions
2. then one has to run several calculations starting from the
   ruptures, one per sub-region
3. finally one has to carefully aggregate the results from the different
   calculations

Such steps are tedious, time consuming and very much error prone.

In order to solve such issues a new calculator, tentatively called ``ebrisk``,
has been introduced in engine 3.4. For small calculations the ``ebrisk`` calculator
will not be much better than the ``event_based_risk`` calculator, but
the larger your calculation is, the better it will work, and in situations
like the Canada example here it can be orders of
magnitude more efficient, both in speed and memory consumption.
The reason why the ``ebrisk`` calculator is so efficient is that
it computes the GMFs in memory instead of reading them from the datastore.

The older ``event_based_risk`` calculator
works by storing the GMFs in the hazard phase of the calculation and
by reading them in the risk phase. For small to medium sized risk
calculations, this approach has the following advantages:

1. if the GMFs calculation is expensive, it is good to avoid repeating
   it when you change a risk parameter without changing the hazard parameters
2. it is convenient to have the GMFs saved on disk to debug issues
   with the calculation
3. except for huge calculations, writing and reading the GMFs is fast,
   since they stored in a very optimized HDF5 format
   
On the other hand, there are other considerations for large national or 
continental risk calculations:

1. these larger risk calculations are typically dominated by the
   reading time of the GMFs, which happens concurrently
2. saving disk space matters, as such large calculations can generate
   hundreds of gigabytes or even terabytes of GMFs that cannot be stored
   conveniently

So, in practice, in very large calculations the strategy of computing the
GMFs on-the-fly wins over over the strategy of saving them to disk and this is
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

Moreover, since each task in the ``ebrisk`` calculator gets sent the entire
exposure, it is able to aggregate the losses without problems, while the
``event_based_risk`` calculator cannot do that — even if each task has access to
all events, it only receives a subset of the exposure, so it cannot aggregate
on the assets. 

The ``event_based_risk`` can produce the loss curves for the individual
assets in the exposure, but it cannot compute aggregate loss curves (say for
all assets of a particular occupancy class or for administrative divisions), 
because loss curves are not additive::

  loss_curve([asset1]) + loss_curve([asset2]) != loss_curve([asset1, asset2])

On the other hand the ``ebrisk`` calculator has no problem with aggregated
loss curves, so you *must* use it if you are interested in such outputs.

Aggregation of average annual losses, instead, is computed simply by 
summing the component values. This algorithm is linear and both the 
``event_based_risk`` calculator and the ``ebrisk`` calculator are capable of
this aggregation.

In order to compute aggregate loss curves with the ``ebrisk`` you must
set the ``aggregate_by`` parameter in the ``job.ini`` to one or more tags
over which you wish to perform the aggregation. Your exposure must contain 
the specified tags with values for each asset. 
We have an example for Nepal in our event based risk demo.
The exposure for this demo contains various tags and in particular a geographic
tag called NAME1 with values "Mid-Western", "Far-Western", "West", "East",
"Central", and the ``job_eb.ini`` file defines

``aggregate_by = NAME_1``

When running the calculation you will see something like this::

   Calculation 1 finished correctly in 17 seconds
  id | name
   9 | Aggregate Event Losses
   1 | Aggregate Loss Curves
   2 | Aggregate Loss Curves Statistics
   3 | Aggregate Losses
   4 | Aggregate Losses Statistics
   5 | Average Asset Losses Statistics
  11 | Earthquake Ruptures
   6 | Events
   7 | Full Report
   8 | Input Files
  10 | Realizations
  12 | Total Loss Curves
  13 | Total Loss Curves Statistics
  14 | Total Losses
  15 | Total Losses Statistics

Exporting the *Aggregate Loss Curves Statistics* output will give
you the mean and quantile loss curves in a format like the following one::

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
    
If you do not set the ``aggregate_by`` parameter for an ``ebrisk`` calculation, 
you will still able to compute the total loss curve 
(for the entire portfolio of assets), and the total average losses.


The asset loss table
---------------------

When performing an event based risk (or ebrisk) calculation the engine
keeps in memory a table with the losses for each asset and each event,
for each loss type. It is impossible to fully store such table,
because it is extremely large; for instance, for 1 million assets, 1
million events, 2 loss types and 4 bytes per loss ~8 TB of disk space
would be required. It is true that many events will produce zero losses
because of the `maximum_distance` and `minimum_intensity` parameters,
but still the asset loss table is prohibitively large and for many years
could not be stored. In engine 3.8 we made a breakthrough: we decided to
store a partial asset loss table, obtained by discarding small losses,
by leveraging on the fact that loss curves for long enough return periods
are dominated by extreme events, i.e. there is no point in saving all
the small losses.

To that aim, since version 3.8 the engine honors a parameter called
``minimum_loss_fraction``, with a default value of 0.05,
which determine how many losses are discarded when storing the
asset loss table. The rule is simple: losses below

 ``mean_value_per_asset * minimum_loss_fraction``

are discarded. The mean value per asset is simply the total value of the
portfolio divided by the number of assets (notice that there a value for each
loss type, ``mean_value_per_asset`` is a vector). By default losses below 5% of
the mean value are discarded and in an ideal world with this value

1. the vast majority of the losses would be discarded, thus making the
   asset loss table storable;
2. the loss curves would still be nearly identical to the ones without
   discarding any loss, except for small return periods.

It is the job of the user to verify if 1 and 2 are true in the real world.
He can assess that by playing with the ``minimum_loss_fraction`` in a small
calculation, finding a good value for it, and then extending to the large
calculation. Clearly it is a matter of compromise: by sacrificing precision
it is possible to reduce enourmously the size of the stored asset loss table
and to make an impossible calculation possible.

NB: the asset loss table is interesting only when computing the aggregate
loss curves by tag: if there are no tags the total loss curve can be
computed from the event loss table (i.e.  the asset loss table
aggregated by asset *without discarding anything*) which is always
stored. Thanks to that it is always possible to compare the total loss curve
with the approximated loss curve, to assess the goodness
of the approximation.
