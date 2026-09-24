.. _probabilistic-fault-displacement:

Probabilistic Fault Displacement Calculator
============================================

Since version 3.27 the OpenQuake engine can compute probabilistic fault
displacement hazard (PFDHA), i.e. the hazard of permanent fault
displacement (in meters) at the surface, in addition to the classical
ground-shaking hazard. The calculation mode is ``displacement``.

While the classical calculators estimate the intensity of ground shaking
(PGA, spectral acceleration, ...) at a site, the displacement calculator
estimates the probability that the ground next to a fault is displaced
by more than a given amount in the next year. This is the quantity of
interest for the design of infrastructure that crosses active faults
(pipelines, roads, bridges) and for fault-rupture hazard maps.

How it works
-------------

The engine reads a standard fault source model (simple, complex or
multi-fault sources). For each rupture whose top edge reaches within
``surface_rupture_depth_tolerance_km`` of the surface, and for each
hazard site, it computes annual exceedance rates of displacement:

- the *principal* rate, for displacement on the fault trace itself,
  ``lambda_p = rate * P(SR) * P(D > d | SR) * W_p(r)``;
- the *distributed* rate, for displacement off the principal trace
  (distributed faulting), ``lambda_d = rate * P(SR) * P(D > d | SR, r) * G(r)``.

``P(SR)`` is the probability of surface rupture, ``P(D > d | ...)`` the
conditional probability of exceeding the displacement level ``d``,
``W_p(r)`` a rupture-location weight that accounts for the uncertainty
on the actual surface trace, and ``G(r)`` the distributed-rupture
weight. The faulting style (normal, reverse or strike-slip) of each
rupture is derived from its rake: normal for -150 <= rake <= -30,
reverse for 30 <= rake <= 150, strike-slip otherwise, and it is used
to select the models that apply to the source.

The PFD models are epistemic-regression models ported from the
`oq-pfdha <https://github.com/gem/oq-pfdha>`_ toolkit; the engine calls
them through the rate kernel in
:mod:`openquake.hazardlib.calc.displacement`. Unlike the ground-shaking
machinery there are no ground motion prediction equations (GMPEs): the
hazard levels are displacement thresholds in meters, and the output
rates are annual.

Inputs
-------

job.ini
*******

A displacement job.ini is like a classical one, with the following
differences:

- ``calculation_mode = displacement``
- ``pfd_logic_tree_file`` is mandatory and replaces
  ``gsim_logic_tree_file`` (the two are mutually exclusive)
- the intensity measure type is ``Disp`` and the levels are
  displacements in meters
- if ``maximum_distance`` is not given, the default is 10 km

The PFD-specific parameters are:

- ``r_sigma_km``: two-sided mapping-error sigma (km) for the Petersen
  et al. (2011) Gaussian rupture-location weight. 0 (the default)
  selects the boxcar/complementary split instead.
- ``r_threshold_km``: half-width (km) of the on-trace
  principal-displacement zone for the boxcar rupture-location weight
  (used when ``r_sigma_km == 0``). Default: 0.1.
- ``near_far_threshold_km``: distance (km) below which a site is in
  the Visini et al. (2025) distributed-faulting 'near' regime.
  Default: 0.2.
- ``surface_rupture_depth_tolerance_km``: a rupture contributes to
  the hazard only if its top edge reaches within this depth (km);
  deeper (buried) ruptures are skipped. Default: 0.01.

The standard statistics parameters work as in the classical
calculator: ``mean``, ``std``, ``max``, ``quantile_hazard_curves``,
and ``poes`` for the hazard maps.

The engine requires the site parameter ``vs30`` (a site model file or
the ``sites`` keyword argument, with the default value if not given).

PFD logic tree
**************

The PFD logic tree is an NRML ``<logicTree>`` file with up to five
branch sets, one per model slot:

- ``fdhaPrimarySRModel``: the principal surface-rupture probability
  model P(SR | M)
- ``fdhaPrimaryFDModel``: the principal displacement model
  P(D > d | SR, M, x/L)
- ``fdhaSecondarySRModel``: the distributed surface-rupture
  probability model P(D > 0 | M, r)
- ``fdhaSecondaryFDModel``: the distributed displacement model
  P(D > d | SR, M, r)
- ``fdhaCalcRSigma`` (optional): the value of ``r_sigma_km``, to be
  used as a calculation parameter inside the logic tree

The ``<uncertaintyModel>`` element is a model class name, optionally
followed by a TOML block of parameters, e.g.::

    <logicTreeBranch branchID="B2_PRIMARY_SURF_DISPL">
      <uncertaintyModel>
        [Youngs2003PrimaryFD]
        style = "normal"
        norm_disp_type = "AD"
      </uncertaintyModel>
      <uncertaintyWeight>1.0</uncertaintyWeight>
    </logicTreeBranch>

Branch sets can be conditional: the
``applyToBranches`` attribute limits a branch set to specific
upstream branches. The PFD logic tree is also *source-oriented*: a
branch set can carry the attributes ``applyToSources`` (a
comma-separated list of source IDs) and ``applyToStyle`` (normal,
reverse or strike-slip), so that different model combinations can be
applied to different sources or faulting styles. The total number of
realizations of a displacement calculation is the product of the
number of source model realizations and the number of paths of the
PFD logic tree.

Example
--------

The engine repository contains a set of worked examples in
``openquake/qa_tests_data/pfd``. The minimal case (``case_1``) is
composed of a single-site job, a simple-fault source and a one-branch
PFD logic tree. The job.ini is::

    [general]
    description = pfd case_1
    calculation_mode = displacement

    [geometry]
    sites = 16.16573727 39.64704451

    [erf]
    rupture_mesh_spacing = 2.0
    width_of_mfd_bin = 0.1

    [calculation]
    investigation_time = 1.0
    intensity_measure_types_and_levels = {"Disp": [0.0001, 0.001, 0.01, 0.1, 1.0]}
    r_threshold_km = 0.1
    pfd_logic_tree_file = pfd_logic_tree.xml
    source_model_logic_tree_file = source_model_logic_tree.xml

    [output]
    mean = true

and the PFD logic tree selects one model per slot::

    <logicTree logicTreeID="lt_fdha_hazard_curve_minimal">
      <logicTreeBranchSet branchSetID="bs_1" uncertaintyType="fdhaPrimarySRModel">
        <logicTreeBranch branchID="B1">
          <uncertaintyModel>
            [Youngs2003PrimarySR]
            style = "all"
          </uncertaintyModel>
          <uncertaintyWeight>1.0</uncertaintyWeight>
        </logicTreeBranch>
      </logicTreeBranchSet>
      <logicTreeBranchSet branchSetID="bs_2" uncertaintyType="fdhaPrimaryFDModel"
                          applyToBranches="B1">
        <logicTreeBranch branchID="B2">
          <uncertaintyModel>
            [Youngs2003PrimaryFD]
            style = "normal"
            norm_disp_type = "AD"
          </uncertaintyModel>
          <uncertaintyWeight>1.0</uncertaintyWeight>
        </logicTreeBranch>
      </logicTreeBranchSet>
      <logicTreeBranchSet branchSetID="bs_3" uncertaintyType="fdhaSecondarySRModel"
                          applyToBranches="B2">
        <logicTreeBranch branchID="B3">
          <uncertaintyModel>
            [Youngs2003SecondarySR]
            version = 3
            style = "all"
          </uncertaintyModel>
          <uncertaintyWeight>1.0</uncertaintyWeight>
        </logicTreeBranch>
      </logicTreeBranchSet>
      <logicTreeBranchSet branchSetID="bs_4" uncertaintyType="fdhaSecondaryFDModel"
                          applyToBranches="B3">
        <logicTreeBranch branchID="B4">
          <uncertaintyModel>
            [Youngs2003SecondaryFD]
            style = "normal"
          </uncertaintyModel>
          <uncertaintyWeight>1.0</uncertaintyWeight>
        </logicTreeBranch>
      </logicTreeBranchSet>
    </logicTree>

Running the calculation::

    $ oq engine --run job.ini
    ...
      id | name
    4882 | Full Report
    4883 | Hazard Curves
    4884 | Hazard Curves per Source

Outputs
--------

The displacement calculator produces the same kind of outputs as the
classical calculator, with displacement levels in place of intensity
measure levels:

- hazard curves: the annual exceedance rate of each displacement
  level for each site, stored as ``hcurves-stats`` (statistics over
  the realizations, e.g. the mean) and, when there is a single
  realization or ``individual_rlzs = true``, as ``hcurves-rlzs``.
  The export key is ``hcurves`` and produces files
  ``hazard_curve-<stat>-Disp_<id>.csv`` with one
  ``poe-<level>`` column per displacement level, e.g.::

      lon,lat,depth,poe-1.00000e-04,poe-1.00000e-03,poe-1.00000e-02,
      poe-1.00000e-01,poe-1.00000e+00
      16.16574,39.64704,0.00000,5.524193E-04,5.523678E-04,5.440485E-04,
      3.544071E-04,3.328750E-05

- hazard maps: set ``poes`` to get the displacement corresponding to
  each probability of exceedence; the export key is ``hmaps``
- per-source rates: the mean annual rate contributed by each source,
  as ``mean_rates_by_src`` (the export key is ``mean_rates_by_src``),
  useful to see which fault drives the hazard at a site
- source information: ``source_info`` and ``source_data`` tables with
  the number of contexts, ruptures and the computation time per
  source

The rates are annual rates of exceedence: with
``investigation_time = 1.0`` they can be used directly; with a
different investigation time the engine divides by it, as in the
classical calculator.

Caveats
--------

- only ruptures that break (almost) the surface contribute to the
  hazard: ruptures with a top edge deeper than
  ``surface_rupture_depth_tolerance_km`` are ignored, so the
  calculator is meant for active, shallow faulting sources
- the displacement models are empirical regressions calibrated on
  specific datasets and faulting styles (see the tables below); a
  model should be applied only to sources with a compatible
  faulting style
- aggregate-definition primary displacement models (e.g.
  ``Lavrentiadis2023PrimaryFD_aggregate``) already include the
  distributed contribution in the principal term, so the distributed
  bucket is not added on top of them
- some models (e.g. ``Chiou2025PrimaryFD``) require the fault trace
  to be smoothed with an expensive reference-line algorithm (ECS);
  the engine builds the smoothed line only if at least one model in
  the logic tree declares it, and uses the raw fault segments
  otherwise
- the calculation reuses the classical machinery: the ground
  motion context maker is driven by a no-op GMPE that declares the
  distances and site parameters needed by the PFD models

Underlying PFD models
----------------------

The four model slots are populated with empirical models ported from
oq-pfdha. The class name is the one to be used in the
``<uncertaintyModel>`` element of the PFD logic tree. The
displacement definition follows the taxonomy of Sarmiento et al.
(2025): *principal* is the displacement on the principal fault
strand, *sum-of-principal* is the slip summed over the principal
strands within a measurement aperture, *aggregate* is the total
displacement including distributed faulting, and *distributed* is
the off-trace displacement.

fdhaPrimarySRModel
******************

Models of the probability of principal surface rupture P(SR | M).

.. list-table::
   :header-rows: 1
   :widths: 28 40 20 28

   * - Model
     - Reference
     - Faulting style
     - Notes
   * - ``WC1993PrimarySR``
     - Wells & Coppersmith (1993), SRL 64(1), 54
     - all
     - magnitude-only logistic model
   * - ``Youngs2003PrimarySR``
     - Youngs et al. (2003), Earthq. Spectra 19(1)
     - ``style = "normal"`` or ``"all"``
     - normal-faulting subset or worldwide dataset
   * - ``MossRoss2011PrimarySR``
     - Moss & Ross (2011), BSSA 101(4)
     - reverse
     - 
   * - ``Moss2013PrimarySR``
     - Moss et al. (2013), SRL 84(3)
     - all
     - depends on the site vs30
   * - ``Takao2013PrimarySR``
     - Takao et al. (2013), JJAEE 9(2)
     - reverse, strike-slip
     - calibrated on Japanese earthquakes
   * - ``Pizza2023PrimarySR``
     - Pizza et al. (2023), BSSA 113(5)
     - all
     - coefficients per faulting style
   * - ``Yang2021PrimarySR``
     - Yang et al. (2021)
     - reverse
     - Australian stable continental region, 4 <= Mw <= 6.6
   * - ``Mammarella2024PrimarySR``
     - Mammarella et al. (2024)
     - all (from the rake)
     - uses the seismogenic thickness and a magnitude-scaling relation
   * - ``MammarellaEtAl2024PrimarySR``
     - Mammarella et al. (2024)
     - all
     - alias of ``Mammarella2024PrimarySR``
   * - ``FixedPrimarySR``
     - n/a
     - all
     - fixed probability, parameter ``value`` (default 1.0)

fdhaPrimaryFDModel
******************

Models of the probability of exceeding a principal displacement
threshold P(D > d | SR, M, x/L).

.. list-table::
   :header-rows: 1
   :widths: 30 40 20 28

   * - Model
     - Reference
     - Faulting style
     - Notes
   * - ``Youngs2003PrimaryFD``
     - Youngs et al. (2003), Earthq. Spectra 19(1)
     - normal
     - vertical component; parameter ``norm_disp_type`` = AD or MD
   * - ``MossRoss2011PrimaryFD``
     - Moss & Ross (2011), BSSA 101(4)
     - reverse
     - principal
   * - ``Takao2013PrimaryFD``
     - Takao et al. (2013), JJAEE 9(2)
     - reverse, strike-slip
     - principal; lognormal, parameter ``n_sigma``
   * - ``Petersen2011PrimaryFD``
     - Petersen et al. (2011), BSSA 101(2)
     - strike-slip
     - principal, lateral component
   * - ``Moss2022PrimaryFD``
     - Moss et al. (2022)
     - reverse
     - principal; AD or MD scaling
   * - ``Moss2024PrimaryFD``
     - Moss et al. (2024)
     - reverse
     - principal; parameter ``source`` (e.g. GIRS)
   * - ``Lavrentiadis2023PrimaryFD_principal``
     - Lavrentiadis & Abrahamson (2023), Earthq. Spectra 41(4)
     - normal, reverse, strike-slip
     - sum-of-principal
   * - ``Lavrentiadis2023PrimaryFD_aggregate``
     - Lavrentiadis & Abrahamson (2023), Earthq. Spectra 41(4)
     - normal, reverse, strike-slip
     - aggregate: includes the distributed contribution
   * - ``Kuehn2024PrimaryFD``
     - Kuehn et al. (2024)
     - normal, reverse, strike-slip
     - aggregate; optional epistemic sampling
   * - ``Chiou2025PrimaryFD``
     - Chiou et al. (2025)
     - strike-slip
     - sum-of-principal; requires the smoothed (ECS) reference line

fdhaSecondarySRModel
********************

Models of the probability of distributed surface rupture (i.e.
distributed displacement greater than zero) P(D > 0 | M, r).

.. list-table::
   :header-rows: 1
   :widths: 30 40 20 28

   * - Model
     - Reference
     - Faulting style
     - Notes
   * - ``Youngs2003SecondarySR``
     - Youngs et al. (2003), Earthq. Spectra 19(1)
     - all
     - parameter ``version``
   * - ``Petersen2011SecondarySR``
     - Petersen et al. (2011), BSSA 101(2)
     - strike-slip
     - parameter ``pixel_size`` (m)
   * - ``Petersen2011SecondarySR_default``
     - Petersen et al. (2011), BSSA 101(2)
     - strike-slip
     - default pixel size
   * - ``Takao2013SecondarySR``
     - Takao et al. (2013), JJAEE 9(2)
     - reverse, strike-slip
     - 
   * - ``Takao2014SecondarySR``
     - Takao et al. (2014)
     - reverse, strike-slip
     - 
   * - ``FerrarioLivio2021SecondarySR``
     - Ferrario & Livio (2021)
     - normal
     - 
   * - ``Rodriguez2023SecondarySR``
     - Rodriguez Padilla & Oskin (2023)
     - strike-slip
     - 
   * - ``Moss2022SecondarySR``
     - Moss et al. (2022)
     - reverse
     - parameter ``method``
   * - ``Visini2025SecondarySR``
     - Visini et al. (2025)
     - normal, reverse
     - combined A/B/C pipeline with ``Visini2025SecondaryFD``
   * - ``FixedSecondarySR``
     - n/a
     - all
     - fixed probability, parameter ``value`` (default 1.0)

fdhaSecondaryFDModel
********************

Models of the probability of exceeding a distributed displacement
threshold P(D > d | M, r).

.. list-table::
   :header-rows: 1
   :widths: 30 40 20 28

   * - Model
     - Reference
     - Faulting style
     - Notes
   * - ``Youngs2003SecondaryFD``
     - Youngs et al. (2003), Earthq. Spectra 19(1)
     - normal
     - vertical component
   * - ``Petersen2011SecondaryFD``
     - Petersen et al. (2011), BSSA 101(2)
     - strike-slip
     - lateral component
   * - ``Takao2013SecondaryFD``
     - Takao et al. (2013), JJAEE 9(2)
     - reverse, strike-slip
     - 
   * - ``Moss2022SecondaryFD``
     - Moss et al. (2022)
     - reverse
     - parameter ``method``
   * - ``Visini2025SecondaryFD``
     - Visini et al. (2025)
     - normal, reverse
     - combined A/B/C pipeline with ``Visini2025SecondarySR``

fdhaCalcRSigma
**************

The optional fifth branch set does not select a model: each branch
gives a value of the calculation parameter ``r_sigma_km``, so that
different realizations can be run with a different mapping-error
uncertainty. The branch value is the sigma in kilometers, e.g.::

    <logicTreeBranchSet branchSetID="bs_5" uncertaintyType="fdhaCalcRSigma">
      <logicTreeBranch branchID="B5A">
        <uncertaintyModel>0.5</uncertaintyModel>
        <uncertaintyWeight>0.5</uncertaintyWeight>
      </logicTreeBranch>
      <logicTreeBranch branchID="B5B">
        <uncertaintyModel>1.0</uncertaintyModel>
        <uncertaintyWeight>0.5</uncertaintyWeight>
      </logicTreeBranch>
    </logicTreeBranchSet>

The ``fdhaCalcRSigma`` branch set is mutually exclusive with the scalar
``r_sigma_km`` parameter in the job.ini file: if both are given the
engine raises an error.
