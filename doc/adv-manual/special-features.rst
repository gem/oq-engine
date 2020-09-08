Special features of the engine
============================================

There are few rarely used feature of the engine that are not
documented in the manual, since their usage is quite specific. They are
documented here.

GMPE logic trees with `minimum_distance`
-------------------------------------------

GMPEs have a range of validity. In particular they may give wrong
results for points too close to the rupture. To avoid this problem
some GSIMs in hazardlib have a minimum distance cutoff: for distances
below the ``minimum_distance`` they give always the same result, which
is the value at the minimum distance. The ``minimum_distance`` is
normally provided by the author of the GSIMs, but it is somewhat
heuristic. It may be useful to experiment with different values of the
``minimum_distance``, to see how the hazard and risk change.  It would
be too inconvenient to have to change the source code of the GSIM
every time. Instead, the user can specify a ``minimum_distance``
attribute in the GSIM logic tree branch that will take precedence over
the one in hazardlib.  Here is an example:

.. code-block:: xml
         
      <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="bs1"
                          applyToTectonicRegionType="Subduction Deep">
        
         <logicTreeBranch branchID="b1">
           <uncertaintyModel minimum_distance="10">
             LinLee2008SSlab
           </uncertaintyModel>
           <uncertaintyWeight>0.60</uncertaintyWeight>
         </logicTreeBranch>
           
         <logicTreeBranch branchID="b2">
           <uncertaintyModel minimum_distance="5">
             YoungsEtAl1997SSlab
           </uncertaintyModel>
           <uncertaintyWeight>0.40</uncertaintyWeight>
         </logicTreeBranch>
       </logicTreeBranchSet>

Most GSIMs do not have a ``minimum_distance`` parameter in hazardlib,
which is equivalent to say that the minimum distance is zero. Even for
them, however, it is possible to set a minimum distance in the logic
tree in order to perform sensitivity experiments at small distances.

GMPE logic trees with weighted IMTs
-------------------------------------------

Our Canadian users asked us to implement GMPE logic trees with a
different weight per each IMT. For instance you could have a GMPE
applicable to PGA with a certain level of uncertainty, to SA(0.1) with
another and to SA(1.0) with still another one. The user may want to
give an higher weight to the IMTs were the GMPE has a small
uncertainty and a lower weight to the IMTs with a large
uncertainty. Moreover the GMPE could not be applicable for some
period, and in that case the user can assign to it a zero weight, to
ignore it.  This is useful when you have a logic tree with multiple
GMPEs per branchset, some of which are applicable for some IMTs and
not for others.  Here is an example:

.. code-block:: xml

    <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="bs1"
            applyToTectonicRegionType="Volcanic">
        <logicTreeBranch branchID="BooreEtAl1997GeometricMean">
            <uncertaintyModel>BooreEtAl1997GeometricMean</uncertaintyModel>
            <uncertaintyWeight>0.33</uncertaintyWeight>
            <uncertaintyWeight imt="PGA">0.25</uncertaintyWeight>
            <uncertaintyWeight imt="SA(0.5)">0.5</uncertaintyWeight>
            <uncertaintyWeight imt="SA(1.0)">0.5</uncertaintyWeight>
            <uncertaintyWeight imt="SA(2.0)">0.5</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="SadighEtAl1997">
            <uncertaintyModel>SadighEtAl1997</uncertaintyModel>
            <uncertaintyWeight>0.33</uncertaintyWeight>
            <uncertaintyWeight imt="PGA">0.25</uncertaintyWeight>
            <uncertaintyWeight imt="SA(0.5)">0.5</uncertaintyWeight>
            <uncertaintyWeight imt="SA(1.0)">0.5</uncertaintyWeight>
            <uncertaintyWeight imt="SA(2.0)">0.5</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="MunsonThurber1997Hawaii">
            <uncertaintyModel>MunsonThurber1997Hawaii</uncertaintyModel>
            <uncertaintyWeight>0.34</uncertaintyWeight>
            <uncertaintyWeight imt="PGA">0.25</uncertaintyWeight>
            <uncertaintyWeight imt="SA(0.5)">0.0</uncertaintyWeight>
            <uncertaintyWeight imt="SA(1.0)">0.0</uncertaintyWeight>
            <uncertaintyWeight imt="SA(2.0)">0.0</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="Campbell1997">
            <uncertaintyModel>Campbell1997</uncertaintyModel>
            <uncertaintyWeight>0.0</uncertaintyWeight>
            <uncertaintyWeight imt="PGA">0.25</uncertaintyWeight>
            <uncertaintyWeight imt="SA(0.5)">0.0</uncertaintyWeight>
            <uncertaintyWeight imt="SA(1.0)">0.0</uncertaintyWeight>
            <uncertaintyWeight imt="SA(2.0)">0.0</uncertaintyWeight>
        </logicTreeBranch>
    </logicTreeBranchSet>        

Clearly the weights for each IMT must sum up to 1, otherwise the engine
will complain. Note that this feature only works for the classical and
disaggregation calculators: in the event based case only the default
``uncertaintyWeight`` (i.e. the first in the list of weights, the one
without ``imt`` attribute) would be taken for all IMTs.


Equivalent Epicenter Distance Approximation
-------------------------------------------

The equivalent epicenter distance approximation (``reqv`` for short)
was introduced in engine 3.2 to enable the comparison of the OpenQuake
engine with time-honored Fortran codes using the same approximation.

You can enable it in the engine by adding a ``[reqv]`` section to the
job.ini, like in our example in
openquake/qa_tests_data/classical/case_2/job.ini::

reqv_hdf5 = {'active shallow crust': 'lookup_asc.hdf5',
             'stable shallow crust': 'lookup_sta.hdf5'}

For each tectonic region type to which the approximation should be applied,
the user must provide a lookup table in .hdf5 format containing arrays
``mags`` of shape M, ``repi`` of shape N and ``reqv`` of shape (M, N).

The examples in openquake/qa_tests_data/classical/case_2 will give you
the exact format required. M is the number of magnitudes (in the examples
there are 26 magnitudes ranging from 6.05 to 8.55) and N is the
number of epicenter distances (in the examples ranging from 1 km to 1000 km).

Depending on the tectonic region type and rupture magnitude, the
engine converts the epicentral distance ``repi` into an equivalent
distance by looking at the lookup table and use it to determine the
``rjb`` and ``rrup`` distances, instead of the regular routines. This
means that within this approximation ruptures are treated as
pointwise and not rectangular as the engine usually does.

Notice that the equivalent epicenter distance approximation only
applies to ruptures coming from
PointSources/AreaSources/MultiPointSources, fault sources are
untouched.


Ruptures in CSV format
-------------------------------------------

Since engine v3.10 there is a way to serialize ruptures in
CSV format. The command to give is::
  
  $ oq extract "ruptures?min_mag=<mag>" <calc_id>`

For instance, assuming there is an event based calculation with ID 42,
we can extract the ruptures in the datastore with magnitude larger than
6 with ``oq extract "ruptures?min_mag=6" 42``: this will generate a CSV file.
Then it is possible to run scenario
calculations starting from that rupture by simply setting

``rupture_model_file = ruptures-min_mag=6_42.csv``

in the ``job.ini`` file. The format is provisional and may change in the
future, but it will stay a CSV with JSON fields. Here is an example
for a planar rupture, i.e. a rupture generated by a point source::

  #,,,,,,,,,,"trts=['Active Shallow Crust']"
  serial,mag,rake,lon,lat,dep,multiplicity,trt,kind,mesh,extra
  24,5.050000E+00,0.000000E+00,0.08456,0.15503,5.000000E+00,1,Active Shallow Crust,ParametricProbabilisticRupture PlanarSurface,"[[[0.08456, 0.08456, 0.08456, 0.08456]], [[0.13861, 0.17145, 0.13861, 0.17145]], [[3.17413, 3.17413, 6.82587, 6.82587]]]","{""occurrence_rate"": 4e-05}"

The format is meant to support all kind of ruptures, including ruptures
generated by simple and complex fault sources, characteristic sources,
nonparametric sources and new kind of sources that could be introduced
in the engine in the future. The header will be the same for all
kind of ruptures that will be stored in the same CSV. Here is description
of the fields as they are named now:

serial
  the serial number of the rupture, which is also the random seed used
  to compute the GMFs
mag
  the magnitude of the rupture
rake
  the rake angle of the rupture surface in degrees
lon
  the longitude of the hypocenter in degrees
lat
  the latitude of the hypocenter in degrees
dep
  the depth of the hypocenter in km
multiplicity
  the number of occurrences of the rupture
trt
  the tectonic region type of the rupture; must be consistent with the
  trts listed in the pre-header of the file
kind
  a space-separated string listing the rupture class and the surface class
  used in the engine
mesh
  nested list with lon, lat, dep of the points of the discretized
  rupture geometry
extra
  extra parameters of the rupture as a JSON dictionary, for instance
  the rupture occurrence rate

Notice that using a CSV file generated with an old version of the engine
is inherently risky: for instance if we changed the
``ParametricProbabilisticRupture`` class or the ``PlanarSurface classes`` in an
incompatible way with the past, then a scenario calculation starting
with the CSV would give different results in the new version of the engine.
We never changed the rupture classes or the surface
classes, but we changed the seed algorithm often, and that too would
cause different numbers to be generated (hopefully, statistically
consistent). A bug fix or change of logic in the calculator can also
change the numbers across engine versions.
  
``max_sites_disagg``
--------------------------------

There is a parameter in the `job.ini` called ``max_sites_disagg``, with a
default value of 10. This parameter controls the maximum number of sites
on which it is possible to run a disaggregation. If you need to run a
disaggregation on a large number of sites you will have to increase
that parameter. Notice that there are technical limits: trying to
disaggregate 100 sites will likely succeed, trying to disaggregate
100,000 sites will most likely cause your system to go out of memory or
out of disk space, and the calculation will be terribly slow.
If you have a really large number of sites to disaggregate, you will
have to split the calculation and it will be challenging to complete
all the subcalculations.

The parameter ``max_sites_disagg`` is extremely important not only for
disaggregation, but also for classical calculations. Depending on its
value and then number of sites (``N``) your calculation can be in the
*few sites* regime or the *many sites regime*.

In the *few sites regime* (``N <= max_sites_disagg``) the engine stores
information for each rupture in the model (in particular the distances
for each site) and therefore uses more disk space. The problem is mitigated
since the engine uses a relatively aggressive strategy to collapse ruptures,
but that requires more RAM available.

In the *many sites regime* (``N > max_sites_disagg``) the engine does not store
rupture information (otherwise it would immediately run out of disk space,
since typical hazard models have tens of millions of ruptures) and uses
a much less aggressive strategy to collapse ruptures, which has the advantage
of requiring less RAM.

extendModel
---------------------------------

Starting from engine 3.9 there is a new feature in the source model
logic tree: the ability to define new branches by adding sources
to a base model. An example will explain it all:

.. code-block:: xml

  <?xml version="1.0" encoding="UTF-8"?>
  <nrml xmlns:gml="http://www.opengis.net/gml"
        xmlns="http://openquake.org/xmlns/nrml/0.4">
    <logicTree logicTreeID="lt1">
      <logicTreeBranchSet uncertaintyType="sourceModel"
                          branchSetID="bs0">
        <logicTreeBranch branchID="b01">
          <uncertaintyModel>common1.xml</uncertaintyModel>
          <uncertaintyWeight>0.6</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="b02">
          <uncertaintyModel>common2.xml</uncertaintyModel>
          <uncertaintyWeight>0.4</uncertaintyWeight>
        </logicTreeBranch>
      </logicTreeBranchSet>
      <logicTreeBranchSet uncertaintyType="extendModel" applyToBranches="b01"
                          branchSetID="bs1">
        <logicTreeBranch branchID="b11">
          <uncertaintyModel>extra1.xml</uncertaintyModel>
          <uncertaintyWeight>0.6</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="b12">
          <uncertaintyModel>extra2.xml</uncertaintyModel>
          <uncertaintyWeight>0.4</uncertaintyWeight>
        </logicTreeBranch>
      </logicTreeBranchSet>
    </logicTree>
  </nrml>

In this example there are two base source models, named ``commom1.xml`` and
``common2.xml``; the branchset with ``uncertaintyType = "extendModel"`` is
telling the engine to generate two effective source models by extending
``common1.xml`` first with ``extra1.xml`` and then with ``extra2.xml``.
If we removed the constraint ``applyToBranches="b01"`` then two additional
effective source models would be generated by applying ``extra1.xml`` and
``extra2.xml`` to ``common2.xml``.
