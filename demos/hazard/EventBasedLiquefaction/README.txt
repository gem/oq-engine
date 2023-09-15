Event Based Liquefaction Demo

This calculation demo exercises the Event-Based liquefaction calculator with a
trivial source model logic tree, containing a single model with two area source.
This source adds complexity to the calculation due to uncertainties present in
nodal plane distribution and hypocentral depth.

We compute a Ground Motion Field, Liquefaction Occurence, and Probability of
Liquefaction for each rupture.

Expected runtime: ~5 minutes
Number of sites: 4154
Number of logic tree realizations: 50
GMPEs: AbrahamsonEtAL2014 (0.5), CauzziEtAl2014 (0.5)
IMTs: PGV
Outputs: Stochastic Event Sets, Ground Motion Fields
