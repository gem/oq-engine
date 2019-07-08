Special features of the classical calculator
============================================

There are few rarely used feature of the classical calculator that are not
documented in the manual, since their usage is quite specific. They are
documented here.

GMPE logic trees with weighted IMTs
-------------------------------------------

Our Canadian users asked us to implement GMPEs with a different weight per
each IMT. For instance you could have a GMPE applicable to PGA with a certain
level of uncertainty to SA(0.1) with another and to SA(1.0) with still
another one. The user may want to give an higher weight to the IMT were the
GMPE has a small uncertainty and a lower weight to the IMT with a large
uncertainty. More the GMPE could not even be applicable for say SA(2.0)
and in that case the user can assign to it a zero weight, to ignore it.
This is useful when you have a logic tree with multiple GMPEs, some of
which are applicable for some IMTs and not for others.



Equivalent Epicenter Distance Approximation
-------------------------------------------

The equivalent epicenter distance approximation (``reqv`` for short)
was introduced in engine 3.2 to enable the comparison of the OpenQuake
engine with time-honored Fortran codes using the same approximation.

You can enable it in the engine by adding a ``[reqv]`` section to the
job.ini, like in our example in
openquake/qa_tests_data/classical/case_2/job.ini::

  [reqv]
  active shallow crust = lookup_asc.hdf5
  stable shallow crust = lookup_sta.hdf5

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
means that within this approximation ruptures are treated as really
pointwise and not rectangular as the engine usually does.

Notice that the equivalent epicenter distance approximation only
applies to ruptures coming from
PointSources/AreaSources/MultiPointSources, fault sources are
untouched.
