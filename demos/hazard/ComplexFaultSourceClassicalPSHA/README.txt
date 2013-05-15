Classical PSHA Complex Fault Source Demo

This calculation demo exercises the Classical hazard calculator with a trivial
source model logic tree, containing a single model with a single complex fault
source.

In this example, we first compute hazard curves for all IMTs and sites of
interest (see below). From each curve set we interpolate hazard maps at 10% and
2% probabilities of exceedance. Finally, we also extract Uniform Hazard Spectra
(UHS) for the same probabilities from the PGA and SA hazard maps.

Expected runtime: ~2 minutes
Number of sites: 1452
Number of logic tree realizations: 1
GMPEs: BooreAtkinson2008
IMTs: PGV, PGA, SA(0.025), SA(0.05), SA(0.1), SA(0.2), SA(0.5), SA(1.0), SA(2.0)
Outputs: Hazard Curves, Hazard Maps, UHS
