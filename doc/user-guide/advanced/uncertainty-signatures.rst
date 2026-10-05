.. _uncertainty-signatures:

Uncertainty signatures
----------------------

NB: *new in version 3.27*

In the OpenQuake engine the epistemic uncertainties are applied to the
sources one set of realizations at a time; realizations having the
same uncertainties for a given source are identified by a so-called
*uncertainty signature*.

In particular for classical calculations there is a global RateMap,
i.e. an array of float32 numbers of shape (N, L, Gt), where N is the
total number of hazard sites, L the total number of intensity measure
levels and Gt is the total number of uncertainty signatures summed over
all the tectonic region types::

      Gt = Σ_i G(trt_i)

 ``Gt`` is also called the *core size* of the logic tree.
 
.. note::

   Since many realizations have the same uncertainties, the core size
   is typically **much smaller** than the number R of realizations of
   the logic tree: in the demo described below there are 324
   realizations but only 36 uncertainty signatures, i.e. 9 times less data
   than one would store naively. This is what
   makes it possible to run large logic trees; see
   :ref:`large-calculations`.

   The global RateMap is usually not kept in memory: it
   is materialized in the master node only when the rates must be accumulated
   there, i.e. when there are few sites, or when ``disagg_by_src`` is
   set, or when the sources of a group are split in blocks. It is still
   a useful concept, since the rates stored in the datastore are enough
   to reconstruct it and from the global RateMap one can rebuild the
   full hazard curves for all realizations (the engine does that in
   postclassical by splitting in blocks of sites so that it does
   not need to keep the full RateMap in memory).

Since the signatures are fully determined by the logic tree and by the
source model, they are computed while building the CompositeSourceModel,
i.e. before the preclassical, and stored in the datastore in the
``unc_signatures`` dataset; the core size is logged at the same time,
together with the size in bytes of the global RateMap.

The concept of uncertainty signatures is relevant only if your logic
tree contains ``applyToSources`` or ``applyToBranches``, i.e. only if some
uncertainties are applied to a subset of the sources. If all the
uncertainties are applied to all the sources, each source has a single
signature covering all its realizations and there is nothing to sign.

In that case (the trivial case) ``Gt`` can be computed trivially as
the sum of the number of GSIMs for each tectonic region type::

  Gt = Σ_i num_gsims(trt_i)

In the nontrivial case the engine can determine the signatures and the core size without
running a full calculation; just run the command ``oq check_input job.ini`` and they will
be printed at the end; they can be also inspected in any calculation with
the command ``oq show unc_signatures``.

NB: for branchsets with parameters the ``values`` column contains a
tuple per distinct value, i.e. the fields of the value, and the fields
changing across the values are listed in brackets at the end, i.e.
``(0.8, 3.25, 0.371113), (0.8, 3.25, 0.29666) [rate: 0.371113,
0.29666]``; this is how the table can stay readable for models with
many sources and branchsets.

An example with applyToSources
------------------------------

The demo ``LogicTreeCase2ClassicalPSHA`` has a ``sourceModel`` branchset
and four uncertainty branchsets, ``abGRAbsolute`` and
``maxMagGRAbsolute`` applied to the first and to the second source, each
with three branches::

    sourceModel(1) x abGRAbsolute first(3) x maxMagGRAbsolute first(3)
                 x abGRAbsolute second(3) x maxMagGRAbsolute second(3)
                 = 81 source model paths

and the check gives::

    Core size Gt=36 out of R=324 realizations
    Global RateMap of 2.67 KB for 1 sites and 19 levels
    ...
    Uncertainty signatures of calc_172129
    | source_id | realizations | signatures | counts | branchset | values                             |
    |-----------+--------------+------------+--------+-----------+------------------------------------|
    | first     | 81           | 9          | 9      | bs2       | (4.6, 1.1), (4.5, 1.0), (4.4, 0.9) |
    |           |              |            |        | bs4       | 7.0, 7.3, 7.6                      |
    | second    | 81           | 9          | 9      | bs3       | (3.3, 1.0), (3.2, 0.9), (3.1, 0.8) |
    |           |              |            |        | bs5       | 7.5, 7.8, 8.0                      |

Only ``bs2`` and ``bs4`` apply to the area source ``first`` and only
``bs3`` and ``bs5`` apply to the fault source ``second``, therefore each
source has 9 signatures covering the 9 realizations obtained by varying
the uncertainties of the other source, i.e. 18 indices of rate
attribution in total, 9 per source. Since there are two GMMs per tectonic
region type, Gt = 18 x 2 = 36, i.e. the 324 realizations of the logic
tree are reduced to 36 columns of the global RateMap.

Since the core size Gt determines the size of the global RateMap, the
signatures are also a way to understand why a calculation is large; see
:ref:`large-calculations`.

An example with applyToBranches
-------------------------------

Consider the test case ``logictree/case_12``, with a ``sourceModel``
branchset with two branches (``fault_background`` and
``smooth_collapsed``), a ``bGRRelative`` branchset with three branches and
``applyToBranches="smooth_collapsed"`` and a ``maxMagGRRelative``
branchset with three branches.

You can extract the information about the logic tree with the command
``oq info job.ini``, which lists the branchsets with their filters and
plots the tree of branches::

    $ oq info openquake/qa_tests_data/logictree/case_12/job.ini
    calculation_mode: classical
    description: 2018 PSHA model - North Africa
    site parameters: vs30
    input size: 7.47 KB
    <sourceModel(2)>
    <bGRRelative(3, applyToBranches=smooth_collapsed)>
    <maxMagGRRelative(3)>
    └── sm1
        ├── fault_background
        │   └── fault_background
        │       ├── m_m0.2
        │       ├── m_e0.0
        │       └── m_p0.2
        └── smooth_collapsed
            ├── b_m0.05
            │   ├── m_m0.2
            │   ├── m_e0.0
            │   └── m_p0.2
            <snip>
            └── b_p0.05
                ├── m_m0.2
                ├── m_e0.0
                └── m_p0.2

The plot shows at a glance that the branchset ``bval`` appears only inside
the ``smooth_collapsed`` sector of the tree, while the ``fault_background``
branch has only the three branches of ``mmax``.

The signatures are printed by the check command::

    $ oq check_input openquake/qa_tests_data/logictree/case_12/job.ini
    ...
    Building 12 realizations
    ...
    Core size Gt=10 out of R=12 realizations
    Global RateMap of 400 B for 1 sites and 10 levels
    ...
    Uncertainty signatures of calc_172128
    | source_id | realizations | signatures | counts | branchset | values           |
    |-----------+--------------+------------+--------+-----------+------------------|
    | BG_10     | 3            | 1          | 3      | -         | no uncertainties |
    | SC_10:124 | 9            | 9          | 1      | bval      | 0.0, 0.05, -0.05 |
    |           |              |            |        | mmax      | 0.0, 0.2, -0.2   |

There is a row for each pair (source, branchset), since a signature is a
combination of values of branchsets, and a row with ``-`` for the sources
with no uncertainties at all. The ``source_id`` and the columns before
``branchset`` are printed only on the first row of each source, so that
the rows belonging to the same source are visually grouped.

The source ``BG_10`` is in the ``fault_background`` source model, to which
the branchset ``bval`` does not apply, so it has a single signature
covering its 3 realizations; the source ``SC_10:124`` is in the
``smooth_collapsed`` model, to which both ``bval`` and ``mmax`` apply, so
it has 3 x 3 = 9 signatures with one realization each.

The core size ``Gt=10`` of the global RateMap can be read directly from
the table: ``BG_10`` contributes a single index of rate attribution (its
only signature covers the 3 realizations) and ``SC_10:124`` contributes
9, for a total of 1 + 9 = 10; since the GMM logic tree of the case has a
single GMM there is one column per index of rate attribution, i.e.::

    Gt = (1 + 9) x G(trt) = 10 x 1 = 10   with   R = 12 realizations

i.e. Gt is smaller than R because the 3 realizations of the
``fault_background`` model have the same (empty) signature, so they have
the same rates and share a single column.

NB: even though ``mmax`` has no filters, it is not applied to ``BG_10``
either, since a branchset following a branchset with filters applies only
within the same sector of the logic tree, i.e. to the branches selected by
the filters.

The ``signatures`` column contains the number of signatures of the source
and the ``counts`` column the number of realizations per signature; they
are reported as a set, since the signatures do not necessarily contain
the same number of realizations. This is particularly relevant for
correlated uncertainties, where the sources of a group can have
different signatures and a realization can belong to more than one index
of rate attribution: see :ref:`correlated-uncertainties`.
