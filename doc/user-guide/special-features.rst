.. _special-features:

Special Features of the Engine
==============================

There are a few less frequently used features of the engine that are not documented in the general user’s manual, since 
their usage is quite specific. They are documented here.

Sensitivity analysis
--------------------

Running a sensitivity analysis study means to run multiple calculations by changing a parameter and to study how the 
results change. For instance, it is interesting to study the random seed dependency when running a calculation using 
sampling of the logic tree, or it is interesting to study the impact of the truncation level on the PoEs. The engine 
offers a special syntax to run a sensitivity analysis with respect to one (or even more than one) parameter; you can 
find examples in the demos, see for instance the MultiPointClassicalPSHA demo or the EventBasedDamage demo. It is enough 
to write in the job.ini a dictionary of lists like the following::

	sensitivity_analysis = {"random_seed": [100, 200, 300]}
	sensitivity_analysis = {'truncation_level': [2, 3]}

The first example with run 3 calculations, the second 2 calculations. The calculations will be sequential unless you 
specify the ``--many`` flag in ``oq engine --run --many job.ini``. The descriptions of the spawned calculation will be 
extended to include the parameter, so you could have descriptions as follows::

	Multipoint demo {'truncation_level': 2}
	Multipoint demo {'truncation_level': 3}

NB: from version 3.17 the engine is also able to run sensitivity analysis on file parameters. For instance if you want 
to run a ``classical_risk`` calculation starting from three different hazard inputs you can write::

	sensitivity_analysis = {
	  "hazard_curves_file": ["hazard1.csv", "hazard2.csv", "hazard3.csv"]}

The ``custom_site_id``
----------------------

Since engine v3.13, it is possible to assign 6-character ASCII strings as unique identifiers for the sites (8-characters 
since engine v3.15). This can be convenient in various situations, especially when splitting a calculation in geographic 
regions. The way to enable it is to add a field called ``custom_site_id`` to the site model file, which must be unique 
for each site.

The hazard curve and ground motion field exporters have been modified to export the ``custom_site_id`` instead of the 
``site_id`` (if present).

We used this feature to split the ESHM20 model in two parts (Northern Europe and Southern Europe). Then creating the 
full hazard map was as trivial as joining the generated CSV files. Without the ``custom_site_id`` the site IDs would 
overlap, thus making impossible to join the outputs.

A geohash string (see https://en.wikipedia.org/wiki/Geohash) makes a good ``custom_site_id`` since it can enable the 
unique identification of all potential sites across the globe.

The ``minimum_distance`` parameter
----------------------------------

GMPEs often have a prescribed range of validity. In particular they may give unexpected results for points too close to 
ruptures. To avoid this problem the engine recognizes a ``minimum_distance`` parameter: if it is set, then for distances 
below the specified minimum distance, the GMPEs return the ground-motion value at the minimum distance. This avoids 
producing extremely large (and physically unrealistic) ground-motion values at small distances. The minimum distance is 
somewhat heuristic. It may be useful to experiment with different values of the ``minimum_distance``, to see how the 
hazard and risk change.

.. _equivalent-distance-approximation:

Equivalent Epicenter Distance Approximation
-------------------------------------------

The equivalent epicenter distance approximation (``reqv`` for short) was introduced in engine 3.2 to enable the comparison 
of the OpenQuake engine with time-honored Fortran codes using the same approximation.

You can enable it in the engine by adding a ``[reqv]`` section to the job.ini, like in our example in 
openquake/qa_tests_data/logictree/case_02/job.ini::

	reqv_hdf5 = {'active shallow crust': 'lookup_asc.hdf5',
	             'stable shallow crust': 'lookup_sta.hdf5'}

For each tectonic region type to which the approximation should be applied, the user must provide a lookup table in 
.hdf5 format containing arrays ``mags`` of shape M, ``repi`` of shape N and ``reqv`` of shape (M, N).

The examples in openquake/qa_tests_data/classical/case_2 will give you the exact format required. M is the number of 
magnitudes (in the examples there are 26 magnitudes ranging from 6.05 to 8.55) and N is the number of epicenter distances 
(in the examples ranging from 1 km to 1000 km).

Depending on the tectonic region type and rupture magnitude, the engine converts the epicentral distance ``repi`` into an 
equivalent distance by looking at the lookup table and use it to determine the ``rjb`` and ``rrup`` distances, instead of 
the regular routines. This means that within this approximation ruptures are treated as pointwise and not rectangular as 
the engine usually does.

Notice that the equivalent epicenter distance approximation only applies to ruptures coming from 
PointSources/AreaSources/MultiPointSources, fault sources are untouched.

Ruptures in CSV format
----------------------

Since engine v3.10 there is a way to serialize ruptures in CSV format. The command to give is::

	$ oq extract "ruptures?min_mag=<mag>" <calc_id>`

For instance, assuming there is an event based calculation with ID 42, we can extract the ruptures in the datastore with 
magnitude larger than 6 with ``oq extract "ruptures?min_mag=6" 42``: this will generate a CSV file. Then it is possible 
to run scenario calculations starting from that rupture by simply setting ``rupture_model_file = ruptures-min_mag=6_42.csv``
in the ``job.ini`` file. The format is provisional and may change in the future, but it will stay a CSV with JSON fields. 
Here is an example for a planar rupture, i.e. a rupture generated by a point source::

	#,,,,,,,,,,"trts=['Active Shallow Crust']"
	seed,mag,rake,lon,lat,dep,multiplicity,trt,kind,mesh,extra
	24,5.050000E+00,0.000000E+00,0.08456,0.15503,5.000000E+00,1,Active Shallow Crust,ParametricProbabilisticRupture PlanarSurface,"[[[[0.08456, 0.08456, 0.08456, 0.08456]], [[0.13861, 0.17145, 0.13861, 0.17145]], [[3.17413, 3.17413, 6.82587, 6.82587]]]]","{""occurrence_rate"": 4e-05}"

The format is meant to support all kind of ruptures, including ruptures generated by simple and complex fault sources, 
characteristic sources, nonparametric sources and new kind of sources that could be introduced in the engine in the 
future. The header will be the same for all kind of ruptures that will be stored in the same CSV. Here is description of 
the fields as they are named now (engine v3.11):

**seed**
  the random seed used to compute the GMFs generated by the rupture

**mag**
  the magnitude of the rupture

**rake**
  the rake angle of the rupture surface in degrees

**lon**
  the longitude of the hypocenter in degrees

**lat**
  the latitude of the hypocenter in degrees

**dep**
  the depth of the hypocenter in km

**multiplicity**
  the number of occurrences of the rupture (i.e. number of events)

**trt**
  the tectonic region type of the rupture; must be consistent with the trts listed in the pre-header of the file

**kind**
  a space-separated string listing the rupture class and the surface class used in the engine

**mesh**
  3 times nested list with lon, lat, dep of the points of the discretized rupture geometry for each underlying surface

**extra**
  extra parameters of the rupture as a JSON dictionary, for instance the rupture occurrence rate

Notice that using a CSV file generated with an old version of the engine is inherently risky: for instance if we changed 
the ``ParametricProbabilisticRupture`` class or the ``PlanarSurface`` classes in an incompatible way with the past, then 
a scenario calculation starting with the CSV would give different results in the new version of the engine. We never 
changed the rupture classes or the surface classes, but we changed the seed algorithm often, and that too would cause 
different numbers to be generated (hopefully, statistically consistent). A bug fix or change of logic in the calculator 
can also change the numbers across engine versions.

``max_sites_disagg``
--------------------

There is a parameter in the *job.ini* called ``max_sites_disagg``, with a default value of 10. This parameter controls 
the maximum number of sites on which it is possible to run a disaggregation. If you need to run a disaggregation on a 
large number of sites you will have to increase that parameter. Notice that there are technical limits: trying to 
disaggregate 100 sites will likely succeed, trying to disaggregate 100,000 sites will most likely cause your system to 
go out of memory or out of disk space, and the calculation will be terribly slow. If you have a really large number of 
sites to disaggregate, you will have to split the calculation and it will be challenging to complete all the 
subcalculations.

The parameter ``max_sites_disagg`` is extremely important not only for disaggregation, but also for classical 
calculations. Depending on its value and then number of sites (``N``) your calculation can be in the few sites regime 
or the many sites regime.

In the few sites regime (``N <= max_sites_disagg``) the engine stores information for each rupture in the model (in 
particular the distances for each site) and therefore uses more disk space. The problem is mitigated since the engine 
uses a relatively aggressive strategy to collapse ruptures, but that requires more RAM available.

In the many sites regime (``N > max_sites_disagg``) the engine does not store rupture information (otherwise it would 
immediately run out of disk space, since typical hazard models have tens of millions of ruptures) and uses a much less 
aggressive strategy to collapse ruptures, which has the advantage of requiring less RAM.