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

The Classical Probabilistic Seismic Hazard Analysis (cPSHA) approach
allows calculation of hazard curves and hazard maps following the
classical integration procedure (**Cornell [1968]**, **McGuire [1976]**)
as formulated by **Field et al. [2003]**.

Sources:

* | Cornell, C. A. (1968).
  | Engineering seismic risk analysis.
  | Bulletin of the Seismological Society of America, 58:1583–1606.
* | Field, E. H., Jordan, T. H., and Cornell, C. A. (2003).
  | OpenSHA - A developing Community-Modeling
  | Environment for Seismic Hazard Analysis. Seism. Res. Lett., 74:406–419.
* | McGuire, K. K. (1976).
  | Fortran computer program for seismic risk analysis. Open-File report 76-67,
  | United States Department of the Interior, Geological Survey. 102 pages.

Classical PSHA Core
===================
.. automodule:: openquake.calculators.hazard.classical.core

***************************
Event-Based PSHA Calculator
***************************

The Event-Based Probabilistic Seismic Hazard Analysis (ePSHA) approach
allows calculation of ground-motion ﬁelds from stochastic event sets.
Eventually, Classical PSHA results - such as hazard curves - can be obtained
by post-processing the set of computed ground-motion ﬁelds.

Event-Based Core
================
.. automodule:: openquake.calculators.hazard.event_based.core

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

*********************************
Uniform Hazard Spectra Calculator
*********************************

UHS Core
========
.. automodule:: openquake.calculators.hazard.uhs.core

UHS Celery Tasks
================
.. autofunction:: compute_uhs_task
