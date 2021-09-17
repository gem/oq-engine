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

region_grid_spacing
---------------------

In our experience, the most common error made by out users is to
compute the hazard at the sites of the exposure. The issue is that it
very possible to have exposures with millions of assets on millions of
distinct hazard sites. Computing the GMFs for millions of sites is
hard or even impossible (there is a limit of 4 billion rows on the
size of the GMF table in the datastore).  Even in the cases when
computing the hazard is possible, then computing the risk starting
from an extremely large amount of GMFs will likely be impossible, due
to memory/runtime constraints.

The second most common error is to use an extremely fine grid for the
site model. Remember that if you have a resolution of 250 meters, a
square of 250 km x 250 km will contain one million sites, which is
definitely too much. The engine when designed when the site models
had resolutions around 5-10 km, i.e. of the same order of the hazard
grid, while nowadays the vs30 fields have a much larger resolution.

Both problems can be solved in a simple way by specifying the
``region_grid_spacing`` parameter. Make it large enough that the
resulting number of sites becomes reasonable and you are done.
You will loose some precision, but that is preferable to not
being able to run the calculation. You will need to run a sensitivity
analysis with different values of ``region_grid_spacing`` parameter
to make sure that you get consistent results, but that's it.

Once a ``region_grid_spacing`` is specified, the engine computes the
convex hull of the exposure sites and builds a grid of hazard sites,
associating the site parameters from the closest site in the site model
and discarding sites in region where there are no assets (i.e. more
distant than ``region_grid_spacing * sqrt(2)``). The precise logic
is encoded in the function
``openquake.commonlib.readinput.get_sitecol_assetcol``, if you want
to know the nitty-gritty details.

Our recommendation is to use the command ``oq prepare_site_model`` to
apply such logic before starting a calculation and thus producing a
custom site model file tailored to your exposure (see the section
:ref:`prepare_site_model`).


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

Disabling the computation of the epsilon matrix
----------------------------------------------------------------

The vulnerability functions using continuous distributions (lognormal/beta)
to characterize the uncertainty in the loss ratio, specify the mean loss
ratios and the corresponding coefficients of variation for a set of intensity
levels. They are used to build the so called epsilon matrix within the engine,
governing how loss ratios are sampled from the distribution for each asset.

There is clearly a performance/memory penalty associated with the propagation
of uncertainty in the vulnerability to losses. The epsilon matrix has 
to be computed and its size is huge (for instance with 1 million events
and 1 million assets the epsilon matrix require 8 TB of RAM) so in large
calculation it is impossible to generate it. In the past the only solution
was setting

``ignore_covs = true``

in the `job.ini` file. Then the engine would compute just the mean loss
ratios by ignoring the uncertainty.
Since engine 3.12 there is a better solution: setting

``ignore_master_seed = true``

in the `job.ini` file. Then the engine will compute the mean loss
ratios but also store information about the uncertainty of the results
in the asset loss table, in the column "variance", by using the formulae

.. math::

    variance &= \Sigma_i \sigma_i^2 \ for\ asset\_correl=0 \\
    variance &= (\Sigma_i \sigma_i)^2 \ for\ asset\_correl=1

in terms of the variance of each asset for the event and intensity level in
consideration, extracted from the asset loss and the
coefficients of variation. People interested in the details should look at
the implementation in https://github.com/gem/oq-engine/blob/master/openquake/risklib/scientific.py.

The asset loss table
====================

When performing an event based risk calculation the engine
keeps in memory a table with the losses for each asset and each event,
for each loss type. It is usually impossible to fully store such table,
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

To that aim,the engine honors a parameter called
``minimum_asset_loss`` which determine how many losses are discarded
when storing the asset loss table. The rule is simple: losses below
``minimum_asset_loss`` are discarded. By choosing the threshold
properly in an ideal world

1. the vast majority of the losses would be discarded, thus making the
   asset loss table storable;
2. the loss curves would still be nearly identical to the ones without
   discarding any loss, except for small return periods.

It is the job of the user to verify if 1 and 2 are true in the real world.
He can assess that by playing with the ``minimum_asset_loss`` in a small
calculation, finding a good value for it, and then extending to the large
calculation. Clearly it is a matter of compromise: by sacrificing precision
it is possible to reduce enourmously the size of the stored asset loss table
and to make an impossible calculation possible.

Starting from engine 3.11 the asset loss table is stored if the user
specifies

``aggregate_by = id``

in the job.ini file. In large calculations it extremely easy to run out of
memory or the make the calculation extremely slow, so we recommend
not to store the asset loss table. The functionality is there for the sole
purpose of debugging small calculations, for instance to see the effect
of the ``minimum_asset_loss`` approximation at the asset level.

For large calculations usually one is interested in the aggregate loss
table, which contains the losses per event and per aggregation tag (or
multi-tag). For instance, the tag ``occupancy`` has the three values
"Residential", "Industrial" and "Commercial" and by setting

``aggregate_by = occupancy``

the engine will store a pandas DataFrame called ``risk_by_event` with a
field ``agg_id`` with 4 possible value: 0 for "Residential", 1 for
"Industrial", 2 for "Commercial" and 3 for the full aggregation.

NB: if the parameter ``aggregate_by`` is not specified, the engine will
still compute the aggregate loss table but then the ``agg_id`` field will
have a single value 0 corresponding to the total portfolio losses.

The Probable Maximum Loss (PML) and the loss curves
---------------------------------------------------

Given an effective investigation time and a return period,
the engine is able to compute a PML for each
aggregation tag. It does so by using the function
``openquake.risklib.scientific.losses_by_period`` which takes in input
an array of cumulative losses associated to the aggregation tag, a
list of or return periods, and the effective investigation time. If
there is a single return period the function returns the PML; if there are
multiple return periods it returns the loss curve. The two concepts
are essentially the same thing, since a loss curve is just an array of
PMLs, one for each return period. For instance

.. code-block:: python

   >>> from openquake.risklib.scientific import losses_by_period
   >>> losses = [3, 2, 3.5, 4, 3, 23, 11, 2, 1, 4, 5, 7, 8, 9, 13, 0]
   >>> [PML_500y] = losses_by_period(losses, [500], eff_time=1000)
   >>> PML_500y
   13.0

computes the Probably Maximum Loss at 500 years for the given losses
with an effective investigation time of 1000 years. The algorithm works
by ordering the losses (suppose there are E > 1 losses) generating E time
periods ``eff_time/E, eff_time/(E-1), ... eff_time/1`` and log-interpolating
the loss at the return period. Of course this works only if the condition

``eff_time/E < return_period < eff_time``

is respected. In this example there are E=16 losses, so the return period
must be in the range 62.5 .. 1000 years. If the return period is too
small the PML will be zero

>>> losses_by_period(losses, [50], eff_time=1000)
array([0.])

while if the return period is outside the investigation range we will
refuse the temptation to extrapolate and we will return NaN instead:

>>> losses_by_period(losses, [1500], eff_time=1000)
array([nan])

The rules above are the reason while you will see zeros or NaNs in the
loss curves generated by the engine sometimes, especially when there are
too few events: the valid range will be small and some return periods
may slip outside the range.

In order to compute aggregate loss curves you must
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
    
If you do not set the ``aggregate_by`` parameter
you will still able to compute the total loss curve 
(for the entire portfolio of assets), and the total average losses.

Aggregating by multiple tags
----------------------------

The engine also supports aggregation my multiple tags. For instance
the second event based risk demo (the file ``job_eb.ini``) has a line

   ``aggregate_by = NAME_1, taxonomy``

and it is able to aggregate both on geographic region (``NAME_1``) and
on taxonomy. There are 25 possible combinations, that you can see with
the command::

   $ oq show agg_keys
   | NAME_1_ | taxonomy_ | NAME_1      | taxonomy                   |
   +---------+-----------+-------------+----------------------------+
   | 1       | 1         | Mid-Western | Wood                       |
   | 1       | 2         | Mid-Western | Adobe                      |
   | 1       | 3         | Mid-Western | Stone-Masonry              |
   | 1       | 4         | Mid-Western | Unreinforced-Brick-Masonry |
   | 1       | 5         | Mid-Western | Concrete                   |
   | 2       | 1         | Far-Western | Wood                       |
   | 2       | 2         | Far-Western | Adobe                      |
   | 2       | 3         | Far-Western | Stone-Masonry              |
   | 2       | 4         | Far-Western | Unreinforced-Brick-Masonry |
   | 2       | 5         | Far-Western | Concrete                   |
   | 3       | 1         | West        | Wood                       |
   | 3       | 2         | West        | Adobe                      |
   | 3       | 3         | West        | Stone-Masonry              |
   | 3       | 4         | West        | Unreinforced-Brick-Masonry |
   | 3       | 5         | West        | Concrete                   |
   | 4       | 1         | East        | Wood                       |
   | 4       | 2         | East        | Adobe                      |
   | 4       | 3         | East        | Stone-Masonry              |
   | 4       | 4         | East        | Unreinforced-Brick-Masonry |
   | 4       | 5         | East        | Concrete                   |
   | 5       | 1         | Central     | Wood                       |
   | 5       | 2         | Central     | Adobe                      |
   | 5       | 3         | Central     | Stone-Masonry              |
   | 5       | 4         | Central     | Unreinforced-Brick-Masonry |
   | 5       | 5         | Central     | Concrete                   |

The lines in this table are associated to the *generalized aggregation ID*,
``agg_id`` which is an index going from ``0`` (meaning aggregate assets with
NAME_1=*Mid-Western* and taxonomy=*Wood*) to ``24`` (meaning aggregate assets
with NAME_1=*Mid-Western* and taxonomy=*Wood*); moreover ``agg_id=25`` means
full aggregation.

The ``agg_id`` field enters in ``risk_by_event`` and in outputs like
the aggregate losses; for instance::

   $ oq show agg_losses-rlzs
   | agg_id | rlz | loss_type     | value       |
   +--------+-----+---------------+-------------+
   | 0      | 0   | nonstructural | 2_327_008   |
   | 0      | 0   | structural    | 937_852     |
   +--------+-----+---------------+-------------+
   | ...    + ... + ...           + ...         +
   +--------+-----+---------------+-------------+
   | 25     | 1   | nonstructural | 100_199_448 |
   | 25     | 1   | structural    | 157_885_648 |

The exporter (``oq export agg_losses-rlzs``) converts back the ``agg_id``
to the proper combination of tags; ``agg_id=25``, i.e. full aggregation,
is replaced with the string ``*total*``.

By knowing the number of events, the number of aggregation keys and the
number of loss types, it is possible to give an upper limit to the size
of ``risk_by_event``. In the demo there are 1703 events, 26 aggregation
keys and 2 loss types, so ``risk_by_event`` contains at most

  1703 * 26 * 2 = 88,556 rows

This is an upper limit, since some combination can produce zero losses
and are not stored, especially if the ``minimum_asset_loss`` feature is
used. In the case of the demo actually only 20,877 rows are nonzero::

   $ oq show risk_by_event
          event_id  agg_id  loss_id           loss      variance
   ...
   [20877 rows x 5 columns]
