Common mistakes: bad configuration parameters
========================================================

By far, the most common source of problems with the engine is the
choice of parameters in the `job.ini` file. It is very easy to make
mistakes, because users typically copy the parameters from the
OpenQuake demos. However, the demos are meant to show off all of the
features of the engine in simple calculations, they are not meant
for getting performance in large calculations.

The quadratic parameters
----------------------------

In large calculations, it is essential to tune a few parameters that
are really important. Here is a list of parameters relevant for all
calculators:

maximum_distance:
   The larger the maximum_distance, the more sources and ruptures will be 
   considered; the effect is quadratic, i.e. a calculation with
   ``maximum_distance=500`` km could take up to 6.25 times more time than a
   calculation with ``maximum_distance=200`` km.

region_grid_spacing:
  The hazard sites can be specified by giving a region and a grid step.
  Clearly the size of the computation is quadratic with the inverse grid
  step: a calculation with ``region_grid_spacing=1`` will be up to 100 times
  slower than a computation with ``region_grid_spacing=10``.

area_source_discretization:
  Area sources are converted into point sources,
  by splitting the area region into a grid of points. The
  ``area_source_discretization`` (in km) is the step of the grid.
  The computation time is inversely proportional to the square of the
  discretization step, i.e. calculation with ``area_source_discretization=5``
  will take up to four times more time than a calculation with
  ``area_source_discretization=10``.

rupture_mesh_spacing:
  Fault sources are computed by converting the geometry of the fault into
  a mesh of points; the ``rupture_mesh_spacing`` is the parameter determining
  the size of the mesh. The computation time is quadratic with
  the inverse mesh spacing. Using a ``rupture_mesh_spacing=2`` instead of
  ``rupture_mesh_spacing=5`` will make your calculation up to 6.25 times slower.
  Be warned that the engine may complain if the ``rupture_mesh_spacing`` is
  too large.

complex_fault_mesh_spacing:
  The same as the ``rupture_mesh_spacing``, but for complex fault sources.
  If not specified, the value of ``rupture_mesh_spacing`` will be used.
  This is a common cause of problems; if you have performance issue you
  should consider using a larger ``complex_fault_mesh_spacing``. For instance, 
  if you use a ``rupture_mesh_spacing=2`` for simple fault sources but
  ``complex_fault_mesh_spacing=10`` for complex fault sources, your computation
  can become up to 25 times faster, assuming the complex fault sources
  are dominating the computation time.

Intensity measure types and levels
----------------------------------

Classical calculations are roughly linear in the number of intensity
measure types and levels. A common mistake is to use too many levels.
For instance a configuration like the following one::

  intensity_measure_types_and_levels = {"PGA":  logscale(0.001,4.0, 100),
                                        "SA(0.3)":  logscale(0.001,4.0, 100),
                                        "SA(1.0)":  logscale(0.001,4.0, 100)}

requires computing the PoEs on 300 levels. Is that really what the user wants?
Since calculations are usually dominated by epistemic errors, it could very
well be that within the systematic error using only 20 levels per each intensity
measure type produces good enough results, while reducing the computation
time by a factor of 5, at least in theory.

pointsource_distance
----------------------------

PointSources (and MultiPointSources and AreaSources,
which are split into PointSources and therefore are effectively
the same thing) have an hypocenter distribution and
a nodal plane distribution, which are used to model the uncertainties on
the hypocenter location and ont the orientation of the underlying ruptures.
Since PointSources produce rectangular surfaces, thery are really
not pointwise for the engine, and are actually complicated things.
Is the effect of the hypocenter/nodal planes distributions relevant?
It depends on the calculation, but if you are interested in points that
are far from the rupture the effect is minimal. So if you have a nodal
plane distribution with 20 planes and a hypocenter distribution with 5
hypocenters, the engine will consider 20 x 5 ruptures and perform 100
times more calculations than needed, since at large distance the hazard
will be more or less the same for each rupture.

To avoid this performance problem it is a good practice to set the
`pointsource_distance` parameter. For instance, setting

`pointsource_distance = 50`

means: for the points that are distant more than 50 km from the ruptures
ignore the hypocenter and nodal plane distributions and consider only the
first rupture in the distribution. This will give you a substantial speedup
if your model is dominated by PointSources and there are several
nodal planes/hypocenters in the distribution. In same situation it also
makes sense to set

`pointsource_distance = 0`

to completely remove the nodal plane/hypocenter distributions. For instance
the Indonesia model has 20 nodal planes for each point sources; however such
model uses the so-called `equivalent distance approximation`_ which considers
the point sources to be really pointwise. In this case the contribution to
the hazard is totally independent from the nodal plane and by using

`pointsource_distance = 0`

one can get *exactly* the same numbers and run the model in 1 hour instead
of 20. Actually, starting from engine 3.3 the engine is smart enough to
recognize the cases where the equivalent distance approximation is used and
automatically set `pointsource_distance = 0`.

Even if you not using the equivalent distance approximation, the effect
of the nodal plane/hypocenter distribution: I have seen case when setting
setting `pointsource_distance = 0` changed the result only by 0.1% and
gained an order of magnitude of speedup. You have to check on a case by case
basis.


concurrent_tasks parameter
---------------------------

There is a last parameter which is worthy of mention, because of its
effect on the memory occupation in the risk calculators and in the
event based hazard calculator.

concurrent_tasks:
   This is a parameter that you should not set, since in most cases the
   engine will figure out the correct value to use. However,
   in some cases, you may be forced to set it. Typically this happens in
   event based calculations, when computing the ground motion fields.
   If you run out of memory, increasing this parameter will help, since
   you will produce smaller tasks. Another case when it may help is when
   computing hazard statistics with lots of sites and realizations, since
   by increasing this parameter the tasks will contain less sites.

.. _equivalent distance approximation: equivalent_distance_approximation.rst
