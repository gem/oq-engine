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


event_based/scenario parameters
--------------------------------

ground_motion_correlation_model:
  Event based/scenario calculations with a ground motion correlation model
  are severely limited by the size of the correlation matrix. If you have
  thousands of hazard sites it will likely be impossible to run the
  calculation, because you will run out of memory. Just reduce the number
  of sites or remove the correlation model. If you remove the correlation,
  the calculation of the GMFs will become orders of magnitude faster.

minimum_intensity:
  Event based/scenario calculators honors a `minimum_intensity` parameter,
  i.e. ground motion fields below the minimum intensity are  
  discarded. For instance, if you add to your `job.ini` file a line
  ``minimum_intensity={'PGA': 0.05, 'SA(0.1)': 0.05}`` all ground motion
  fields below the value of 0.05 g will be discarded. This parameter has  
  a huge effect on memory consumption and data transfer: a calculation
  which is impossible without specifying it can become possible after specifying
  a carefully chosen value for it.

event_based_risk parameters
------------------------------

asset_loss_table:
   Running an event based risk calculation with asset_loss_table=true
   will use a lot of memory. Make sure this parameter is false (the default)
   unless you really need it. At the moment it is needed if you want to
   compute loss curves and maps for all assets of your exposure.

  
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
   you will produce smaller tasks.
