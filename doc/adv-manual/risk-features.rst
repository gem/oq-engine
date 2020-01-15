Advanced risk features
======================

Here we document some new risk features which have not yet made it
into the engine manual. These are new features and cannot be
considered fully-tested and stable yet.


Taxonomy mapping
---------------------------------

In an ideal world, for every building type represented in the 
exposure model, there would be a unique matching function
in the vulnerability or fragility models. However, often it may
not be possible to have a one-to-one mapping of the taxonomy strings
in the exposure and those in the vulnerability or fragility models.
For cases where the exposure model has richer detail, many taxonomy
strings in the exposure would need to be mapped onto a single 
vulnerability or fragility function. In other cases where building
classes in the exposure are more generic and the fragility or vulnerability
functions are available for more specific building types, a modeller
may wish to assign more than one vulnerability or fragility function
to the same building type in the exposure with different weights.

We may encode such information into a `taxonomy_mapping.csv`
file like the following:

=========== ===========
taxonomy     conversion
----------- -----------
Wood Type A  Wood
Wood Type B  Wood
Wood Type C  Wood
=========== ===========

Using an external file is convenient, because we can avoid changing the
original exposure. If in the future we will be able to get specific
risk functions, then we will just remove the taxonomy mapping.
This usage of the taxonomy mapping (use proxies for missing risk
functions) is pretty useful, but there is also another usage which
is even more interesting.

Consider a situation where there are doubts about the precise
composition of the exposure. For instance we may know than in a given
geographic region 20% of the building of type "Wood" are of "Wood Type
A", 30% of "Wood Type B" and 50% of "Wood Type C", corresponding to
different risk functions, but do not know building per building
what it its precise taxonomy, so we just use a generic "Wood"
taxonomy in the exposure. We may encode the weight information into a
`taxonomy_mapping.csv` file like the following:

========= ============ =======
taxonomy   conversion   weight
--------- ------------ -------
Wood       Wood Type A  0.2
Wood       Wood Type B  0.3
Wood       Wood Type C  0.5
========= ============ =======

The engine will read this mapping file and when performing the risk calculation
will use all three kinds of risk functions to compute a single result
with a weighted mean algorithm. The sums of the weights must be 1
for each exposure taxonomy, otherwise the engine will raise an error.
In this case the taxonomy mapping file works like a risk logic tree.

Internally both the first usage and the second usage are treated in
the same way, since the first usage is a special case of the second
when all the weights are equal to 1.

Currently, this taxonomy mapping feature has been tested only for the scenario
and event based risk calculators.


Extended consequences
----------------------------------------------

Scenario damage calculations produce the so called *asset damage table*,
i.e. a set of damage distributions (the probability of being in each
damage state listed in the fragility functions) per each asset, event
and loss type. From the asset damage table it is possible to compute
generic consequences by multiplying for known coefficients that are
what is called the *consequence model*. For instance, from the probability
of being in the collapsed damage state one can estimate the number of
fatalities, given the right multiplicative coefficient.

By default the engine allows to compute economic losses; in that case the
coefficients depends on the taxonomy and the consequence model can be
represented as a CSV file like the following::

 taxonomy,cname,loss_type,slight,moderate,extensive,complete
 CR_LFINF-DUH_H2,losses,structural,0.05,0.25,0.6,1
 CR_LFINF-DUH_H4,losses,structural,0.05,0.25,0.6,1
 MCF_LWAL-DNO_H3,losses,structural,0.05,0.25,0.6,1
 MR_LWAL-DNO_H1,losses,structural,0.05,0.25,0.6,1
 MR_LWAL-DNO_H2,losses,structural,0.05,0.25,0.6,1
 MUR_LWAL-DNO_H1,losses,structural,0.05,0.25,0.6,1
 W-WS_LPB-DNO_H1,losses,structural,0.05,0.25,0.6,1
 W-WWD_LWAL-DNO_H1,losses,structural,0.05,0.25,0.6,1
 MR_LWAL-DNO_H3,losses,structural,0.05,0.25,0.6,1

The first field in the header is the name of a tag in the exposure; in
this case it is the taxonomy but it can be something else; for instance
for volcanic ash fall consequences the kind of roof you have will be
relevant. The framework is meant to be used for generic consequences,
even not related to earthquakes, because since version 3.6 the engine
provides a multi-risk calculator.

The second field of the header, the ``cname``, is a string identifying
the kind of consequence we are considering. It is important because it
is associated to the name of the plugin function to use to compute the
consequence; right now (engine 3.8) we only support
``cname="losses"``, but this will change in the future. The `cname` is
also used when saving the consequence outputs in the datastore; right
now we are storing only ``losses_by_event`` and ``losses_by_asset``
but additional outputs  ``<cname>_by_event`` and ``<cname>_by_asset``
will be stored in the future, should the CSV file contain references
to additional plugin functions. For instance we could have outputs
``fatalities_by_event`` and ``fatalities_by_asset``.

The other fields in the header are the loss_type and the damage states.
For instance the coefficient 0.05 for "moderate" means that 5% of the
value of the asset will be lost if we are in that damage state, while
the coefficient 1 for "complete" means that everything will be lost if
are in that state.
