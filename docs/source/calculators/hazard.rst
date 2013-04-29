##################
Hazard Calculators
##################

*******
General
*******
.. automodule:: openquake.engine.calculators.hazard.general

*************************
Classical PSHA Calculator
*************************
.. automodule:: openquake.engine.calculators.hazard.classical.__init__

Classical PSHA Core
===================
.. automodule:: openquake.engine.calculators.hazard.classical.core

Classical PSHA Post-Processing
==============================
.. automodule:: openquake.engine.calculators.hazard.classical.post_processing
.. autofunction:: openquake.engine.calculators.hazard.classical.post_processing.hazard_curves_to_hazard_map_task
.. autofunction:: openquake.engine.calculators.hazard.classical.post_processing.do_post_process

***************************
Event-Based PSHA Calculator
***************************
.. automodule:: openquake.engine.calculators.hazard.event_based.__init__

Event-Based Core
================
.. automodule:: openquake.engine.calculators.hazard.event_based.core

Event-Based Post-Proccessing
============================
.. automodule:: openquake.engine.calculators.hazard.event_based.post_processing

*******************
Scenario Calculator
*******************

The Scenario Siesmic Hazard Analysis (SSHA) approach allows calculation of
ground motion ﬁelds from a single earthquake rupture scenario taking
into account ground-motion aleatory variability.

*************************
Disaggregation Calculator
*************************

.. automodule:: openquake.engine.calculators.hazard.disaggregation.__init__
