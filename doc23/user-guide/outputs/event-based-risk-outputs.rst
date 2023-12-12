Event Based Risk Outputs
========================

The asset loss table
--------------------

When performing an event based risk calculation the engine
keeps in memory a table with the losses for each asset and each event,
for each loss type. It is usually impossible to fully store such a table,
because it is extremely large; for instance, for 1 million assets, 1
million events, 2 loss types and 4 bytes per loss ~8 TB of disk space
would be required. It is true that many events will produce zero losses
because of the `maximum_distance` and `minimum_intensity` parameters,
but still, the asset loss table is prohibitively large and for many years
could not be stored. In engine 3.8 we made a breakthrough: we decided to
store a partial asset loss table, obtained by discarding small losses,
by leveraging on the fact that loss curves for long enough return periods
are dominated by extreme events, i.e. there is no point in saving all
the small losses.

To that aim, the engine honours a parameter called
``minimum_asset_loss`` which determines how many losses are discarded
when storing the asset loss table. The rule is simple: losses below
``minimum_asset_loss`` are discarded. By choosing the threshold
properly in an ideal world

1. the vast majority of the losses would be discarded, thus making the
   asset loss table storable;
2. the loss curves would still be nearly identical to the ones without
   discarding any loss, except for small return periods.

It is the job of the user to verify if 1 and 2 are true in the real world.
He can assess that by playing with the ``minimum_asset_loss`` in a small
calculation, finding a good value for it, and then extending it to the large
calculation. Clearly, it is a matter of compromise: by sacrificing precision
it is possible to reduce enormously the size of the stored asset loss table
and to make an impossible calculation possible.

Starting from engine 3.11 the asset loss table is stored if the user
specifies

``aggregate_by = id``

in the job.ini file. In large calculations it is extremely easy to run out of
memory or make the calculation extremely slow, so we recommend
not to store the asset loss table. The functionality is there for the sole
purpose of debugging small calculations, for instance, to see the effect
of the ``minimum_asset_loss`` approximation at the asset level.

For large calculations usually one is interested in the aggregate loss
table, which contains the losses per event and per aggregation tag (or
multi-tag). For instance, the tag ``occupancy`` has the three values
"Residential", "Industrial" and "Commercial" and by setting

``aggregate_by = occupancy``

the engine will store a pandas DataFrame called ``risk_by_event`` with a
field ``agg_id`` with 4 possible value: 0 for "Residential", 1 for
"Industrial", 2 for "Commercial" and 3 for the full aggregation.

NB: if the parameter ``aggregate_by`` is not specified, the engine will
still compute the aggregate loss table but then the ``agg_id`` field will
have a single value of 0 corresponding to the total portfolio losses.

The Probable Maximum Loss (PML) and the loss curves
---------------------------------------------------

Given an effective investigation time and a return period,
the engine is able to compute a PML for each
aggregation tag. It does so by using the function
``openquake.risklib.scientific.losses_by_period`` which takes as input
an array of cumulative losses associated with the aggregation tag, a
list of the return periods, and the effective investigation time. If
there is a single return period the function returns the PML; if there are
multiple return periods it returns the loss curve. The two concepts
are essentially the same thing, since a loss curve is just an array of
PMLs, one for each return period. 

For instance:

.. code-block:: python

   >>> from openquake.risklib.scientific import losses_by_period
   >>> losses = [3, 2, 3.5, 4, 3, 23, 11, 2, 1, 4, 5, 7, 8, 9, 13, 0]
   >>> [PML_500y] = losses_by_period(losses, [500], eff_time=1000)
   >>> PML_500y
   13.0

computes the Probably Maximum Loss at 500 years for the given losses
with an effective investigation time of 1000 years. The algorithm works
by ordering the losses (suppose there are E losses,  E > 1) generating E time
periods ``eff_time/E, eff_time/(E-1), ... eff_time/1``, and log-interpolating
the loss at the return period. Of course this works only if the condition
``eff_time/E < return_period < eff_time`` is respected.

In this example there are E=16 losses, so the return period
must be in the range 62.5 .. 1000 years. If the return period is too
small the PML will be zero

>>> losses_by_period(losses, [50], eff_time=1000)
array([0.])

while if the return period is outside the investigation range, we will
refuse the temptation to extrapolate and we will return NaN instead:

>>> losses_by_period(losses, [1500], eff_time=1000)
array([nan])

The rules above are the reason why you will see zeros or NaNs in the
loss curves generated by the engine sometimes, especially when there are
too few events (the valid range will be small and some return periods
may slip outside the range).

Aggregate loss curves
~~~~~~~~~~~~~~~~~~~~~
In some cases the computation of the PML is particularly simple and
you can do it by hand: this happens when the ratio
``eff_time/return_period`` is an integer. Consider for instance a case with
``eff_time=10,000`` years and ``return_period=2,000`` years;
suppose there are the following 10 losses aggregating the commercial
and residential buildings of an exposure:

>>> import numpy as np
>>> losses_COM = np.array([123, 0, 400, 0, 1500, 200, 350, 0, 700, 600])
>>> losses_RES = np.array([0, 800, 200, 0, 500, 1200, 250, 600, 300, 150])

The loss curve associate the highest loss to 10,000 years, the second
highest to 10,000 / 2 years, the third highest to 10,000 / 3 years, the
fourth highest to 10,000 / 4 years, the fifth highest to 10,000 / 5 years
and so on until the lowest loss is associated to 10,000 / 10 years.
Since the return period is 2,000 = 10,000 / 5 to compute the MPL
it is enough to take the fifth loss ordered in descending order:

>>> MPL_COM = [1500, 700, 600, 400, 350, 200, 123, 0, 0, 0][4] = 350
>>> MPL_RES = [1200, 800, 600, 500, 300, 250, 200, 150, 0, 0][4] = 300

Given this algorithm, it is clear why the MPL cannot be additive, i.e.
MPL(COM + RES) != MPL(COM) + MPL(RES): doing the sums before or
after the ordering of the losses is different. In this example
by taking the fifth loss of the sorted sums

>>> sorted(losses_COM + losses_RES, reverse=True)
[2000, 1400, 1000, 800, 750, 600, 600, 600, 123, 0]

one gets ``MPL(COM + RES) = 750`` which is different from
``MPL(RES) + MPL(COM) = 350 + 300 = 650``.

The engine is able to compute aggregate loss curves correctly, i.e.
by doing the sums before the ordering phase. In order to perform
aggregations, you need to set the ``aggregate_by`` parameter in the
``job.ini`` by specifying tags over which you wish to perform the
aggregation. Your exposure must contain the specified tags
for each asset.  We have an example for Nepal in our event based risk
demo.  The exposure for this demo contains various tags and in
particular a geographic tag called NAME_1 with values "Mid-Western",
"Far-Western", "West", "East", "Central", and the ``job_eb.ini`` file
defines

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
you will still be able to compute the total loss curve 
(for the entire portfolio of assets), and the total average losses.