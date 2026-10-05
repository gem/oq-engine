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
        applyToSources="alt2-NVA-bkg alt2-NVA-NVA-EF1 alt2-NVA-NVA-EF2
                        alt2-NVA-NVA-EF3 alt2-NVA-NVA-EF4"
        branchSetID="alt2_rset" uncertaintyType="recurSet">

Two features make these branchsets correlated:

- ``applyToBranches`` chains them, so that the ``recurRow`` values
  depend on the ``recurSet`` value and the ``rateSplit`` values depend
  on the ``recurRow`` values: the engine rejects a branchset referring to
  branches that do not exist;
- ``applyToSources`` lists *all* the sources that must be modified
  together, e.g. the background source ``alt2-NVA-bkg`` and the four
  faults ``alt2-NVA-NVA-EF1`` … ``EF4``, which is what guarantees that
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

Since the sources of a group are affected by *different* branchsets, a
group does **not** have a single signature: in the realization
``alt2/alt2_rs132/alt2_rspl_rs132_scn1/alt2_rs132_scn1_r00/alt2_dip45/
alt2_lsd15`` the sources of the group ``alt2-NVA`` have the signatures

.. code-block:: text

    alt2-NVA-NVA-EF1  alt2_rset={...max_mag 6.8} alt2_rspl_132={0.05, 0.95}
                      alt2_rrow_132_scn1={b 0.8, rate 0.371113} alt2_dip=45.0
    ...
    alt2-NVA-bkg      alt2_rset={...max_mag 6.8} alt2_rspl_132={0.05, 0.95}
                      alt2_rrow_132_scn1={b 0.8, rate 0.371113} alt2_lsd=15.0

i.e. the four faults share one signature and the background has another
one, because the dip is modified for the faults and the lower
seismogenic depth for the background.

The consequence is that the realizations of the group are split in
*indices of rate attribution* (one per distinct signature of the
sources), and since the sources of a group have different signatures, a
realization can belong to more than one index: in this case one index
covers the background and another one the four faults. The rates of such
a realization are the sum of the columns of its indices, i.e. it has
more than one gid.

The uncertainties are applied to the sources in the workers, one index
at a time, by ``source_reader.modified_groups``; the correlated
branchsets are validated at build time instead
(``lt.check_correlated``), since the groups are still whole there.

Full enumeration
~~~~~~~~~~~~~~~~

With ``number_of_logic_tree_samples = 0`` the logic tree has 144
realizations, i.e. the size of the logic tree is ``R = 144``::

    $ oq show composite_source_model
    | grp_id | trt | num_sources |
    |--------+-----+-------------|
    | 0      | NVA | 1           |
    | 1      | NVA | 1           |
    | 2      | NVA | 5           |
    | 3      | NVA | 5           |
    | 4      | NVA | 5           |
    | 5      | NVA | 5           |

Each group has its own ``trt_smrs`` in the ``trt_smrs`` dataset
(8, 8, 48, 48, 16, 16 realizations) and its own indices of rate
attribution in ``core_trt_smrs``, one per realization (8, 8, 48, 48, 16,
16): the realizations of a group are *not* grouped together, since the
uncertainties of its sources differ from realization to realization.
The core size of the logic tree is therefore as large as the logic tree
itself, ``Gt = 144``, and the RateMap has shape ``(1, 6, 144)``:

.. code-block:: text

    realizations R                      144
    indices of rate attribution         144  (16 of size 1, 128 of size 2)
    core size Gt                        144
    RateMap                             (N=1, L=6, Gt=144) float32
    gids per realization                16 with 1, 128 with 2

The 16 realizations with a single gid are the ones in which the dip and
the lower seismogenic depth coincide, so that the background and the
faults have the same signature.

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
    indices of rate attribution          27   (24 of size 1, 3 of size 2)
    core size Gt                         27
    RateMap                              (N=1, L=6, Gt=27) float32
    gids per realization                 44 with 1, 6 with 2

Now the core size ``Gt = 27`` is smaller than the size of the logic tree
``R = 50``, because some of the sampled realizations share the same set
of uncertainties: the three indices of size 2 contain two realizations
each.

Note that the sum of the sizes of the indices (30) is larger than the
number of ``trt_smrs`` (24): the six realizations with two gids (15, 16,
19, 20, 21, 22) are counted twice, once for the index of the background
and once for the index of the faults; e.g. the realization 15 belongs to
the indices 7 and 8, since the source ``alt2-NVA-bkg`` has one set of
uncertainties in it and the four faults another one.

Checking a calculation
~~~~~~~~~~~~~~~~~~~~~~

The datasets involved are:

.. code-block:: text

    $ oq show trt_smrs          # the realizations of each source group
    $ oq show core_trt_smrs    # the units of rate attribution
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
    array([ 0,  1, 12, ...], dtype=uint32)

where each ``trt_rlzs[i]`` contains ``rlz + 2**24 * trti`` for the
realizations behind the gid ``i``, i.e. the values of the ``gid``
column of the stored contexts and of the ``_rates`` dataset.
