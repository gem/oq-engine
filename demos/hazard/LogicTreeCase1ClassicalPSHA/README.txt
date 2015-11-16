Classical PSHA Logic Tree Demo, Case 1

This calculation demo exercises the Classical hazard calculator with a non-trivial
source model logic tree, containing two similar source models. Each source model
contains one area source and one simple fault source and they are nearly identical,
except that the area source geometry differs slightly.

This demo also specifies a non-trivial GMPE logic tree, containing two branching
levels and a total of four GMPEs (two for seismic sources in "Active Shallow Crust"
and two for "Stable Continental Crust").

In this example, we first compute hazard curves for each logic tree realization
for the single site of interest. We then compute the weighted mean of all eight
realizations and output this curve as a separate artifact. Similarly we also
compute 5%, 50%, and 95% weighted quantile aggregates.

Finally, we extract hazard maps and Uniform Hazard Spectra at a 10% probability
of exceedance.

Expected runtime: <1 minute
Number of sites: 1
Number of logic tree realizations: 8
GMPEs: BooreAtkinson2008, ChiouYoungs2008, ToroEtAl2002, Campbell2003
IMTs: PGA
Outputs: Hazard Curves, Mean Hazard Curves, Quantile Hazard Curves, Hazard Maps, UHS
