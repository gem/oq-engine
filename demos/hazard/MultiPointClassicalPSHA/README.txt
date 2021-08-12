MultiPointSource demo

This calculation demo exercises the Classical hazard calculator with a
single site, a single MultiPointSource and four GMPEs. We compute
the mean hazard curve and the hazard spectrum.

The MultiPointSource contains 1105 point sources with 29 different magnitudes,
each one with 2 nodal planes and 4 hypocenters, for a total of 256,360 ruptures.
Within the integration distance of 300 km only 161,472 ruptures are
contributing, corresponding to 696 point sources out of the original 1105,
which is still quite a lot. This is why the demo uses the pointsource gridding
approximation, which is collapsing point sources far away from the point.

Expected runtime: < 10 seconds
Number of sites: 1
Number of source model logic tree realizations: 1
GMPEs: ChiouYoungs2014, AkkarEtAlRjb2014, AtkinsonBoore2006Modified2011, PezeshkEtAl2011NEHRPBC
IMTs: SA(2.0)
Outputs: Hazard Curves
