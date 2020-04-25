MultiPointSource demo

This calculation demo exercises the Classical hazard calculator with a
single site, a single MultiPointSource and four GMPEs. We compute
the mean hazard curve and the hazard spectrum.

The MultiPointSource contains 1105 point sources with 29 different magnitudes,
each one with 2 nodal planes and 4 hypocenters, for a total of 256,360 ruptures.
Within the integration distance of 300 km only 161,472 ruptures are
contributing, corresponding to 696 point sources out of the original 1105,
which is still quite a lot. This is why the demo uses the
`pointsource_distance` approximation, meaning that planar ruptures
far away from the site are considered pointlike: the nodal plane
distribution is ignored, the mean hypocenter is considered and area of
the rupture is considere to be zero.

Users can define their own magnitude-dependent pointsource_distance
approximation, or can leave the decision to the engine. Here we demonstrate
the automagic pointsource_distance feature, enabled by the line

pointsource_distance = *

If you run the demo the following line will be logged:

Using pointsource_distance=
{'Tectonic_Type_C': [(4.55, 3),
                     (4.65, 4),
                     (4.75, 4),
                     (4.85, 5),
                     (4.95, 5),
                     (5.05, 5),
                     (5.15, 5),
                     (5.25, 5),
                     (5.35, 6),
                     (5.45, 8),
                     (5.55, 10),
                     (5.65, 11),
                     (5.75, 13),
                     (5.85, 16),
                     (5.95, 17),
                     (6.05, 20),
                     (6.15, 23),
                     (6.25, 27),
                     (6.35, 34),
                     (6.45, 42),
                     (6.55, 53),
                     (6.65, 67),
                     (6.75, 86),
                     (6.85, 104),
                     (6.95, 126),
                     (7.05, 154),
                     (7.15, 190),
                     (7.25, 237),
                     (7.35, 300)]}
The engine computes the `pointsource_distance` at each relevant magnitude
automatically, based on the GSIMs and the site conditions.

For instance for magnitude 7.25 the effective `pointsource_distance` goes
down to 237 km, while at the minimum magnitude of 4.55 it goes down
to only 3 km: it means that a huge number of ruptures will be considered
pointlike. At this moment the engine
starts collapsing the pointlike ruptures which are in the same
magnitude-distance bin and that reduces the number of effective
ruptures further. The log will print this information:

Effective number of ruptures: 33_818/150_336

There are over 4 times less ruptures thanks to the collapsing, which
means a large speedup.

A surprising feature to the non-initiated is that the collapsing
depends on the number of spawned tasks: the less tasks, the more
collapsing.

Expected runtime: < 15 seconds
Number of sites: 1
Number of source model logic tree realizations: 1
GMPEs: ChiouYoungs2014, AkkarEtAlRjb2014, AtkinsonBoore2006Modified2011, PezeshkEtAl2011NEHRPBC
IMTs: SA(2.0)
Outputs: Hazard Curves
