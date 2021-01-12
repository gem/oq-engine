Classical PSHA Point Source Demo

This calculation demo exercises the Classical hazard calculator with a trivial
source model logic tree, containing a single model with a single point source.

In this example, we first compute hazard curves for all IMTs and sites of
interest (see below). From each curve set we interpolate hazard maps at 10% and
2% probabilities of exceedance. Finally, we also extract Uniform Hazard Spectra
(UHS) for the same probabilities from the PGA and SA hazard maps.

The non-trivial bit is the usage of pointsource distance approximation.
In this example there are 840 sites within the maximum_distance of 300 km,
of which 313 within the pointsource_distance of 100 km and 527 outside.
There are also 6 nodal planes and 3 hypocenter depths. The computational
weight is therefore 313 x 18 (for the close sites) + 527 x 1 (for the far
sites) to be compared to a weight of 840 x 18 without the approximation:
a gain of 6161 vs 15120, i.e. more than twice.

Expected runtime: ~10 seconds
Number of sites: 1936
Number of logic tree realizations: 1
GMPEs: BooreAtkinson2008
IMTs: PGV, PGA, SA(0.025), SA(0.05), SA(0.1), SA(0.2), SA(0.5), SA(1.0), SA(2.0)
Outputs: Hazard Curves, Hazard Maps, UHS
