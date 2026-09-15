.. _multi-peril-risk-intro:

Multi-peril scenario damage
===========================

A multi-peril damage calculation evaluates primary ground shaking and one or
more earthquake-triggered secondary perils in the same scenario. For example,
the engine can calculate ground-shaking, landslide, and liquefaction damage to
the same assets and use the results in an infrastructure connectivity
analysis.

This workflow uses the normal ``scenario_damage`` calculation mode. It does
not use ``multi_risk``, which is a separate calculator retained for other
multi-hazard applications.

How the inputs fit together
---------------------------

A multi-peril calculation adds three relationships to a standard scenario
damage model:

1. ``secondary_perils`` selects the models that derive secondary intensity
   measures from the earthquake ground motions and site parameters.
2. A separate fragility file relates each peril's intensity measure to damage
   states.
3. The taxonomy mapping and, when used, the consequence model identify the
   peril to which each row applies.

The relevant parts of ``job.ini`` look like this:

.. code-block:: ini

   [general]
   calculation_mode = scenario_damage

   [site_params]
   site_model_file = site_model.csv

   [perils]
   secondary_perils = Jibson2007BLandslides,
       AllstadtEtAl2022Liquefaction

   [calculation]
   intensity_measure_types = PGA, PGV, SA(0.3)

   [exposure]
   exposure_file = exposure.xml
   taxonomy_mapping_csv = taxonomy_mapping.csv

   [fragility]
   groundshaking_fragility_file = {
       "structural": "fragility_groundshaking.xml"}
   landslide_fragility_file = {
       "structural": "fragility_landslide.xml"}
   liquefaction_fragility_file = {
       "structural": "fragility_liquefaction.xml"}

   [consequence]
   consequence_file = {'taxonomy': 'consequences.csv'}

The prefix of each fragility parameter is the peril name used throughout the
risk model. ``groundshaking`` is the primary peril. The secondary fragility
functions use the intensity measure produced by the selected secondary-peril
model; for example, the maintained demo uses ``Disp`` for landslides and
``LSE`` for liquefaction.

The taxonomy mapping needs one row for every applicable taxonomy and peril:

.. code-block:: csv

   taxonomy,risk_id,weight,peril
   bridge,bridge1,1,groundshaking
   bridge,bridge1,1,landslide
   bridge,bridge1,1,liquefaction

The ``risk_id`` must identify a function in the corresponding fragility
file. If consequences are required, their CSV rows use the same risk IDs and
perils:

.. code-block:: csv

   risk_id,consequence,peril,slight,moderate,extensive,complete
   bridge1,non_operational,groundshaking,0,0,1,1
   bridge1,non_operational,landslide,0,0,0,1
   bridge1,non_operational,liquefaction,0,0,0,1

See :ref:`secondary-perils` for the intensity measures and site parameters
required by each secondary-peril model. See :ref:`consequence-models` for the
complete consequence file format.

Consistency checks and modelling choices
-----------------------------------------

Before running the calculation, check that:

- every fragility model uses the same limit-state names in the same order;
- the ground-motion calculation includes all primary intensity measures
  needed by both the ground-shaking fragilities and secondary-peril models;
- each secondary fragility uses an intensity measure produced by its selected
  secondary-peril model;
- every applicable exposure taxonomy maps to a valid risk ID for each peril;
  and
- consequence rows, when supplied, cover the required risk IDs and perils.

Review warnings about secondary intensity measures being discarded below
``minimum_intensity``. A threshold that is too high can bias the damage
results.

Asset Risk Distributions and Asset Risk Statistics preserve the result for
each peril. Ground-shaking columns use names such as
``structural-complete``; secondary-peril columns are prefixed, for example
``landslide-structural-complete`` and
``liquefaction-structural-complete``.

For ``risk_by_event`` and the aggregate damage outputs, the engine composes
the per-peril damage distributions. For each damage-state exceedance
probability :math:`p_i`, the combined value is
:math:`1 - \prod_i (1 - p_i)`. Consequences are combined by taking the maximum
value across the perils for each asset and event. These are modelling
assumptions rather than a joint fragility model; assess whether they are
appropriate for the intended application. Infrastructure connectivity
analysis uses these composed event results.

Maintained example
------------------

The
`InfrastructureMultiPeril demo
<https://github.com/gem/oq-engine/tree/master/demos/risk/InfrastructureMultiPeril>`_
contains a complete ground-shaking, landslide, and liquefaction scenario for
a small road network. From a checkout of the engine repository, run it with:

.. code-block:: console

   oq engine --run demos/risk/InfrastructureMultiPeril/job.ini
   oq engine --list-outputs -1
   oq engine --export-outputs -1 results
