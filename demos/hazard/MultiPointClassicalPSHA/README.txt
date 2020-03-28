MultiPointSource demo

This calculation demo exercises the Classical hazard calculator with a
single site, a single MultiPointSource and four GMPEs. We compute
the mean hazard curve and the hazard spectrum. The MultiPointSource
contains 1105 point sources with 29 different magnitudes, each one with
2 nodal planes and 4 hypocenters, for a total of 256,360 ruptures.
Within the integration distance of 300 km only 161,472 ruptures are
contributing, which is still quite a lot. This is why the demo
uses a pointsource_distance of 100 km, meaning that all ruptures
over 100 km from the site are considered really pointlike, i.e.
the nodal plane distribution is ignored and only the mean hypocenter
is considered. That reduces the number of effective ruptures to
27,898 (19,082 pointlike ruptures + 8,816 finite size ruptures,
being 19,082 * 8 + 8,816 = 161,472 is the original number of
ruptures). The computation time goes down from 568s to 91s on a regular laptop.
At this moment the engine starts collapsing the pointlike ruptures
which are in the same magnitude-distance bin and that reduces the number of
effective ruptures to 9,106 (8,816 finite size ruptures + 290 collapsed
pointlike ruptures). As a result, the computation time goes down
from 91s to 41s on the same laptop.

Expected runtime: < 1 minute
Number of sites: 1
Number of source model logic tree realizations: 1
GMPEs: ChiouYoungs2014, AkkarEtAlRjb2014, AtkinsonBoore2006Modified2011, PezeshkEtAl2011NEHRPBC
IMTs: PGA, SA(0.1), SA(0.2), SA(0.5), SA(1.0), SA(2.0)
Outputs: Hazard Curve, UHS
