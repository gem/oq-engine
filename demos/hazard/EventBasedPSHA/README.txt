Event Based PSHA Area Source Demo

This calculation demo exercises the Event-Based hazard calculator with a
trivial source model logic tree, containing a single model with a single area
source. This source adds complexity to the calculation due to the presence of
a nodal plane distribution containing 12 uncertainties.

In this example, we first simulate 10 Stochastic Event Sets, each containing a
random set of ruptures. (Note: This random element is controlled by the
`random_seed` in the job.ini.) We then compute a Ground Motion Field for each
rupture.

Once GMFs are computed, we can produce a hazard curve for the site of interest
by aggregating all of the ground motion values. This method of hazard curve
computation is considered to be equivalent to the Classical PSHA approach.

Finally, this demo also extracts a hazard map at a 10% probability of exceedance.

Expected runtime: ~5 minutes
Number of sites: 1
Number of logic tree realizations: 1
GMPEs: BooreAtkinson2008
IMTs: PGA
Outputs: Stochastic Event Sets, Ground Motion Fields, Hazard Curves, Hazard Maps
