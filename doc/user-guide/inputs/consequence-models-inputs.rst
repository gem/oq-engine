.. _consequence-models:

Consequence Models
==================

Consequence models are optional inputs for ``scenario_damage`` and
``event_based_damage`` calculations. They convert the damage distributions
computed from fragility functions into quantities such as economic losses,
fatalities, homelessness, collapse, or loss of functionality.

Consequence models use CSV format. The former NRML/XML consequence format is
no longer supported. A minimal model for ground-shaking losses is:

.. code-block:: csv

   risk_id,consequence,loss_type,peril,slight,moderate,extreme,complete
   Adobe,losses,structural,groundshaking,0.04,0.31,0.60,1.00
   Concrete,losses,structural,groundshaking,0.04,0.31,0.60,1.00

The columns have the following meanings:

- ``risk_id`` identifies the fragility function to which the row applies.
  It must be consistent with the risk IDs selected by the taxonomy mapping.
- ``consequence`` selects the calculation applied to the coefficients. Run
  ``oq info consequences`` to list the values supported by the installed
  engine version. Common values include ``losses``, ``collapsed``,
  ``injured``, ``fatalities``, ``homeless``, and ``non_operational``.
- ``loss_type`` identifies the corresponding fragility loss type. It defaults
  to ``structural`` when omitted.
- ``peril`` identifies the peril associated with the fragility function. It
  defaults to ``groundshaking`` when omitted and must be explicit in a
  multi-peril model.
- The remaining column names must exactly match the limit states in the
  corresponding fragility model. Each value is the coefficient conditional
  on that damage state.

For a ``losses`` consequence, a coefficient of 0.25 means that the repair cost
is 25 percent of the asset value for the specified loss type and damage
state. Other consequences use the relevant exposure quantity: for example,
``collapsed`` applies to the number of units, ``fatalities`` and ``injured``
apply to occupants at the configured ``time_event``, and ``homeless`` applies
to residents.

Reference the CSV file in ``job.ini`` as follows:

.. code-block:: ini

   [consequence]
   consequence_file = {'taxonomy': 'consequences.csv'}

The ``taxonomy`` key is retained for compatibility and maps the CSV
``risk_id`` values to the selected risk functions. A consequence file can
also be keyed by another exposure tag when coefficients vary by a property
such as occupancy or roof type.

The CSV stores deterministic coefficients. It does not define a probability
distribution or uncertainty for a consequence ratio. Providing at least one
fragility model is mandatory for a damage calculation; providing a
consequence model is optional.

****************************
discrete_damage_distribution
****************************

Damage distributions are called discrete when the number of buildings in each
damage state is an integer, and continuous when it is a floating-point number.
Continuous distributions are more efficient to compute and are the default.
To request a discrete damage distribution, set
``discrete_damage_distribution = true`` in ``job.ini``. This setting raises an
error if the exposure contains a non-integer number of buildings for any
asset. Non-integer values are common when ``number`` is an estimate or
average.

Even when the exposure contains only integers and
``discrete_damage_distribution = true``, aggregate damage distributions
normally contain floating-point numbers. They are obtained by summing integer
distributions for all seismic events in a hazard realization and dividing by
the number of events in that realization.

Summing the values in all damage states gives the total number of buildings
for an aggregation level. If the exposure contains integers, this sum will be
an integer apart from small numerical differences, because the engine stores
even discrete distributions as floating-point numbers.

*************************
The EventBasedDamage demo
*************************

Given a source model, a logic tree, an exposure, a set of fragility functions and a set of consequence functions, the 
``event_based_damage`` calculator is able to compute results such as average consequences and average consequence curves. 
The ``scenario_damage`` calculator does the same, except it does not start from a source model and a logic tree, but 
rather from a set of predetermined ruptures or ground motion fields, and the averages are performed on the input 
parameter ``number_of_ground_motion_fields`` and not on the effective investigation time.

In the engine distribution, in the folders ``demos/risk/EventBasedDamage`` and ``demos/risk/ScenarioDamage`` there are 
examples of how to use the calculators.

Let’s start with the EventBasedDamage demo. The source model, the exposure and the fragility functions are much 
simplified and you should not consider them realistic for the Nepal, but they permit very fast hazard and risk 
calculations. The effective investigation time is ``eff_time = 1 (year) x 1000 (ses) x 50 (rlzs) = 50,000 years``
and the calculation is using sampling of the logic tree. Since all the realizations have the same weight, on the risk 
side we can effectively consider all of them together. This is why there will be a single output (for the effective risk 
realization) and not 50 outputs (one for each hazard realization) as it would happen for an ``event_based_risk`` 
calculation.

Normally the engine does not store the damage distributions for each asset (unless you specify ``aggregate_by=id`` in 
the ``job.ini`` file).

By default it stores the aggregate damage distributions by summing on all the assets in the exposure. If you are 
interested only in partial sums, i.e. in aggregating only the distributions associated to a certain tag combination, 
you can produce the partial sums by specifying the tags. For instance ``aggregate_by = taxonomy`` will aggregate by 
taxonomy, ``aggregate_by = taxonomy, region`` will aggregate by taxonomy and region, etc. The aggregated damage 
distributions (and aggregated consequences, if any) will be stored in a table called ``risk_by_event`` which can be 
accessed with pandas. The corresponding DataFrame will have fields ``event_id``, ``agg_id`` (integer referring to which 
kind of aggregation you are considering), ``loss_id`` (integer referring to the loss type in consideration), a column 
named ``dmg_X`` for each damage state and a column for each consequence. In the EventBasedDamage demo the exposure has 
a field called ``NAME_1`` and representing a geographic region in Nepal (i.e. “East” or “Mid-Western”) and there is an 
``aggregate_by = NAME_1, taxonomy`` in the ``job.ini``.

Since the demo has 4 taxonomies (“Wood”, “Adobe”, “Stone-Masonry”, “Unreinforced-Brick-Masonry”) there 4 x 2 = 8 
possible aggregations; actually, there is also a 9th possibility corresponding to aggregating on all assets by 
disregarding the tags. You can see the possible values of the the ``agg_id`` field with the following command::

	$ oq show agg_id
	                          taxonomy       NAME_1
	agg_id
	0                             Wood         East
	1                             Wood  Mid-Western
	2                            Adobe         East
	3                            Adobe  Mid-Western
	4                    Stone-Masonry         East
	5                    Stone-Masonry  Mid-Western
	6       Unreinforced-Brick-Masonry         East
	7       Unreinforced-Brick-Masonry  Mid-Western
	8                         *total*      *total*

Armed with that knowledge it is pretty easy to understand the ``risk_by_event`` table::

	>> from openquake.commonlib.datastore import read
	>> dstore = read(-1)  # the latest calculation
	>> df = dstore.read_df('risk_by_event', 'event_id')
	          agg_id  loss_id  dmg_1  dmg_2  dmg_3  dmg_4         losses
	event_id
	472            0        0    0.0    1.0    0.0    0.0    5260.828125
	472            8        0    0.0    1.0    0.0    0.0    5260.828125
	477            0        0    2.0    0.0    1.0    0.0    6368.788574
	477            8        0    2.0    0.0    1.0    0.0    6368.788574
	478            0        0    3.0    1.0    1.0    0.0    5453.355469
	...          ...      ...    ...    ...    ...    ...            ...
	30687          8        0   56.0   53.0   26.0   16.0  634266.187500
	30688          0        0    3.0    6.0    1.0    0.0   14515.125000
	30688          8        0    3.0    6.0    1.0    0.0   14515.125000
	30690          0        0    2.0    0.0    1.0    0.0    5709.204102
	30690          8        0    2.0    0.0    1.0    0.0    5709.204102
	[8066 rows x 7 columns]

The number of buildings in each damage state is integer (even if stored as a float) because the exposure contains only 
integers and the job.ini is setting explicitly ``discrete_damage_distribution = true``.

It should be noted that while there is a CSV exporter for the
``risk_by_event`` table, it is designed to export only the total aggregation
component (i.e. ``agg_id=8`` in this example) for reasons of backward
compatibility with the past, when the only aggregation the engine could
perform was the total aggregation. Since the ``risk_by_event`` table can be
rather large, it is recommended to interact with it with pandas and not to
export it to CSV.

There is instead a CSV exporter for the aggregated damage distributions (together with the aggregated consequences) that 
you may call with the command ``oq export aggrisk``; you can also see the distributions directly::

	$ oq show aggrisk
	   agg_id  rlz_id  loss_id        dmg_0     dmg_1     dmg_2     dmg_3     dmg_4        losses
	0       0       0        0    18.841061  0.077873  0.052915  0.018116  0.010036    459.162567
	1       3       0        0   172.107361  0.329445  0.591998  0.422925  0.548271  11213.121094
	2       5       0        0     1.981786  0.003877  0.005539  0.004203  0.004594    104.431755
	3       6       0        0   797.826111  1.593724  1.680134  0.926167  0.973836  23901.496094
	4       7       0        0    48.648529  0.120687  0.122120  0.060278  0.048386   1420.059448
	5       8       0        0  1039.404907  2.125607  2.452706  1.431690  1.585123  37098.269531

By summing on the damage states one gets the total number of buildings for each aggregation level::

	agg_id dmg_0 + dmg_1 + dmg_2 + dmg_3 + dmg_4 aggkeys
	0        19.000039 ~ 19                      Wood,East
	3       173.999639 ~ 174                     Wood,Mid-Western
	5         2.000004 ~ 2                       Stone-Masonry,Mid-Western
	6       802.999853 ~ 803                     Unreinforced-Brick-Masonry,East
	7        48.999971 ~ 49                      Unreinforced-Brick-Masonry,Mid-Western
	8      1046.995130 ~ 1047                    Total

***********************
The ScenarioDamage demo
***********************

The demo in ``demos/risk/ScenarioDamage`` is similar to the EventBasedDemo
(it still refers to Nepal), but it uses a much larger exposure with 9063
assets and 5,365,761 buildings. Moreover, the configuration file is split in
two: first run ``job_hazard.ini`` and then run ``job_risk.ini`` with the
``--hc`` option.

The first calculation will produce 2 sets of 100 ground motion fields each (since ``job_hazard.ini`` contains 
``number_of_ground_motion_fields = 100`` and the gsim logic tree file contains two GMPEs). The second calculation will 
use such GMFs to compute aggregated damage distributions. Contrarily to event based damage calculations, scenario damage 
calculations normally use full enumeration, since there are very few realizations (only two in this example), thus the 
scenario damage calculator is able to distinguish the results by realization.

The main output of a ``scenario_damage`` calculation is still the ``risk_by_event`` table which has exactly the same 
form as for the EventBasedDamage demo. However there is a difference when considering the aggrisk output: since we are 
using full enumeration we will produce a damage distribution for each realization::

	$ oq show aggrisk
	   agg_id  rlz_id  loss_id       dmg_0  ...  dmg_4        losses
	0       0       0        0  4173405.75  ...  452433.40625  7.779261e+09
	1       0       1        0  3596234.00  ...  633638.37500  1.123458e+10

The sum over the damage states will still produce the total number of buildings, which will be independent from 
the realization::

	rlz_id dmg_0 + dmg_1 + dmg_2 + dmg_3 + dmg_4
	0      5365761.0
	1      5365761.0

In this demo there is no ``aggregate_by`` specified, so the only aggregation which is performed is the total aggregation. 
You are invited to specify ``aggregate_by`` and study how ``aggrisk`` changes.
