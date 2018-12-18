Tips for running large hazard calculations
==========================================

Running large hazard calculations, especially ones with large logic
trees, is an art, and there are various techniques that can be used to
reduce an impossible calculation to a feasible one.

The first thing to do
----------------------

The first thing to do when you have a large calculation is to reduce it
so that it can run in a reasonable amount of time. The simplest way to do
that is to reduce the number of sites, for instance by considering a small
geographics portion of the region interested, of by increasing the grid
spacing. Once the calculation has been reduced, you can run
it and determine what are the factors dominating the run time.

As we discussed in section `common mistakes`_, you may want to tweak
the quadratic parameters (``maximum_distance``,
``area_source_discretization``, ``rupture_mesh_spacing``,
``complex_fault_mesh_spacing``). Also, you may want to choose different
GMPEs, since some are faster than others. You may want to play with
the logic tree, to reduce the number of realizations: this is
especially important, in particular for event based calculation were
the number of generated ground motion fields is linear with the number
of realizations.

Once you have tuned the reduced computation, you can have an idea of the time
required for the full calculation. It will be less than linear with the number
of sites, so if you reduced your sites by a factor by a number of 100, the
full computation will take a lot less than 100 times the time of the reduced
calculation (fortunately). Still, the full calculation can be impossible because
of the memory/data transfer requirements, especially in the case of event based
calculations. Sometimes it is necessary to reduce your expectations. The
example below will discuss a concrete case.

Case study: GMFs for California
-----------------------------------------

We had an user asking for the GMFs of California on 707,920 hazard sites,
using the UCERF mean model and an investigation time of 100,000 years.
Is this feasible or not? Some back of the envelope calculations
suggests that it is unfeasible, but reality can be different.

The relevant parameters are the following::

 N = 707,920 hazard sites
 E = 10^5 estimated events of magnitude greather then 5.5 in the investigation
     time of 100,000 years
 B = 1 number of branches in the UCERF logic tree
 G = 5 number of GSIMS in the GMPE logic tree
 I = 6 number of intensity measure types
 S1 = 13 number of bytes used by the engine to store a single GMV

The maximum size of generated GMFs is

``N * E * B * G * I * S1 = 25 TB (terabytes)``

Storing and sharing 25 TB of data is a big issue, so the problem seems
without solution. However, most of the ground motion values are zero,
because there is a maximum distance of 300 km and a rupture cannot
affect all of the sites. So the size of the GMFs should be less than
25 TB. Moreover, if you want to use such GMFs for a damage analysis,
you may want to discard very small shaking that will not cause any
damage to your buildings. The engine has a parameter to discard all
GMFs below a minimum threshould, the `minimum_intensity` parameter. The
higher the threshold, the smaller the size of the GMFs. By playing
with that parameter you can reduce the size of the output by orders of
magnitudes. Terabytes could easily become gigabytes with a well chosen
threshold.

In practice, we were able to run the full 707,920 sites by
splitting the sites in 70 tiles and by using a minimum intensity of 0.1 g. This
was the limit configuration for our cluster which has 5 machines with
128 GB of RAM each. 

The full calculation was completed in only 4 hours because our calculators
are highly optimized. The total size of the generated .hdf5 files was
of 400 GB. This is a lot less than 25 TB, but still too large for sharing
purposes.

Another way to reduce the output is to reduce the number of intensity
measure types. Currently in your calculations there are 6 of them
(PGA, SA(0.1), SA(0.2), SA(0.5), SA(1.0), SA(2.0)) but if you restrict
yourself to only PGA the computation and the output will become 6
times smaller. Also, there are 5 GMPEs: if you restrict yourself to 1 GMPE
you gain a factor of 5. Similarly, you can reduce the investigation period
from 100,000 year to 10,000 years, thus gaining another order of magnitude.
Also, raising the minimum magnitude reduces the number of events significantly.

But the best approach is to be smart. For instance, we know from experience
that if the final goal is to estimate the total loss for a given exposure, the
right way to do that is to aggregate the exposure on a smaller number of
hazard sites. For instance, instead of the original 707,920 hazard sites
we could aggregate on only ~7,000 hazard sites and we would a calculation
which is 100 times faster, produces 100 times less GMFs and still produces
a good estimate for the total loss.

In short, risk calculations for the mean field UCERF model are routines
now, in spite of what the naive expectations could be.

Disaggregation
----------------------------------------

Disaggregation calculations can be quite large and are rather
difficult to reduce, because they usually involve a single site, so
there is nothing to reduce there. What can be reduced are the
quadratic parameters.


.. _common mistakes: common-mistakes.rst
