MultiPointSource demo

This calculation demo exercises the Classical hazard calculator with a
single site, a single MultiPointSource and four GMPEs. We compute
the mean hazard curve and the hazard spectrum.

The MultiPointSource contains 1105 point sources with 29 different magnitudes,
each one with 2 nodal planes and 4 hypocenters, for a total of 256,360 ruptures.
Within the integration distance of 300 km only 161,472 ruptures are
contributing, corresponding to 696 point sources out of the original 1105,
which is still quite a lot. This is why the demo
uses a `pointsource_distance` of 100 km, meaning that the ruptures
at maximum magnitude distance more 100 km from the site are considered
pointlike, i.e. the nodal plane distribution is ignored and only the mean
hypocenter is considered.

For magnitudes smaller than the maximum magnitude (the demos contains
magnitudes from 7.35 down to 4.55) the effective `pointsource_distance`
is clearly lower than the maximum `pointsource_distance`; the engine
computes it automatically based on the GSIMs and the site conditions.

For instance for magnitude 7.25 the effective `pointsource_distance` goes
down to 70 km, while at the minimum magnitude of 4.55 it goes down
to only 17 km: it means that a huge number of ruptures will be considered
pointlike. In particular an analysis show that for magnitude 7.35 only 45 point
sources (out of 696) will be considered finite-size, for magnitude
7.25 only 5, and for all the other magnitudes the finite-size effects
will be completely neglected, thus resulting in a strong reduction of
the number of ruptures.

That reduces the number of effective ruptures to 20,534 (20,134
pointlike ruptures + 400 finite size ruptures, being 20,134 * 8 + 400
= 161,472 the original number of ruptures).  The computation time goes
down from 570s to 60s on a regular laptop.  At this moment the engine
starts collapsing the pointlike ruptures which are in the same
magnitude-distance bin and that reduces the number of effective
ruptures to 690 (400 finite size ruptures + 290 collapsed pointlike
ruptures). As a result, the computation time goes down from 60s to 8s
on the same laptop.

Expected runtime: < 20 seconds
Number of sites: 1
Number of source model logic tree realizations: 1
GMPEs: ChiouYoungs2014, AkkarEtAlRjb2014, AtkinsonBoore2006Modified2011, PezeshkEtAl2011NEHRPBC
IMTs: SA(2.0)
Outputs: Hazard Curves
