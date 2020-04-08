Site-specific classical calculations
==========================================

Starting from version 3.9, the engine offers some optimizations for
site specific classical calculations.

The pointsource_distance approximation
--------------------------------------

If you have multiple sites and you have set the `pointsource_distance`
parameter in the job.ini, then the nodal plane distributions and hypocenter
distributions will be collapsed for far away ruptures, as we discussed
in the section about `common mistakes`_. If you have a single site,
*an additional collapsing* will be applied, that will further reduce
the effective number of ruptures, even in the case of trivial
nodal plane distributions and hypocenter distributions.
This additional collapsing takes the ruptures that are more distant
than the `pointsource_distance` from the site of interest, groups
them by magnitude and distance, and take only one representative per
bin. The number of distance bins is determined by the parameter
`point_rupture_bins`, which has a default of 20, and which can be
tuned in the `job.ini` file. This reduces greatly the number of ruptures
at the cost of a minor loss in precision.
There is a detailed discussion of the mechanism in the
MultiPointClassicalPSHA demo. Here we will just show a plot displaying the
hazard curve without `pointsource_distance` (with ID=-2) and with
`pointsource_distance=200` km (with ID=-1). As you see they are nearly
identical but the second calculation is ten times faster on my laptop.

.. image:: mp-demo.png

.. _common mistakes: common-mistakes.rst
