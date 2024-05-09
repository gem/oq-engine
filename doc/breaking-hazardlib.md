The problem as of June 2021
---------------------------

As it is well known, the main road to scientific programming in Python
is numpy-oriented programming. The recipe is simple: **dot not use
user-defined objects, use numpy arrays everywhere**.

Unfortunaly hazardlib was designed over 10 years ago without following
this philosophy and it is actually a class-oriented library, full of
complex hierarchies with plenty of overridden methods. While this is not a big
issue for objects that do not enter in inner loops (like sources;
using classes for sources is not a big deal), it is a major problem
for objects like intensity measure types, ruptures and GMPEs.

That original design choice *makes it impossible to speedup hazardlib*,
since every performance-oriented tool (numba, cython, etc) requires a
numpy-oriented codebase to start from.

Until now we managed to live with this original sin, since the main use
for the engine is to build national hazard maps. In this case for each IMT,
rupture and GSIM there are normally thousands of affected sites: looping
on the ruptures, IMTs and GSIMs in Python is not an issue since the meat
of the calculation is on the sites. However, for site-specific calculations
the performance of the engine is disastrous.

Experiments that I made last year suggest that if we could vectorize
on the ruptures we could reach speedups on single-site calculations of
the order of 30x.

However vectorizing on the ruptures (with the current state of the
code) means essentially to double the size of hazardlib, adding to
every method vectorized by site a companion method vectorized by
rupture, plus some logic to decide when to use an approach or the
other depending on the number of sites.

It should be noticed that working incrementamentally is not an option:
as soon as a single GMPE (of the dozens normally used in a hazard model)
is not vectorized by rupture the entire calculation will be slow.

As of June 2021 hazardlib/gsim contains over 160,000 lines of code, including
docstrings and comments, nearly 500 GMPE classes and nearly 1400 methods. On
the other hand, there is only one person maintaining it.

It is clearly impossible to refactor hazardlib manually, but we could
investigate ways to automatize at least some kinds of refactoring.
Vectorizing by rupture is certainly hard and must be done on a case-by-case
basis.

Towards a numpy-oriented hazardlib
----------------------------------

Rather than reimplementing thousands of methods it would be much better
to make hazardlib more numpy-oriented. If hazardlib was fully numpy-oriented,
looping on the ruptures could be done at C-speed and there
would be no need to duplicate methods.

The move towards numpy actually started many years ago, and for
instance now we have `Context` objects which are closer to numpy
arrays than `Rupture` objects. However, we are at the very beginning,
and very far for the ideal goal.

To be clear, the ideal goal would be to **remove completely all class
hierarchies and turn all methods into functions taking in input only
numpy arrays or simple types**.

The ideal goal is out of reach (by far), so we will have to compromise
significantly; moreover, since we have hundreds of users of hazardlib,
we always must keep in main that any nontrivial refactoring would break
user code.

What it is feasible as first step is to simplify the class hierarchy
of the GMPEs: right now it is a fully general multiple inheritance
hierarchy. *Per se* this is already bad, since actually we do not need
multiple inheritance: its existency is only making further refactoring harder.

So the first step is to forbid multiple inheritance. This will break the
code of users using multiple inheritance. It is likely that there
are no such users and even it there are, we can suggest to them some
workarounds.

The second step is to try to simplify the single inheritance hierarchy,
wich is 7 levels deep, with structures like

```
1  GroundShakingIntensityModel
2    GMPE
3      Bradley2013
4          Bradley2013LHC
5              Bradley2013bChchCBD
6                  Bradley2013bChchNorth
7                      Bradley2013bChchNorthAdditionalSigma
```

The ideal would be to have a flat hierarchy. Then one would have
to extract the methods from the classes and then reduce the GMPE classes
to numpy arrays, but this is too difficult for the moment.

But just simplifying the hierarchy is a good thing, even if the speedup
will be zero, because it will make reasoning about hazardlib easier and
will enable further refactorings.

Another step in the direction of numpy-oriented programming would be to
replace all methods of the GMPEs which are overridden with generic
functions. This will be long but it is likely feasible.
There plenty of methods to consider, including the following:

```
_a0
_c0
_clip_mean
_compute_distance
_compute_distance_term
_compute_focal_depth_term
_compute_forearc_backarc_term
_compute_magnitude
_compute_mean
_convert_magnitude
_depth_scaling
_get_adjusted_stddevs
_get_anelastic_coeff
_get_dS2S
_get_delta_c1
_get_deltac3
_get_deltas
_get_ln_a_n_max
_get_ln_sf
_get_magnitude_scale
_get_magnitude_term
_get_mean
_get_regional_site_term
_get_site_amplification_term
_get_site_class
_get_stddevs
_get_style_of_faulting_term
_path_term_h
_set_params
_setup_standard_deviations
compute_base_term
compute_depth_term
compute_magnitude_term
get_amplification_factor
get_depth_term
get_distance_coefficients
get_distance_term
get_magnitude_scaling_term
get_site_amplification
get_sof_term
get_stddevs
```

Before doing that we should see if we can replace the IMT classes with
numpy objects. This looks much easier, even if still difficult since
it may break use code.

It is important to notice that there is an unwanted complication in the IMTs:
there is a lot of work to  support the `sa_damping` field which actually is
actually hard-coded to 5.0 in all CoeffsTable. It would be nice to remove it.

It would also be nice to be able to vectorize by IMT. But that will be
difficult too. At minimum one will have to refactor the usage of the
`CoeffsTable` (update: as of June the 10th the `CoeffsTable` has been
refactored and we are now able to proceed with the program *even
without replacing the existing IMT classes*, which is a major
compatibility win).

This is going to be long (months/years). It is also possible that we will
never reach the ideal. Also, in the normal case with many sites (national
hazard maps) all this effort will give moderate speedups, possibly zero
speedup.

Nevertheless we need to do something. Every year hazardlib becomes
larger, every year we have more users, every year it is more difficult
to change anything, every year the models become larger and slower,
and every year the frustration caused by the initial design decisions
increases.

The GMPEs at C speed
--------------------

As I said, a numpy-oriented API will improve single-site calculations
by an order of magnitude or so, *even without numba/Cython acceleration*,
because of the automatic vectorization by ruptures. But once we have the
new API in place the following workflow will become possible:

1. read the input files
2. determine the required GMPEs and parameters (distances, site params, etc)
3. determine the required numpy dtypes and compile the required functions
   (`calc_mean`, `calc_stdt`, ...) with the right specializations
4. import the generated extension module and replace the interpreted
   functions with the compiled functions, while still in pre_execute phase
5. run the calculation at C speed!

In practice switching to the new API means *rewriting hazardlib in C
but without leaving the Python world*.

This, in theory, but the devil is in the details;-) Generally speaking, *the
performance for global hazard models is not expected to improve*, since we
are already working at C speed in numpy, due to the vectorization by sites.

The plan
---------------------

Here is the long term plan:

**Phase 0:** remove multiple inheritance, replace IMT classes with a
single namedtuple class, at the cost of a minor breakage of user
code. Already done (at the end of June 2021).

**Phase 1:** replace all methods of the GMPEs with helper functions,
except for the method *get_mean_and_stddevs*. This can be done mostly
without breaking user code since such methods were essentially
private already. In progress.

**Phase 2:** replace the method *get_mean_and_stddevs* with a new method
*compute(ctx, imts, mean, sig, tau, phi)*, while keeping backward
compatibility.

**Phase 3:** vectorize by rupture. This is hard, and it is only in this phase
that we will see the speedup for single site situations.

**Phase 4:** investigate the usage of numba or other compilation
techniques.  They will always be *optional*, i.e. the engine will work
even if numba is not installed. It could be that phase 4 will never be
implemented, if the performance tests show that there is no benefit
(as it seems to be the case at the present).

Update at March 2022
--------------------

The vectorization plan is now complete. All of the GMPEs in hazardlib
are vectorized, and trying to introduce a new non-vectorized GMPE will
result in an error. Phases 1, 2 and 3 are done, while I have decided
not to start on Phase 4, since it is too much of an effort. Instead
of doing Phase 4 there is a much simpler and much effective way to
progress, i.e. the collapsing of the contexts which will be implemented
in the following months.
