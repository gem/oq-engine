.. _consequence-models:

Consequence Models
==================

Starting from OpenQuake engine v1.7, the Scenario Damage calculator also accepts consequence models in addition to 
fragility models, in order to estimate consequences based on the calculated damage distribution. The user may provide 
one *Consequence Model* file corresponding to each loss type (amongst structural, nonstructural, contents, and business 
interruption) for which a *Fragility Model* file is provided. Whereas providing a *Fragility Model* file for at least one 
loss type is mandatory for running a Scenario Damage calculation, providing corresponding *Consequence Model* files is 
optional.

This section describes the schema currently used to store consequence models, which are optional inputs for the Scenario 
Damage Calculator. A *Consequence Model* defines a set of consequence functions, describing the distribution of the loss 
(or consequence) ratio conditional on a set of discrete limit (or damage) states. These *Consequence Function* can be 
currently defined in OpenQuake engine by specifying the parameters of the continuous distribution of the loss ratio for 
each limit state specified in the fragility model for the corresponding loss type, for each taxonomy defined in the 
exposure model.

An example *Consequence Model* is shown in the listing below.::

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<consequenceModel id="consequence_example"
	                  assetCategory="buildings"
	                  lossCategory="structural">
	
	  <description>Consequence Model Example</description>
	  <limitStates>slight moderate extensive complete</limitStates>
	
	  <consequenceFunction id="RC_LowRise" dist="LN">
	    <params ls="slight" mean="0.04" stddev="0.00"/>
	    <params ls="moderate" mean="0.16" stddev="0.00"/>
	    <params ls="extensive" mean="0.32" stddev="0.00"/>
	    <params ls="complete" mean="0.64" stddev="0.00"/>
	  </consequenceFunction>
	
	</consequenceModel>
	
	</nrml>

The initial portion of the schema contains general information that describes some general aspects of the *Consequence 
Model*. The information in this metadata section is common to all of the functions in the *Consequence Model* and needs 
to be included at the beginning of every *Consequence Model* file. The parameters are described below:

- ``id``: a unique string used to identify the *Consequence Model*. This string can contain letters (a–z; A–Z), numbers (0–9), dashes (-), and underscores (_), with a maximum of 100 characters.
- ``assetCategory``: an optional string used to specify the type of assets for which consequencefunctions will be defined in this file (e.g: buildings, lifelines).
- ``lossCategory``: mandatory; valid strings for this attribute are “structural”, “nonstructural”, “contents”, and “business_interruption”.
- ``description``: mandatory; a brief string (ASCII) with further information about the *Consequence Model*, for example, which building typologies are covered or the source of the functions in the *Consequence Model*.
- ``limitStates``: mandatory; this field is used to define the number and nomenclature of each limit state. Four limit states are employed in the example above, but it is possible to use any number of discrete states. The limit states must be provided as a set of strings separated by white spaces between each limit state. Each limit state string can contain letters (a–z; A–Z), numbers (0–9), dashes (-), and underscores (_). Please ensure that there is no white space within the name of any individual limit state. The number and nomenclature of the limit states used in the *Consequence Model* should match those used in the corresponding *Fragility Model*.::

	<consequenceModel id="consequence_example"
	                  assetCategory="buildings"
	                  lossCategory="structural">
	
	  <description>Consequence Model Example</description>
	  <limitStates>slight moderate extensive complete</limitStates>

The following snippet from the above *Consequence Model* example file defines a *Consequence Function* using a lognormal 
distribution to model the uncertainty in the consequence ratio for each limit state::

	  <consequenceFunction id="RC_LowRise" dist="LN">
	    <params ls="slight" mean="0.04" stddev="0.00"/>
	    <params ls="moderate" mean="0.16" stddev="0.00"/>
	    <params ls="extensive" mean="0.32" stddev="0.00"/>
	    <params ls="complete" mean="0.64" stddev="0.00"/>
	  </consequenceFunction>

The following attributes are needed to define a *Consequence Function*:

- ``id``: mandatory; a unique string used to identify the taxonomy for which the function is being defined. This string is used to relate the *Consequence Function* with the relevant asset in the *Exposure Model*. This string can contain letters (a–z; A–Z), numbers (0–9), dashes (-), and underscores (_), with a maximum of 100 characters.
- ``dist``: mandatory; for vulnerability function which use a continuous distribution to model the uncertainty in the conditional loss ratios, this attribute should be set to either ``“LN”`` if using the lognormal distribution, or to ``“BT”`` if using the Beta distribution [1]_.
- ``params``: mandatory; this field is used to define the parameters of the continuous distribution used for modelling the uncertainty in the loss ratios for each limit state for this *Consequence Function*. For a lognormal distrbution, the two parameters required to specify the function are the mean and standard deviation of the consequence ratio. These parameters are defined for each limit state using the attributes ``mean`` and ``stddev`` respectively. The attribute ``ls`` specifies the limit state for which the parameters are being defined. The parameters for each limit state must be provided on a separate line. The number and names of the limit states in each *Consequence Function* must be equal to the number of limit states defined in the corresponding *Fragility Model* using the attribute ``limitStates``.

Extended consequences
---------------------

Scenario damage calculations produce damage distributions, i.e. arrays containing the number of buildings in each damage 
state defined in the fragility functions. There is a damage distribution per each asset, event and loss type, so you can 
easily produce *billions* of damage distributions. This is why the engine provide facilities to compute results based on 
aggregating the damage distributions, possibly multiplied by suitable coefficients, i.e. *consequences*.

For instance, from the probability of being in the collapsed damage state, one may estimate the number of fatalities, 
given the right multiplicative coefficient. Another commonly computed consequence is the economic loss; in order to 
estimated it, one need a different multiplicative coefficient for each damage state and for each taxonomy. The table of 
coefficients, a.k.a. the *consequence model*, can be represented as a CSV file like the following:

+-------------------+-------------+------------+--------+----------+-----------+----------+
|      taxonomy     | consequence |  loss_type | slight | moderate | extensive | complete |
+===================+=============+============+========+==========+===========+==========+
|  CR_LFINF-DUH_H2  |    losses   | structural |  0.05  |   0.25   |    0.6    |     1    |
+-------------------+-------------+------------+--------+----------+-----------+----------+
|  CR_LFINF-DUH_H4  |    losses   | structural |  0.05  |   0.25   |    0.6    |     1    |
+-------------------+-------------+------------+--------+----------+-----------+----------+
|  MCF_LWAL-DNO_H3  |    losses   | structural |  0.05  |   0.25   |    0.6    |     1    |
+-------------------+-------------+------------+--------+----------+-----------+----------+
|   MR_LWAL-DNO_H1  |    losses   | structural |  0.05  |   0.25   |    0.6    |     1    |
+-------------------+-------------+------------+--------+----------+-----------+----------+
|   MR_LWAL-DNO_H2  |    losses   | structural |  0.05  |   0.25   |    0.6    |     1    |
+-------------------+-------------+------------+--------+----------+-----------+----------+
|  MUR_LWAL-DNO_H1  |    losses   | structural |  0.05  |   0.25   |    0.6    |     1    |
+-------------------+-------------+------------+--------+----------+-----------+----------+
|  W-WS_LPB-DNO_H1  |    losses   | structural |  0.05  |   0.25   |    0.6    |     1    |
+-------------------+-------------+------------+--------+----------+-----------+----------+
| W-WWD_LWAL-DNO_H1 |    losses   | structural |  0.05  |   0.25   |    0.6    |     1    |
+-------------------+-------------+------------+--------+----------+-----------+----------+
|   MR_LWAL-DNO_H3  |    losses   | structural |  0.05  |   0.25   |    0.6    |     1    |
+-------------------+-------------+------------+--------+----------+-----------+----------+

The first field in the header is the name of a tag in the exposure; in this case it is the taxonomy but it could be any 
other tag — for instance, for volcanic ash-fall consequences, the roof-type might be more relevant, and for recovery 
time estimates, the occupancy class might be more relevant.

The consequence framework is meant to be used for generic consequences, not necessarily limited to earthquakes, because 
since version 3.6 the engine provides a multi-hazard risk calculator.

The second field of the header, the ``consequence``, is a string identifying the kind of consequence we are considering. 
It is important because it is associated to the name of the function to use to compute the consequence. It is rather 
easy to write an additional function in case one needed to support a new kind of consequence. You can show the list of 
consequences by the version of the engine that you have installed with the command::

	$ oq info consequences  # in version 3.12
	The following 5 consequences are implemented:
	losses
	collapsed
	injured
	fatalities
	homeless

The other fields in the header are the loss type and the damage states. For instance the coefficient 0.25 for “moderate” 
means that the cost to bring a structure in “moderate damage” back to its undamaged state is 25% of the total 
replacement value of the asset. The loss type refers to the fragility model, i.e. ``structural`` will mean that the 
coefficients apply to damage distributions obtained from the fragility functions defined in the file ``structural_fragility_model.xml``.

****************************
discrete_damage_distribution
****************************

Damage distributions are called discrete when the number of buildings in each damage is an integer, and continuous when 
the number of buildings in each damage state is a floating point number. Continuous distributions are a lot more 
efficient to compute and therefore that is the default behavior of the engine, at least starting from version 3.13. You 
can ask the engine to use discrete damage distribution by setting the flag in the job.ini file ``discrete_damage_distribution = true``
However, it should be noticed that setting ``discrete_damage_distribution = true`` will raise an error if the exposure 
contains a floating point number of buildings for some asset. Having a floating point number of buildings in the 
exposure is quite common since the “number” field is often estimated as an average.

Even if the exposure contains only integers and you have set ``discrete_damage_distribution = true`` in the job.ini, the 
aggregate damage distributions will normally contains floating point numbers, since they are obtained by summing 
integer distributions for all seismic events of a given hazard realization and dividing by the number of events of that 
realization.

By summing the number of buildings in each damage state one will get the total number of buildings for the given 
aggregation level; if the exposure contains integer numbers than the sum of the numbers will be an integer, apart from 
minor differences due to numeric errors, since the engine stores even discrete distributions as floating point numbers.

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

It should be noted that while there is a CSV exporter for the ``risk_by_event`` table, it is designed to export only the 
total aggregation component (i.e. ``agg_id=9`` in this example) for reasons of backward compatibility with the past, the 
time when the only aggregation the engine could perform was the total aggregation. Since the ``risk_by_event`` table can 
be rather large, it is recommmended to interact with it with pandas and not to export in CSV.

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

The demo in ``demos/risk/ScenarioDamage`` is similar to the EventBasedDemo (it still refers to Nepal) but it uses a 
much large exposure with 9063 assets and 5,365,761 building. Moreover the configuration file is split in two: first you 
should run ``job_hazard.ini`` and then run ``job_risk.ini`` with the ``--hc`` option.

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

.. [1] Note that as of OpenQuake engine v1.8, the uncertainty in the consequence ratios is ignored, and only the mean consequence ratios for the set of limit states is considered when computing the consequences from the damage distribution. Consideration of the uncertainty in the consequence ratios is planned for future releases of the OpenQuake engine.