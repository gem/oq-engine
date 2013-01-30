##################
Hazard Calculators
##################

*******
General
*******
.. automodule:: openquake.calculators.hazard.general

*************************
Classical PSHA Calculator
*************************
.. automodule:: openquake.calculators.hazard.classical.__init__

Classical PSHA Core
===================
.. automodule:: openquake.calculators.hazard.classical_core

Classical PSHA Post-Processing
==============================
.. automodule:: openquake.calculators.hazard.classical.post_processing
.. autofunction:: openquake.calculators.hazard.classical.post_processing.hazard_curves_to_hazard_map_task
.. autofunction:: openquake.calculators.hazard.classical.post_processing.do_post_process

***************************
Event-Based PSHA Calculator
***************************
.. automodule:: openquake.calculators.hazard.event_based.__init__

Event-Based Core
================
.. automodule:: openquake.calculators.hazard.event_based_core

Event-Based Post-Proccessing
============================
.. automodule:: openquake.calculators.hazard.event_based.post_processing

*******************
Scenario Calculator
*******************

The Scenario Siesmic Hazard Analysis (SSHA) approach allows calculation of
ground motion ﬁelds from a single earthquake rupture scenario taking
into account ground-motion aleatory variability.

*************************
Disaggregation Calculator
*************************

The Disaggregation approach allows calculating relative contribution to a seismic hazard level.
Contributions are defined in terms of latitude, longitude, magnitude, distance,
epsilon, and tectonic region type.

Sources:

* | Disaggregation of Seismic Hazard
  | by Paolo Bazzurro and C. Allin Cornell
  | Bulletin of the Seismological Society of America, 89, 2, pp. 501-520, April 1999
