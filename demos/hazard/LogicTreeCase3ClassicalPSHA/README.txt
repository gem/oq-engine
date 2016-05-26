Classical PSHA Logic Tree Demo, Case 3

This calculation demo exercises the Classical hazard calculator with a non-trivial
source model logic tree, containing a single source model with relative uncertainties
on Gutenberg-Richter b values and maximum magnitude.

This demo also specifies a non-trivial GMPE logic tree, containing two branching
levels and a total of four GMPEs (two for seismic sources in "Active Shallow Crust"
and two for "Stable Continental Crust").

In this example, we first compute hazard curves for each logic tree realization
for the single site of interest. We then compute 5%, 50%, and 95% weighted quantile
aggregates of all 36 realizations.

Finally, we extract hazard maps at 10% and 2% probabilities of exceedance.

Expected runtime: ~3 minutes
Number of sites: 1
Number of logic tree realizations: 36
GMPEs: BooreAtkinson2008, ChiouYoungs2008, ToroEtAl2002, Campbell2003
IMTs: PGA
Outputs: Hazard Curves, Quantile Hazard Curves, Hazard Maps
