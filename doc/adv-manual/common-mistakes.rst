Common mistakes: bad configuration
=========================================

By far, the most common source of problems with the engine is the choice
of parameters in the `job.ini` file. There are a few parameters that are really
important when it comes to the performance of a computation. Here is an
(incomplete) list of them.

region_grid_spacing:
  The hazard sites can be specifying by giving a region and a grid step.
  Clearly the size of the computation is *quadratic with the inverse grid
  step*: a calculation with `region_grid_spacing=1` will be 100 times slower
  than a computation with `region_grid_spacing=10`.

area_source_discretization:
  Area sources are converted into point sources,
  by splitting the area region into a grid of points. The
  `area_source_discretization` (in km) is the step of the grid.
  The computation time is inversely *proportional to the square of the
  discretization step*:
  i.e. calculation with `area_source_discretization=5` will take
  (approximately) *four times*
  more time than a calculation with `area_source_discretization=5`.

rupture_mesh_spacing:
   Fault sources are computed by converting the geometry of the fault into
   a mesh of points; the `rupture_mesh_spacing` is the parameter determining
   the size of the mesh. Again, the computation time is *quadratic* with
   the inverse mesh spacing. Using a `rupture_mesh_spacing=2` instead of
   `rupture_mesh_spacing=5` will make your calculation (approximately)
   6.25 times slower.

complex_fault_mesh_spacing:
   The same as the `rupture_mesh_spacing`, but for complex fault sources.
   If not specified, the value of `rupture_mesh_spacing` will be used.
   This is a common cause of problems; if you have performance issue you
   should consider using a larger `complex_fault_mesh_spacing`. For instance, 
   if you use a `rupture_mesh_spacing=2` for simple fault sources but
   `complex_fault_mesh_spacing=10` for complex fault sources, your computation
   can become upt *25 times faster*, assuming the complex fault sources
   are dominating the computation time.

ground_motion_correlation_model:
   Event based/scenario calculations with a ground motion correlation model
   are severely limited with the size of the correlation matrix. If you have
   thousands of hazard sites it will likely be impossible to run the
   calculation, because you will run out of memory. Just reduce the number
   of sites or remove the correlation model. If you remove the correlation,
   the calculation of the GMFs will become *orders of magnitude faster*.
