The point source gridding approximation
=================================================

WARNING: *the point source gridding approximation is used only in classical
calculations, not in event based calculations*

Most hazard calculations are dominated by distributed seismicity, i.e.
area sources and multipoint sources that for the engine are just
regular point sources. In such situations the parameter governing the
performance is the grid spacing: a calculation with a grid spacing of
50 km produces 25 times less ruptures and it is expected to be 25
times faster than a calculation with a grid spacing of 10 km.

The *point source gridding approximation* is a smart way
of raising the grid spacing without losing too much precision and
without losing too much performance.

The idea is two use two kind of point sources: the original ones and a
set of "effective" ones (instances of the class
``CollapsedPointSource``) that essentially are the original sources averaged
on a larger grid, determined by the parameter ``ps_grid_spacing``.

The plot below should give the idea:

.. image:: gridding.png

For distant points it is possible to use the large
grid (i.e. the CollapsePointSources) without losing precision,
while for close points the original sources should be used.

The engine uses the parameter ``pointsource_distance``
to determine when to use the original sources and when to use the
collapsed sources.

If the ``maximum_distance`` has a value of 500 km and the
``pointsource_distance`` a value of 50 km, then (50/500)^2 = 1%
of the sites will be close and 99% of the sites will be far.
Therefore you will able to use the gridding approximation for
99% percent of the sites and a huge speedup is to big expected.
