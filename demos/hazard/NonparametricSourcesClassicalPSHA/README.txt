Classical PSHA Non-parametric sources Demo

This calculation demo exercises the Classical hazard caclculator with a reduced
source model logic tree, containing a single model with a non-parametric sources
with magnitude larger Mw7.0.

In this example, we first compute hazard curves for all IMTs and sites of
interest (see below). From each curve set we interpolate hazard maps at 10% and
2% probabilities of exceedance. Finally, we also extract Uniform Hazard Spectra
(UHS) for the same probabilities from the PGA and SA hazard maps.

Expected runtime: ~10 seconds
Number of sites: 168
Number of logic tree realizations: 3
GMPEs: MontalvaEtAl2017SSlab AbrahamsonEtAl2015SSlab ZhaoEtAl2006SSlabNSHMP2014
IMTs: PGA, SA(0.2), SA(0.5), SA(1.0), SA(2.0)
Outputs: Hazard Curves, Hazard Maps, UHS
