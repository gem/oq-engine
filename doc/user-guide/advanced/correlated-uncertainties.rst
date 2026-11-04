.. _correlated-uncertainties:

Correlated uncertainties
------------------------

Some epistemic uncertainties make sense only if they are applied
*coherently* to a set of sources: splitting the rate of a background zone
and of the faults bounding it means nothing if it is applied to the
background only, and neither does it make sense to change the dip of one
fault and not the others. Such uncertainties are called *correlated*, and
the page documents how they are handled by the engine, using the test
case ``logictree/case_25``, a BCHydro-style model for British Columbia
with six alternative source models and correlated uncertainties on the
recurrence parameters, the dip and the lower seismogenic depth.

.. contents::
   :local:
   :depth: 1

The logic tree
~~~~~~~~~~~~~~

The logic tree of the case has a ``sourceModel`` branchset with six
branches (``alt1``, ``alt1_AB``, ``alt2``, ``alt2_AB``, ``alt3``,
``alt3_AB``) and then, for each of them, a chain of uncertainty
branchsets attached with ``applyToBranches``, so that the uncertainties
depend on the source model that was selected::

    <logicTreeBranchSet applyToBranches="alt2"
        applyToSources="NVA-bkg NVA-EF1 NVA-EF2
                        NVA-EF3 NVA-EF4"
        branchSetID="alt2_rset" uncertaintyType="recurSet">

Two features make these branchsets correlated:

- ``applyToBranches`` chains them, so that the ``recurRow`` values
  depend on the ``recurSet`` value and the ``rateSplit`` values depend
  on the ``recurRow`` values: the engine rejects a branchset referring to
  branches that do not exist;
- ``applyToSources`` lists *all* the sources that must be modified
  together, e.g. the background source ``NVA-bkg`` and the four
  faults ``NVA-EF1`` … ``NVA-EF4``, which is what guarantees that
  the same rate split is applied to the background and to the faults.

The uncertainties used are ``recurSet``, ``recurRow``, ``rateSplit``,
``simpleFaultDipAbsolute`` and ``setLowerSeismDepthAbsolute``, and they
are applied to *different* subsets of the sources: for instance
``alt2_dip`` (the dip) applies to the four faults only, while
``alt2_lsd`` (the lower seismogenic depth) applies to the background
only.

Resolving the uncertainties
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each pair (realization, source) the engine resolves which
uncertainties apply to that source, by comparing the ``applyToSources``
ids with the source id (or its basename, since the sources of a group
can be fragments of the sources in the logic tree); the result is the
*signature* of the source in that realization, a tuple of
``(branchset id, value)`` pairs. This is done by
``lt.get_bset_value`` and ``source_reader.unc_signature``.

Sources in the same group can be affected by *different* branchsets, so
a group does not necessarily have a single signature. In the realization
``alt2/alt2_rs132/alt2_rspl_rs132_scn1/alt2_rs132_scn1_r00/alt2_dip45/
alt2_lsd15`` the four faults (``NVA-EF1`` to ``NVA-EF4``, in group 2) and
the background (``NVA-bkg``, in group 1) have the signatures

.. code-block:: text

    NVA-EF1           alt2_rset={...max_mag 6.8} alt2_rspl_132={0.05, 0.95}
                      alt2_rrow_132_scn1={b 0.8, rate 0.371113} alt2_dip=45.0
    ...
    NVA-bkg           alt2_rset={...max_mag 6.8} alt2_rspl_132={0.05, 0.95}
                      alt2_rrow_132_scn1={b 0.8, rate 0.371113} alt2_lsd=15.0

i.e. the four faults share one signature and the background has another
one, because the dip is modified for the faults and the lower
seismogenic depth for the background.

The consequence is that a realization can belong to more than one RateMap index (one per distinct signature of its sources): in this
case one index covers the background and another one the four faults.
The rates of such a realization are the sum of the columns of its
indices, i.e. it has more than one gid.

The uncertainties are applied to the sources in the workers, one index
at a time, by ``source_reader.modified_groups``; the correlated
branchsets are validated at build time instead
(``lt.check_correlated``), since the groups are still whole there.

Realizations per signature
~~~~~~~~~~~~~~~~~~~~~~~~~~

The signatures of a source can be inspected with the command
``oq show usignatures``; the ``num_rlzs`` column is explained in
:ref:`uncertainty-signatures`. In the sampled version
of the case (``R = 50``, see below) 5 of the 8 sources have
realization sets of different sizes, for instance the source
``NVA-EF1``

.. code-block:: text

    $ oq show usignatures
    | NVA-EF1             | 1, 1, 1, 1, 1, 1, 1, 2, 2 | alt2_rset             | (TE, west, central, 6.8)                                                                         |
    |                     |                        | alt2_rspl_132         | (0.05, 0.95), (0.15, 0.85)                                                                       |
    |                     |                        | alt2_rrow_132_scn1    | (0.8, 3.25, 0.371113)                                                                            |
    |                     |                        | alt2_dip              | 45.0                                                                                             |
    |                     |                        | alt2_rrow_132_scn2    | (0.8, 3.25, 0.371113)                                                                            |

i.e. the source has 11 realizations in 9 realization sets: seven sets of
size 1 and two sets of size 2. NB: the two
branchsets ``alt2_rrow_132_scn1`` and ``alt2_rrow_132_scn2`` carry the
*same* values (``b 0.8, ref_mag 3.25, rate 0.371113``), but a signature
is a tuple of ``(branchset id, value)`` pairs, so they are different
signatures.

For a given source the realization sets are disjoint and cover all its
realizations, so summing the ``num_rlzs`` gives the number of realizations
of the source and counting the sets gives its number of signatures; the
sets of *different* sources of the same group do overlap instead, since
a realization can have more than one RateMap index, as
explained above.

Full enumeration
~~~~~~~~~~~~~~~~

With ``number_of_logic_tree_samples = 0`` the logic tree has 144
realizations, i.e. the size of the logic tree is ``R = 144``::

    $ oq show composite_source_model
    | grp_id | trt | num_sources |
    |--------+-----+-------------|
    | 0      | NVA | 1           |
    | 1      | NVA | 1           |
    | 2      | NVA | 4           |
    | 3      | NVA | 1           |
    | 4      | NVA | 1           |

Each group has its own ``trt_smrs`` in the ``trt_smrs`` dataset
(56, 56, 128, 16, 16 entries) and its own RateMap indices in
``core_trt_smrs``, one per realization set, which here is one per
realization (144 in total): the realizations
of a group are *not* grouped together, since the
uncertainties of its sources differ from realization to realization.
The core size of the logic tree is therefore as large as the logic tree
itself, ``Gt = 144``, and the RateMap has shape ``(1, 6, 144)``:

.. code-block:: text

    realizations R                      144
    RateMap indices         144  (16 of size 1, 128 of size 2)
    core size Gt                        144
    RateMap                             (N=1, L=6, Gt=144) float32
    gids per realization                16 with 1, 128 with 2

The 16 realizations with a single gid are the 8 ``alt1`` and 8 ``alt1_AB``
realizations: those source models have only the background source
(``NVA-bkg`` and ``NVA-AB-bkg``), so all their sources have one
signature and there is a single gid.

Sampling
~~~~~~~~

The test case sets ``number_of_logic_tree_samples = 50``, i.e. it
samples 50 realizations out of the 144, which the engine reduces to
**24 effective source-model realizations** (``oq show sm_rlzs``), each
with ``samples`` realizations coming from the GMM logic tree (here a
single GMM, so ``samples`` counts the paths collapsed by the sampling):

.. code-block:: text

    realizations R                       50   (sampled out of 144)
    effective source-model realizations  24
    RateMap indices          27   (23 of size 1, 4 of size 2)
    core size Gt                         27
    RateMap                              (N=1, L=6, Gt=27) float32
    gids per realization                 42 with 1, 8 with 2

Now the core size ``Gt = 27`` is smaller than the size of the logic tree
``R = 50``, because some of the sampled realizations share the same set
of uncertainties: the four indices of size 2 contain two realizations
each.

Eight of the sampled realizations (38, 40, 41, 44, 45, 46, 47 and 48)
belong to two RateMap indices: e.g. the realization 40
belongs to the indices 7 and 8.

Checking a calculation
~~~~~~~~~~~~~~~~~~~~~~

The datasets involved are:

.. code-block:: text

    $ oq show trt_smrs          # the realizations of each source group
    $ oq show core_trt_smrs    # the realization sets
    $ oq show composite_source_model

The correspondence between the realizations and the columns of the
rates is available programmatically, together with the rates
themselves::

    >> from openquake.commonlib import datastore
    >> from openquake.calculators import getters
    >> ds = datastore.read(calc_id)
    >> full_lt = ds['full_lt'].init()
    >> req_gb, trt_rlzs, trt_smrs = getters.get_rmap_gb(ds, full_lt)
    >> len(trt_smrs), len(trt_rlzs)
    (27, 27)
    >> trt_rlzs[0]   # the realizations behind the first gid
    array([ 0,  1,  2, 38], dtype=uint32)

where each ``trt_rlzs[i]`` contains ``rlz + 2**24 * trti`` for the
realizations behind the gid ``i``, i.e. the values of the ``gid``
column of the stored contexts and of the ``_rates`` dataset.
