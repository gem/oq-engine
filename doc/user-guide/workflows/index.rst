.. _workflows:

Calculation Workflows
=====================

Hazard Calculators
------------------

The hazard component of the OpenQuake engine can compute seismic hazard using various approaches. Three types of 
analysis are currently supported:

- :ref:`classical-psha-intro`: *Classical Probabilistic Seismic Hazard Analysis (PSHA)*, allowing calculation of hazard curves and hazard maps following the classical integration procedure ((Cornell 1968), McGuire (1976)) as formulated by (Field, Jordan, and Cornell 2003).
- :ref:`event-based-psha-intro`: *Event-Based Probabilistic Seismic Hazard Analysis*, allowing calculation of ground-motion fields from stochastic event sets. Traditional results - such as hazard curves - can be obtained by post- processing the set of computed ground-motion fields.
- :ref:`scenario-hazard-intro`: *Scenario Based Seismic Hazard Analysis*, allowing the calculation of ground motion fields from a single earthquake rupture scenario taking into account ground motion aleatory variability. The ground motion fields can be conditioned to observed data, when available.
- :ref:`secondary-perils-intro`: *Secondary Perils Hazard Analysis*, allowing the calculation of probability of ground failure and induced displacements.

Each workflow has a modular structure, so that intermediate results can be exported and analyzed. Each calculator can be 
extended independently of the others so that additional calculation options and methodologies can be easily introduced, 
without affecting the overall calculation workflow.

Risk Calculators
----------------

The seismic risk results are calculated using the OpenQuake engine risk library, an open-source suite of tools for seismic risk 
assessment and loss estimation. This library is written in the Python programming language and available in the form of 
a “developers” release at the following location: `gem/oq-engine <https://github.com/gem/oq-engine/tree/engine-3.24/openquake/risklib>`_.

The risk component of the OpenQuake engine can compute both scenario-based and probabilistic seismic damage and risk 
using various approaches. The following types of analysis are currently supported:

- :ref:`scenario-damage-intro`: *Scenario Damage Assessment*, for the calculation of damage distribution statistics for a portfolio of buildings from a single earthquake rupture scenario taking into account aleatory and epistemic ground-motion variability.
- :ref:`scenario-risk-intro`: *Scenario Risk Assessment*, for the calculation of individual asset and portfolio loss statistics due to a single earthquake rupture scenario taking into account aleatory and epistemic ground-motion variability. Correlation in the vulnerability of different assets of the same typology can also be taken into consideration.
- :ref:`classical-damage-intro`: *Classical Probabilistic Seismic Damage Analysis*, for the calculation of damage state probabilities over a specified time period, and probabilistic collapse maps, starting from the hazard curves computed following the classical integration procedure ((Cornell 1968), McGuire (1976)) as formulated by (Field, Jordan, and Cornell 2003).
- :ref:`classical-risk-intro`: *Classical Probabilistic Seismic Risk Analysis*, for the calculation of loss curves and loss maps, starting from the hazard curves computed following the classical integration procedure ((Cornell 1968), McGuire (1976)) as formulated by (Field, Jordan, and Cornell 2003).
- :ref:`event-based-damage-intro`: *Stochastic Event Based Probabilistic Seismic Damage Analysis*, for the calculation of event damage tables starting from stochastic event sets. Other results such as damage-state-exceedance curves, probabilistic damage maps, and average annual damages or collapses can be obtained by post-processing the event damage tables.
- :ref:`event-based-risk-intro`: *Stochastic Event Based Probabilistic Seismic Risk Analysis*, for the calculation of event loss tables starting from stochastic event sets. Other results such as loss-exceedance curves, probabilistic loss maps, and average annual losses can be obtained by post-processing the event loss tables.
- :ref:`refrofit-benefit-cost-intro`: *Retrofit Benefit-Cost Ratio Analysis*, which is useful in estimating the net-present value of the potential benefits of performing retrofitting for a portfolio of assets (in terms of decreased losses in seismic events), measured relative to the upfront cost of retrofitting.
- :ref:`reinsurance-intro`: *Reinsurance Loss Analysis*, for the calculation of insurance and reinsuranced aggregated loss curves with different schemes (proportional and nonproportional treaties).
- :ref:`infrastructure-risk-intro`: *Infrastructure Risk Analysis*, for the calculation of infrastructure risk connectivity (functionality/operationality) at global and nodal level.


Each calculation workflow has a modular structure, so that intermediate results can be saved and analyzed. Moreover, 
each calculator can be extended independently of the others so that additional calculation options and methodologies can 
be easily introduced, without affecting the overall calculation workflow. Each workflow is described in more detail in 
the following sections.

.. toctree::
   :maxdepth: 1

   classical-psha
   event-based-psha
   scenario-hazard
   scenario-risk
   classical-risk
   event-based-risk
   refrofit-benefit-cost
   reinsurance
   infrastructure-risk
   secondary-perils
   
   

