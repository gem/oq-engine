.. _uncertainty-signatures:

Uncertainty signatures
----------------------

The epistemic uncertainties are applied one set of realizations at a time;
the sets of realizations having the same uncertainties for a given source
are called *uncertainty signatures* (see :ref:`the section on the
management of the uncertainties in the classical calculator
<classical-internals>`).

.. note::

   The crucial consequence is that the rates are stored per signature,
   i.e. per *index of rate attribution* (gid), and **not** per
   realization. The number of indices of rate attribution (gid) is the
   *core size* of the logic tree, i.e. the number of columns of the
   global RateMap of shape (N, L, Gt)::

      Gt = Σ_i G(trt_i)

   where the sum is over the indices of rate attribution and G(trt) is
   the number of GMMs for the tectonic region type. Since many
   realizations have the same uncertainties, the core size is typically
   **much smaller** than the number R of realizations of the logic tree:
   in the demo described below there are 324 realizations but only 36
   columns of rates, i.e. 9 times less data than one would store with a
   column per realization. This is what makes it possible to run large
   logic trees; see :ref:`large-calculations`.

Since the signatures are fully determined by the logic tree and by the
source model, they are computed while building the CompositeSourceModel,
i.e. before the preclassical, and stored in the datastore in the
``unc_signatures`` dataset; the core size is logged at the same time,
together with the size in bytes of the global RateMap.

NB: the concept of uncertainty signatures is relevant only if your logic
tree contains ``applyToSources`` or ``applyToBranches``, i.e. only if some
uncertainties are applied to a subset of the sources. If all the
uncertainties are applied to all the sources, each source has a single
signature covering all its realizations and there is nothing to sign.

You can determine the signatures and the core size without running a full
calculation; just run the command ``oq check_input job.ini`` and they will
be printed at the end; they can be also inspected in any calculation with
the commands ``oq show unc_signatures`` and ``oq show trt_smrs_gid``.

An example with applyToBranches
-------------------------------

Consider the test case ``logictree/case_12``, with a ``sourceModel``
branchset with two branches (``fault_background`` and
``smooth_collapsed``), a ``bGRRelative`` branchset with three branches and
``applyToBranches="smooth_collapsed"`` and a ``maxMagGRRelative``
branchset with three branches::

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
    | SC_10:124 | 9            | 9          | 1      | mmax      | 0.0, 0.2, -0.2   |

There is a row for each pair (source, branchset), since a signature is a
combination of values of branchsets, and a row with ``-`` for the sources
with no uncertainties at all.

The source ``BG_10`` is in the ``fault_background`` source model, to which
the branchset ``bval`` does not apply, so it has a single signature
covering its 3 realizations; the source ``SC_10:124`` is in the
``smooth_collapsed`` model, to which both ``bval`` and ``mmax`` apply, so
it has 3 x 3 = 9 signatures with one realization each. Since the GMM
logic tree of the case has a single GMM, there are 1 + 9 = 10 indices of
rate attribution and Gt = 10: notice that Gt is smaller than R = 12 since
the 3 realizations of the ``fault_background`` model have the same (empty)
signature, i.e. they produce the same rates.

NB: even though ``mmax`` has no filters, it is not applied to ``BG_10``
either, since a branchset following a branchset with filters applies only
within the same sector of the logic tree, i.e. to the branches selected by
the filters.

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
    | first     | 81           | 9          | 9      | bs4       | 7.0, 7.3, 7.6                      |
    | second    | 81           | 9          | 9      | bs3       | (3.3, 1.0), (3.2, 0.9), (3.1, 0.8) |
    | second    | 81           | 9          | 9      | bs5       | 7.5, 7.8, 8.0                      |

Only ``bs2`` and ``bs4`` apply to the area source ``first`` and only
``bs3`` and ``bs5`` apply to the fault source ``second``, therefore each
source has 9 signatures covering the 9 realizations obtained by varying
the uncertainties of the other source, i.e. 18 indices of rate
attribution in total, 9 per source. Since there are two GMMs per tectonic
region type, Gt = 18 x 2 = 36, i.e. the 324 realizations of the logic
tree are reduced to 36 columns of the global RateMap.

The ``signatures`` column contains the number of signatures of the source
and the ``counts`` column the number of realizations per signature; they
are reported as a set, since the signatures do not necessarily contain
the same number of realizations. This is particularly relevant for
correlated uncertainties, where the sources of a group can have
different signatures and a realization can belong to more than one index
of rate attribution: see :ref:`correlated-uncertainties`.

Since the core size Gt determines the size of the global RateMap, the
signatures are also a way to understand why a calculation is large; see
:ref:`large-calculations`.
