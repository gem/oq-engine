Classical PSHA Logic Tree Demo, Case 2

This calculation demo exercises the Classical hazard calculator with a non-trivial
source model logic tree, containing a single source model with absolute uncertainties
on Gutenberg-Richter a and b values and maximum magnitude.

This demo also specifies a non-trivial GMPE logic tree, containing two branching
levels and a total of four GMPEs (two for seismic sources in "Active Shallow Crust"
and two for "Stable Continental Crust").

In this example, we first compute hazard curves for each logic tree realization
for the single site of interest. We then compute the weighted mean of all 324
realizations and output this curve as a separate artifact. Similarly we also
compute 5%, 50%, and 95% weighted quantile aggregates.

Finally, we extract hazard maps and Uniform Hazard Spectra at 10% and 2% probabilities
of exceedance.

Expected runtime: ~20 seconds
Number of sites: 1
Number of logic tree realizations: 324
GMPEs: BooreAtkinson2008, ChiouYoungs2008, ToroEtAl2002, Campbell2003
IMTs: PGA
Outputs: Hazard Curves, Mean Hazard Curves, Quantile Hazard Curves, Hazard Maps, UHS
