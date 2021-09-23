Extended consequences
=====================

Scenario damage calculations produce damage distributions, i.e. arrays with the
probability of being in each damage state listed in the fragility
functions. There is a damage distribution per each asset, event and
loss type, so you can easily produce *billions* of damage
distributions. This is why the engine provide facilities to
compute results based on aggregating the damage distributions,
possibly multiplied by suitable coefficients, i.e. *consequences*. In
general, from the damage distributions it is possible to compute
generic consequences by multiplying for known coefficients specified
in what is called the *consequence model*. For instance, from the
probability of being in the collapsed damage state, one might estimate
the number of fatalities, given the right multiplicative coefficient.
Another commonly computed consequence is the economic loss; in order
to estimated it, one need a different multiplicative coefficient for
each damage state and for each taxonomy. The consequence model can be
represented as a CSV file like the following:

===================	============	============	========	==========	===========	==========	
 taxonomy          	 consequence  	 loss_type  	 slight 	 moderate 	 extensive 	 complete 	
-------------------	------------	------------	--------	----------	-----------	----------	
 CR_LFINF-DUH_H2   	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 CR_LFINF-DUH_H4   	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 MCF_LWAL-DNO_H3   	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 MR_LWAL-DNO_H1    	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 MR_LWAL-DNO_H2    	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 MUR_LWAL-DNO_H1   	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 W-WS_LPB-DNO_H1   	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 W-WWD_LWAL-DNO_H1 	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 MR_LWAL-DNO_H3    	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
===================	============	============	========	==========	===========	==========	

The first field in the header is the name of a tag in the exposure; in
this case it is the taxonomy but it could be any other tag — for instance,
for volcanic ash-fall consequences, the roof-type might be more relevant,
and for recovery time estimates, the occupancy class might be more relevant.

The consequence framework is meant to be used for generic consequences,
not necessarily limited to earthquakes, because since version 3.6 the engine
provides a multi-hazard risk calculator.

The second field of the header, the ``consequence``, is a string
identifying the kind of consequence we are considering. It is
important because it is associated to the name of the function
to use to compute the consequence. It is rather easy to write
an additional function in case one needed to support a new kind of
consequence. You can show the list of consequences by the version of
the engine that you have installed with the command::

 $ oq info consequences  # in version 3.12
 The following 5 consequences are implemented:
 losses
 collapsed
 injured
 fatalities
 homeless

The other fields in the header are the loss type and the damage states.
For instance the coefficient 0.25 for "moderate" means that the cost to
bring a structure in "moderate damage" back to its undamaged state is
25% of the total replacement value of the asset. The loss type refers
to the fragility model, i.e. ``structural`` will mean that the
coefficients apply to damage distributions obtained from the fragility
functions defined in the file ``structural_fragility_model.xml``.

The Event Based Damage demo
----------------------------------------------------------------

Given a source model, a logic tree, an exposure, a set of fragility functions
and a set of consequence functions, the ``event_based_damage`` calculator
is able to compute results such as average consequences and average
consequence curves. The ``scenario_damage`` calculator does the same,
except it does not start from a source model and a logic tree, but
rather from a set of predetermined ruptures or ground motion fields,
and the averages are performed on the input parameter
``number_of_ground_motion_fields`` and not on the effective investigation time.

In the engine distribution, in the folders ``demos/risk/EventBasedDamage``
and ``demos/risk/ScenarioDamage`` there are examples of how to use the
calculators.

Let's start with the EventBasedDamage demo. The source model, the
exposure and the fragility functions are much simplified and you should
not consider them realistic for the Nepal, but they permit very fast
hazard and risk calculations. The effective investigation time is

``eff_time = 1 (year) x 1000 (ses) x 50 (rlzs) = 50,000 years``

and the calculation is using sampling of the logic tree. 
Notice that *it is an error to use full enumeration with the
event_based_damage calculator*.

The restriction is by design, since the event based damage calculator is
not able to track the results produced by different realizations.
When using sampling all the realizations have the same weight, so on
the risk side we can effectively consider all of them together. This is
why there will be a single output (for the effective risk realization)
and not 50 outputs (one for each hazard realization) as it would happen
for an ``event_based_risk`` calculation.

Normally the engine does not store the damage distributions for each
asset (unless you specify ``aggregate_by=id`` in the ``job.ini`` file).

By default it stores the aggregate damage distributions by summing on
all the assets in the exposure. If you are interested only in partial
sums, i.e. in aggregating only the distributions associated to a certain
tag combination, you can produce the partial sums by specifying the tags.
For instance ``aggregate_by = taxonomy`` will aggregate by taxonomy,
``aggregate_by = taxonomy, region`` will aggregate by taxonomy and region,
etc. The aggregated damage distributions (and aggregated consequences, if
any) will be stored in a table called ``risk_by_event`` which can be
accessed with pandas. The corresponding DataFrame will have fields
``event_id``, ``agg_id`` (integer referring to which kind of aggregation you
are considering), ``loss_id`` (integer referring to the loss type in consideration),
a column named ``dmg_X`` for each damage state and a column for each consequence.
In the EventBasedDamage demo the exposure has a field
called ``NAME_1`` and representing a geographic region in Nepal (i.e.
"East" or "Mid-Western") and there is an ``aggregate_by = NAME_1, taxonomy`` in the ``job.ini``.

Since the demo has 4 taxonomies ("Wood", "Adobe", "Stone-Masonry", "Unreinforced-Brick-Masonry")
there 4 x 2 = 8 possible aggregations; actually, there is also a 9th possibility corresponding to
aggregating on all assets by disregarding the tags. You can see the possible values of the
the ``agg_id`` field with the following command::

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

Armed with that knowledge it is pretty easy to understand the ``risk_by_event`` table:

.. python:

 >> from openquake.commonlib.datastore import read
 >> dstore = read(-1)  # the latest calculation
 >> df = dstore.read_df('risk_by_event', 'event_id')
           agg_id  loss_id      dmg_1      dmg_2      dmg_3      dmg_4         losses
 event_id                                                                            
 248            0        0   1.435510   0.790500   0.164890   0.033948    4936.949707
 248            8        0   1.435510   0.790500   0.164890   0.033948    4936.949707
 251            6        0  56.975407  56.554920  28.172340  20.393412  647603.125000
 251            8        0  56.975407  56.554920  28.172340  20.393412  647603.125000
 254            0        0   1.786917   0.984012   0.205254   0.042258    6145.497559
 ...          ...      ...        ...        ...        ...        ...            ...
 30687          8        0  57.137714  55.869644  27.525604  19.811300  634266.187500
 30688          0        0   4.220542   2.324150   0.484792   0.099810   14515.125000
 30688          8        0   4.220542   2.324150   0.484792   0.099810   14515.125000
 30690          0        0   1.660057   0.914153   0.190682   0.039258    5709.204102
 30690          8        0   1.660057   0.914153   0.190682   0.039258    5709.204102

[8066 rows x 7 columns]

It should be noticed that while there is a CSV exporter for the ``risk_by_event``
table, it is designed to export only the total aggregation component (i.e.
``agg_id=9`` in this example) for reasons of backward compatibility with the
past, the time when the only aggregation the engine could perform was the
total aggregation. Since the ``risk_by_event`` table is rather large, it is
recommmended to interact with it with pandas and not to export in CSV.
