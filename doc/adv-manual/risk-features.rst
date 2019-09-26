Advanced risk features
======================

Here we document some new risk features which are not mentioned in
the manual.

Taxonomy mapping
---------------------------------

In an ideal world for each taxonomy in the exposure there is a taxonomy
in the risk functions (vulnerability/fragility). In the real world there
may be less risk functions than taxonomies in the exposure and so
different taxonomies must be mapped to the same risk function.
For instance we may have buildings in the exposure of different
kind of woods, but only a generic risk function for wood.

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

The engine will read such file and when performing the risk calculation
will use all three kinds of risk functions and compute a single result
with a weighted mean algorithm. The sums of the weights must be 1
for each exposure taxonomy, otherwise the engine will raise an error.
In this case the taxonomy mapping file works like a risk logic tree.

Internally both the first usage and the second usage are treated in
the same way, since the first usage is a special case of the second
when all the weights are equal to 1
