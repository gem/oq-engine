Tips for running large hazard calculations
==========================================

Running large hazard calculations, especially ones with large logic
trees, is an art, and there are various techniques that can be used to
reduce an impossible calculation to a feasible one.

Reducing a calculation
-------------------------------------------

The first thing to do when you have a large calculation is to reduce it
so that it can run in a reasonable amount of time. For instance you
could reduce the number of sites, by considering a small
geographic portion of the region interested, of by increasing the grid
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
of sites, so if you reduced your sites by a factor of 100, the
full computation will take a lot less than 100 times the time of the reduced
calculation (fortunately). Still, the full calculation can be impossible because
of the memory/data transfer requirements, especially in the case of event based
calculations. Sometimes it is necessary to reduce your expectations. The
examples below will discuss a few concrete cases. But first of all, we
must stress an important point::

 Our experience tells us that THE PERFORMANCE BOTTLENECKS OF THE
 REDUCED CALCULATION ARE TOTALLY DIFFERENT FROM THE BOTTLENECKS OF
 THE FULL CALCULATION. Do not trust your performance intuition.


Classical PSHA for Europe
--------------------------------------------

Suppose you want to run a classical PSHA calculation for the latest
model for Europe and that it turns out to be too slow to run on your
infrastructure. Let's say it takes 4 days to run. How do you proceed
to reduce the computation time?

The first thing that comes to mind is to tune the
``area_source_discretization`` parameter, since the calculation (as
most calculations) is dominated by area sources. For instance, by
doubling it (say from 10 km to 20 km) we would expect to reduce the
calculation time from 4 days to just 1 day, a definite improvement.

But how do we check if the results are still acceptable? Also, how we
check that in less than 4+1=5 days? As we said before we have to reduce
the calculation and the engine provides several ways to do that.

If you want to reduce the number of sites, IMTs and realizations you can:

- manually change the ``sites.csv`` or ``site_model.csv`` files
- manually change the ``region_grid_spacing``
- manually change the ``intensity_measure_types_and_levels`` variable
- manually change the GMPE logic tree file by commenting out branches
- manually change the source logic tree file by commenting out branches
- use the environment variable ``OQ_SAMPLE_SITES``
- use the environment variable ``OQ_REDUCE``

Starting from engine 3.11 the simplest approach is to use the ``OQ_REDUCE``
environment variable than not only reduce reduces the number of sites,
but also reduces the number of intensity measure types (it takes the
first one only) and the number of realizations to just 1 (it sets
``number_of_logic_tree_samples=1``) and if you are in an event based
calculation reduces the parameter ``ses_per_logic_tree_path`` too.
For instance the command::

  $ OQ_REDUCE=.01 oq engine --run job.ini

will reduce the number of sites by 100 times by random sampling, as well
a reducing to 1 the number of IMTs and realizations. As a result the
calculation will be very fast (say 1 hour instead of 4 days) and it
will possible to re-run it multiple times with different parameters.
For instance, you can test the impact of the area source discretization
parameter by running::
  
  $ OQ_REDUCE=.01 oq engine --run job.ini --param area_source_discretization=20

Then the engine provides a command `oq compare` to compare calculations;
for instance::

  $ oq compare hmaps PGA -2 -1 --atol .01

will compare the hazard maps for PGA for the original
(ID=-2, area_source_discretization=10 km) and the new calculation
(ID=-2, area_source_discretization=20 km) on all sites, printing out
the sites where the hazard values are different more than .01 g
(``--atol`` means absolute tolerence). You can use ``oq compare --help``
to see what other options are available.

If the call to ``oq compare`` gives a result::
  
  There are no differences within the tolerances atol=0.01, rtol=0%, sids=[...]

it means that within the specified tolerance the hazard is the same
on all the sites, so you can safely use the area discretization of 20
km. Of course, the complete calculation will contain 100 times more
sites, so it could be that in the complete calculation some sites
will have different hazard. But that's life. If you want absolute
certitude you will need to run the full calculation and to wait.
Still, the reduced calculation is useful, because if you see that
are already big differences there, you can immediately assess that
doubling the ``area_source_discretization`` parameter is a no go and
you can try other strategies, like for instance doubling the
``width_of_mfd_bin`` parameter.

As of version 3.11, the ``oq compare hmaps`` command will give an output like
the following, in case of differences::

   site_id calc_id 0.5     0.1     0.05    0.02    0.01    0.005
   ======= ======= ======= ======= ======= ======= ======= =======
   767     -2      0.10593 0.28307 0.37808 0.51918 0.63259 0.76299
   767     -1      0.10390 0.27636 0.36955 0.50503 0.61676 0.74079
   ======= ======= ======= ======= ======= ======= ======= =======
   ===== =========
   poe   rms-diff
   ===== =========
   0.5   1.871E-04
   0.1   4.253E-04
   0.05  5.307E-04
   0.02  7.410E-04
   0.01  8.856E-04
   0.005 0.00106  
   ===== =========

This is an example with 6 hazard maps, for poe = .5, .1, .05, .02, .01
and .005 respectively. Here the only site that shows some discrepancy
if the site number 767. If that site is in Greenland where nobody lives
one can decide that the approximation is good anyway ;-)
The engine also report the RMS-differences by considering all the sites,
i.e.

   rms-diff = sqrt<(hmap1 - hmap2)^2>  # mediating on all the sites

As to be expected, the differences are larger for maps with a smaller poe,
i.e. a larger return period. But even in the worst case the RMS difference
is only of 1E-3 g, which is not much. The complete calculation will have
more sites, so the RMS difference will likely be even smaller.
If you can check the few outlier sites and convince yourself that
they are not important, you have succeeded in doubling the speed
on your computation. And then you can start to work on the other
quadratic and linear parameter and to get an ever bigger speedup!

GMFs for California
-----------------------------------------

We had an user asking for the GMFs of California on 707,920 hazard sites,
using the UCERF mean model and an investigation time of 100,000 years.
Is this feasible or not? Some back of the envelope calculations
suggests that it is unfeasible, but reality can be different.

The relevant parameters are the following::

 N = 707,920 hazard sites
 E = 10^5 estimated events of magnitude greater then 5.5 in the investigation
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
GMFs below a minimum threshold, the ``minimum_intensity`` parameter. The
higher the threshold, the smaller the size of the GMFs. By playing
with that parameter you can reduce the size of the output by orders of
magnitudes. Terabytes could easily become gigabytes with a well chosen
threshold.

In practice, we were able to run the full 707,920 sites by
splitting the sites in 70 tiles and by using a minimum intensity of 0.1 g. This
was the limit configuration for our cluster which has 5 machines with
128 GB of RAM each. 

The full calculation was completed in only 4 hours because our calculators
are highly optimized. The total size of the generated HDF5 files was
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
correct way to do that is to aggregate the exposure on a smaller number of
hazard sites. For instance, instead of the original 707,920 hazard sites
we could aggregate on only ~7,000 hazard sites and we would a calculation
which is 100 times faster, produces 100 times less GMFs and still produces
a good estimate for the total loss.

In short, risk calculations for the mean field UCERF model are routines
now, in spite of what the naive expectations could be.

.. _common mistakes: common-mistakes.rst
