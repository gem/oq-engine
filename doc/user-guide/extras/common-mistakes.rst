Bad configuration parameters
============================

By far, the most common source of problems with the engine is the choice of parameters in the *job.ini* file. It is very 
easy to make mistakes, because users typically copy the parameters from the OpenQuake engine demos. However, the demos are meant 
to show off all of the features of the engine in simple calculations, they are not meant for getting performance in large 
calculations.

The quadratic parameters
------------------------

In large calculations, it is essential to tune a few parameters that are really important. Here is a list of parameters 
relevant for all calculators:

**maximum_distance:**
   The larger the maximum_distance, the more sources and ruptures will be considered; the effect is quadratic, i.e. 
   a calculation with ``maximum_distance=500`` km could take up to 6.25 times more time than a calculation with 
   ``maximum_distance=200`` km.

**region_grid_spacing:**
   The hazard sites can be specified by giving a region and a grid step. Clearly the size of the computation is quadratic 
   with the inverse grid step: a calculation with ``region_grid_spacing=1`` will be up to 100 times slower than a 
   computation with ``region_grid_spacing=10``.

**area_source_discretization:**
   Area sources are converted into point sources, by splitting the area region into a grid of points. The 
   ``area_source_discretization`` (in km) is the step of the grid. The computation time is inversely proportional to the 
   square of the discretization step, i.e. calculation with ``area_source_discretization=5`` will take up to four times 
   more time than a calculation with ``area_source_discretization=10``.

**rupture_mesh_spacing:**
   Fault sources are computed by converting the geometry of the fault into a mesh of points; the ``rupture_mesh_spacing`` 
   is the parameter determining the size of the mesh. The computation time is quadratic with the inverse mesh spacing. 
   Using a ``rupture_mesh_spacing=2`` instead of ``rupture_mesh_spacing=5`` will make your calculation up to 6.25 times 
   slower. Be warned that the engine may complain if the ``rupture_mesh_spacing`` is too large.

**complex_fault_mesh_spacing:**
   The same as the ``rupture_mesh_spacing``, but for complex fault sources. If not specified, the value of 
   ``rupture_mesh_spacing`` will be used. This is a common cause of problems; if you have performance issue you should 
   consider using a larger ``complex_fault_mesh_spacing``. For instance, if you use a ``rupture_mesh_spacing=2`` for 
   simple fault sources but ``complex_fault_mesh_spacing=10`` for complex fault sources, your computation can become up 
   to 25 times faster, assuming the complex fault sources are dominating the computation time.

Maximum distance
----------------

The engine gives users a lot of control on the maximum distance parameter. For instance, you can have a different 
maximum distance depending on the tectonic region, like in the following example::

	maximum_distance = {'Active Shallow Crust': 200, 'Subduction': 500}

You can also have a magnitude-dependent maximum distance::

	maximum_distance = [(5, 0), (6, 100), (7, 200), (8, 300)]

In this case, given a site, the engine will completely discard ruptures with magnitude below 5, keep ruptures up to 100 
km for magnitudes between 5 and 6 (the maximum distance in this magnitude range will vary linearly between 0 and 100), 
keep ruptures up to 200 km for magnitudes between 6 and 7 (with *maximum_distance* increasing linearly from 100 to 200 km 
from magnitude 6 to magnitude 7), keep ruptures up to 300 km for magnitudes between 7 and 8 (with *maximum_distance* 
increasing linearly from 200 to 300 km from magnitude 7 to magnitude 8) and discard ruptures for magnitudes over 8.

You can have both trt-dependent and mag-dependent maximum distance::

	maximum_distance = {
	   'Active Shallow Crust': [(5, 0), (6, 100), (7, 200), (8, 300)],
	   'Subduction': [(6.5, 300), (9, 500)]}

Given a rupture with tectonic region type ``trt`` and magnitude ``mag``, the engine will ignore all sites over the 
maximum distance ``md(trt, mag)``. The precise value is given via linear interpolation of the values listed in the 
job.ini; you can determine the distance as follows::

	from openquake.hazardlib.calc.filters import IntegrationDistance
	idist = IntegrationDistance.new('[(4, 0), (6, 100), (7, 200), (8.5, 300)]')
	interp = idist('TRT')
	interp([4.5, 5.5, 6.5, 7.5, 8])
	array([ 25.        ,  75.        , 150.        , 233.33333333,
	       266.66666667])

pointsource_distance
--------------------

PointSources (and MultiPointSources and AreaSources, which are split into PointSources and therefore are effectively the 
same thing) are not pointwise for the engine: they actually generate ruptures with rectangular surfaces which size is 
determined by the magnitude scaling relationship. The geometry and position of such rectangles depends on the hypocenter 
distribution and the nodal plane distribution of the point source, which are used to model the uncertainties on the 
hypocenter location and on the orientation of the underlying ruptures.

Is the effect of the hypocenter/nodal planes distributions relevant? Not always: in particular, if you are interested in 
points that are far away from the rupture the effect is minimal. So if you have a nodal plane distribution with 20 planes 
and a hypocenter distribution with 5 hypocenters, the engine will consider 20 x 5 ruptures and perform 100 times more 
calculations than needed, since at large distance the hazard will be more or less the same for each rupture.

To avoid this performance problem there is a ``pointsource_distance`` parameter: you can set it in the ``job.ini`` as a 
dictionary (tectonic region type -> distance in km) or as a scalar (in that case it is converted into a dictionary 
``{"default": distance}`` and the same distance is used for all TRTs). For sites that are more distant than the 
*pointsource_distance* plus the rupture radius from the point source, the engine creates an average rupture by taking 
weighted means of the parameters *strike, dip, rake* and *depth* from the nodal plane and hypocenter distributions and 
by rescaling the occurrence rate. For closer points, all the original ruptures are considered. This approximation (we 
call it *rupture collapsing* because it essentially reduces the number of ruptures) can give a substantial speedup if the 
model is dominated by PointSources and there are several nodal planes/hypocenters in the distribution. In some situations 
it also makes sense to set ``pointsource_distance = 0`` to completely remove the nodal plane/hypocenter distributions. For 
instance the Indonesia model has 20 nodal planes for each point sources; however such model uses the so-called 
:ref:`equivalent distance approximation <equivalent-distance-approximation>`
which considers the point sources to be really pointwise. In this case the contribution to the hazard is totally 
independent from the nodal plane and by using ``pointsource_distance = 0`` one can get *exactly* the same numbers and run 
the model in 1 hour instead of 20 hours. Actually, starting from engine 3.3 the engine is smart enough to recognize the 
cases where the equivalent distance approximation is used and automatically set ``pointsource_distance = 0``.

Even if you not using the equivalent distance approximation, the effect of the nodal plane/hypocenter distribution can 
be negligible: I have seen cases when setting ``pointsource_distance = 0`` changed the result in the hazard maps only by 
0.1% and gained an order of magnitude of speedup. You have to check on a case by case basis.

There is a good example of use of the ``pointsource_distance`` in the MultiPointClassicalPSHA demo. Here we will just 
show a plot displaying the hazard curve without *pointsource_distance* (with ID=-2) and with *pointsource_distance=200* km 
(with ID=-1). As you see they are nearly identical but the second calculation is ten times faster.

.. image:: _images/mp-demo.png

The ``pointsource_distance`` is also crucial when using the :ref:`point source gridding <point-source-gridding>`
approximation: then it can be used to speedup calculations even when the nodal plane and hypocenter distributions are 
trivial and no speedup would be expected.

NB: the ``pointsource_distance`` approximation has changed a lot across engine releases and you should not expect it to 
give always the same results. In particular, in engine 3.8 it has been extended to take into account the fact that small 
magnitudes will have a smaller collapse distance. For instance, if you set ``pointsource_distance=100``, the engine will 
collapse the ruptures over 100 km for the maximum magnitude, but for lower magnitudes the engine will consider a (much) 
shorter collapse distance and will collapse a lot more ruptures. This is possible because given a tectonic region type 
the engine knows all the GMPEs associated to that tectonic region and can compute an upper limit for the maximum 
intensity generated by a rupture at any distance. Then it can invert the curve and given the magnitude and the maximum 
intensity can determine the collapse distance for that magnitude.

In engine 3.11, contrarily to all previous releases, finite side effects are not ignored for distance sites, they are 
simply averaged over. This gives a better precision. In some case (i.e. the Alaska model) versions of the engine before 
3.11 could give a completely wrong hazard on some sites. This is now fixed.

Note: setting ``pointsource_distance=0`` does not completely remove finite size effects. If you want to replace point 
sources with points you need to also change the magnitude-scaling relationship to ``PointMSR``. Then the area of the 
underlying planar ruptures will be set to 1E-4 squared km and the ruptures will effectively become points.

The linear parameters: *width_of_mfd_bin* and intensity levels
--------------------------------------------------------------

The number of ruptures generated by the engine is controlled by the parameter *width_of_mfd_bin*; for instance if you 
raise it from 0.1 to 0.2 you will reduce by half the number of ruptures and double the speed of the calculation. It is a 
linear parameter, at least approximately. Classical calculations are also roughly linear in the number of intensity 
measure types and levels. A common mistake is to use too many levels. For instance a configuration like the following one::

	intensity_measure_types_and_levels = {
	  "PGA":  logscale(0.001,4.0, 100),
	  "SA(0.3)":  logscale(0.001,4.0, 100),
	  "SA(1.0)":  logscale(0.001,4.0, 100)}

requires computing the PoEs on 300 levels. Is that really what the user wants? It could very well be that using only 20 
levels per each intensity measure type produces good enough results, while potentially reducing the computation time by 
a factor of 5.

concurrent_tasks parameter
--------------------------

There is a last parameter which is worthy of mention, because of its effect on the memory occupation in the risk 
calculators and in the event based hazard calculator.

**concurrent_tasks:**
   This is a parameter that you should not set, since in most cases the engine will figure out the correct value to use. 
   However, in some cases, you may be forced to set it. Typically this happens in event based calculations, when computing 
   the ground motion fields. If you run out of memory, increasing this parameter will help, since the engine will produce 
   smaller tasks. Another case when it may help is when computing hazard statistics with lots of sites and realizations, 
   since by increasing this parameter the tasks will contain less sites.

Notice that if the number of ``concurrent_tasks`` is too big the performance will get worse and the data transfer will 
increase: at a certain point the calculation will run out of memory. I have seen this to happen when generating tens of 
thousands of tasks. Again, it is best not to touch this parameter unless you know what you are doing.