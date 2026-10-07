.. _uncertainty-signatures:

Uncertainty signatures
----------------------

NB: *new in version 3.27*

In the OpenQuake engine the epistemic uncertainties are applied to the
sources by sets of realizations; realizations having the same
uncertainties for a given source are identified by their *uncertainty
signature*. The signatures are fully determined by the logic tree,
computed while building the ``CompositeSourceModel``, and stored in
the datastore in the ``unc_signatures`` dataset.

Notice that the concept of uncertainty signatures is relevant only if your logic
tree contains source uncertainties. The uncertainties
on the GSIMs (``applyToTectonicRegionType``) are considered trivial
and not stored in ``unc_signatures``. Same for uncertainties on
the source models (i.e. ``sourceModel/extendModel``).

.. note::

   Since many realizations have the same uncertainties, the true cost
   of a calculation (both computational and of disk space) is proportional
   to the *core size*

      :math:`G_t = \sum_i G(\mathrm{trt}_i)`

   of the logic tree, is typically **much smaller** than the number
   ``R`` of realizations: in the demo ``LogicTreeCase1ClassicalPSHA``
   there are 324 realizations but only 36 uncertainty signatures,
   i.e. 9 times less data than one would store naively. This is what
   makes it possible to run large logic trees; see
   :ref:`large-calculations`.

In the trivial case of no source uncertainties, ``Gt`` can be computed as
the sum of the number of GSIMs for each tectonic region type:

  :math:`G_t = \sum_i \mathrm{num\_gsims}_i(\mathrm{trt}_i)`

Notice that identical tectonic region types appearing in different source models
are considered distinct. For instance in the ``LogicTreeCase1ClassicalPSHA``
demo there are 2 GSIMs per tectonic region type, 2 tectonic
region types from the first source model and 2 from the second source model
(identical but considered distinct) and therefore Gt = 2*2 + 2*2 = 8.

In the nontrivial case the engine can determine the signatures and the core size without
running a full calculation; just run the command ``oq check_input job.ini`` and they will
be printed at the end; they can be also inspected in any calculation with
the command ``oq show usignatures``.

An example with applyToSources
------------------------------

The demo ``LogicTreeCase2ClassicalPSHA`` has a ``sourceModel`` branchset
and four uncertainty branchsets, ``abGRAbsolute`` and
``maxMagGRAbsolute`` applied to the first and to the second source, each
with three branches::

    sourceModel(1) x abGRAbsolute first(3) x maxMagGRAbsolute first(3)
                 x abGRAbsolute second(3) x maxMagGRAbsolute second(3)
                 = 81 source model paths

The total number of realizations must be multipled by 4 since there are 2 tectonic region
types with 2 GSIMs each. The check gives::

    Core size Gt=36 out of R=324 realizations
    Global RateMap of 2.67 KB for 1 sites and 19 levels
    ...
    Uncertainty signatures of calc_172129
    | source_id | num_rlzs                  | branchset | values                             |
    |-----------+---------------------------+-----------+------------------------------------|
    | first     | 9, 9, 9, 9, 9, 9, 9, 9, 9 | bs2       | (4.6, 1.1), (4.5, 1.0), (4.4, 0.9) |
    |           |                           | bs4       | 7.0, 7.3, 7.6                      |
    | second    | 9, 9, 9, 9, 9, 9, 9, 9, 9 | bs3       | (3.3, 1.0), (3.2, 0.9), (3.1, 0.8) |
    |           |                           | bs5       | 7.5, 7.8, 8.0                      |

Only ``bs2`` and ``bs4`` apply to the area source ``first`` and only
``bs3`` and ``bs5`` apply to the fault source ``second``, therefore each
source has 3 x 3 = 9 signatures; each source is in the 81 source model
realizations (the GMM logic tree has 4 branches, so R = 81 x 4 = 324),
hence each signature covers 9 realizations, i.e. the ones differing
only in the uncertainties of the other source. In total there are 18
realization sets, 9 per source, so that with two GMMs per tectonic
region type Gt = 18 x 2 = 36, i.e. the 324 realizations of the logic
tree are reduced to 36 columns of the global ``RateMap``.

NB: the global ``RateMap``, is an array of float32 numbers of shape (N, L,
Gt), where N is the total number of hazard sites, L the total number
of intensity measure levels and Gt is the core size of the logic tree.
From the global ``RateMap`` it is possible to reconstruct the full set
of hazard curves for every possible realization, as we will discuss
later on.

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
    | source_id | num_rlzs                  | branchset | values           |
    |-----------+---------------------------+-----------+------------------|
    | BG_10     | 3                         | -         | no uncertainties |
    | SC_10:124 | 1, 1, 1, 1, 1, 1, 1, 1, 1 | bval      | 0.0, 0.05, -0.05 |
    |           |                           | mmax      | 0.0, 0.2, -0.2   |

There is a row for each pair (source, branchset), since a signature is a
combination of values of branchsets, and a row with ``-`` for the sources
with no uncertainties at all. The ``source_id`` and the ``num_rlzs``
column are printed only on the first row of each source, so that the
rows belonging to the same source are visually grouped.

The source ``BG_10`` is in the ``fault_background`` source model, to which
the branchset ``bval`` does not apply, so it has a single signature
covering its 3 realizations; the source ``SC_10:124`` is in the
``smooth_collapsed`` model, to which both ``bval`` and ``mmax`` apply, so
it has 3 x 3 = 9 signatures with one realization each.

The core size ``Gt=10`` of the global ``RateMap`` can be read directly from
the table: ``BG_10`` contributes a single index of rate attribution (its
only signature covers the 3 realizations) and ``SC_10:124`` contributes
9, for a total of 1 + 9 = 10:

    Gt = (1 + 9) x G(trt) = 10 x 1 = 10

i.e. Gt is smaller than R=12 because the 3 realizations of the
``fault_background`` model have the same (empty) signature, so they have
the same rates and share a single column.

NB: even though ``mmax`` has no filters, it is not applied to ``BG_10``
either, since a branchset following a branchset with filters applies only
within the same sector of the logic tree, i.e. to the branches selected by
the filters.

The ``num_rlzs`` column contains the number of realizations in
each *realization set* of the source, i.e. in each set of realizations
with the same uncertainties, in ascending order: ``1, 1, 1`` means
three realization sets with one realization each, while ``3`` means a
single realization set covering 3 realizations; summing them gives the
total number of realizations of the source and counting them gives its
number of signatures. As long as there are at most 10 realization sets
the values are listed one by one, otherwise the repeated ones are
replaced by their multiplicity, i.e. ``1 (x81 sets)``. This is particularly
relevant for correlated uncertainties, where the sources of a group can
have different signatures and a realization can belong to more than one
realization set: see :ref:`correlated-uncertainties`.
