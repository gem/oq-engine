Hazard Disaggregation Demo

This calculation demo exercises the Disaggregation hazard with non-trivial
logic trees. The source model logic tree only contains a single source model,
which in turn contains two sources: an area source and a simple fault source.
Each source is defined with a different tectonic region type ("Stable
Continental Crust" and "Active Shallow Crust", respectively), and thus require
separate GMPEs to be defined for each region type. In GMPE logic tree for this
example, "ChiouYoungs2008" is specified for sources in the "Active Shallow
Crust" tectonic region, while "ToroEtAl2002" is specified for "Stable
Continental Crust" sources.

In this demo, we first calculate a hazard curve for the site of interest. We
then disaggregate in order to quantify the contribution to the level of hazard
at a 10% probability of exceedance, in terms of longitude, latitude, magnitude,
distance, epsilon, and tectonic region type. From this information we construct
a matrix of 6 dimensions, from which we extract multiple "sub-matrices". For a
more detailed description of disaggregation output, see
http://docs.openquake.org/oq-engine/calculators/hazard.html#disaggregation-matrices.

Expected runtime: <1 minute
Number of sites: 1
Number of logic tree realizations: 1
GMPEs: ChiouYoungs2008, ToroEtAl2002
IMTs: PGA
Outputs: Hazard Curves, Disaggregation Matrices
