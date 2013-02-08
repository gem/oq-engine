# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
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


*******
Outputs
*******

* :ref:`Hazard Curves <hazard-curves>`
* :ref:`Hazard Maps <hazard-maps>`

.. _hazard-curves:

Hazard Curves
=============

Hazard Curves are discrete functions which describe probability of ground
motion exceedance in a given time frame. Hazard curves are composed of several
key elements:

* **Intensity Measure Levels (IMLs)** - IMLs define the x-axis values (or
  "ordinates") of the curve. IMLs are defined with an Intensity Measure Type
  (IMT) unit. IMLs are a `strictly monotonically increasing sequence`.
* **Probabilitites of Exceedance (PoEs)** - PoEs define the y-axis values, (or
  "abscissae") of the curve. For each node in the curve, the PoE denotes the
  probability that ground motion will exceedence a given level in a given time
  span.
* **Intensity Measure Type (IMT)** - The unit of measurement for the defined
  IMLs.
* **Investigation time** - The period of time (in years) for an earthquake
  hazard study. It is important to consider the investigation time when
  analyzing hazard curve results, because one can logically conclude that, the
  longer the time span, there is greater probability of ground motion exceeding
  the given values.
* **Spectral Acceleration (SA) Period** - Optional; used only if the IMT is SA.
* **Spectral Acceleration (SA) Damping** - Optional; used only if the IMT is
  SA.
* **Source Model Logic Tree Path (SMLT Path)** - The path taken through the
  calculation's source model logic tree. Does not apply to statistical curves,
  since these aggregate are computed over multiple logic tree realizations.
* **GSIM (Ground Shaking Intensity Model) Logic Tree Path (GSIMLT Path)** - The
  path take through the calculation's GSIM logic tree. As with the SMLT Path,
  this does not apply to statistical curves.

For a given calculation, hazard curves are computed for each logic tree
realization, each IMT/IML definition, and each geographical point of interest.
(In other words: If a calculation specifies 4 logic tree samples, a geometry
with 10 points of interest, and 3 IMT/IML definitions, 120 curves will be
computed.)

Another way to put it is:

``T = R * P * I``

where

* ``T`` is the total number of curves
* ``R`` is the total number of logic tree realizations
* ``P`` is the number of geographical points of interest
* ``I`` is the number of IMT/IML definitions

Hazard curves are grouped by IMT and realization (1 group per IMT per
realization). Each group includes 1 curve for each point of interest.

Statistical Curves
------------------

The classical hazard calculator is also capable of producing `mean` and
`quantile` curves. These aggregates are computed from the curves for a given
point and IMT over all logic tree realizations.

Similar to hazard curves for individual realizations, statistical hazard curves
are grouped by IMT and statistic type. (For quantiles, groups are separated by
quantile level.) Each group includes 1 curve for each point of interest.

Mean Curves
^^^^^^^^^^^

Mean hazard curves can be computed by specifying `mean_hazard_curves = true` in
the job configuration.

When computing a mean hazard curve for a given point/IMT, there are two
possible approaches:

1. mean, unweighted
2. mean, weighted

Technically, both approaches are "weighted". In the first approach, however,
the weights are `implicit` and are taken into account in the process of logic
tree sampling. This approach is used in the case of random Monte-Carlo logic
tree sampling. The total of number of logic tree samples is defined by the user
with the `number_of_logic_tree_samples` configuration parameter.

In the second approach, the weights are explicit in the
caluclation of the mean. This approach is used in the case of end-branch logic
tree enumeration, whereby each possible logic tree path is traversed. (Each
logic tree path in this case defines a weight.) The total number of logic tree
samples in this case is determined by the total number of possible tree paths.
(To perform end-branch enumeration, the user must specify
`number_of_logic_tree_samples = 0` in the job configuration.

The total number of mean curves calculated is

``T = P * I``

where

* ``T`` is the total number of curves
* ``P`` is the number of geographical points of interest
* ``I`` is the number of IMT/IML definitions

Quantile Curves
^^^^^^^^^^^^^^^

Quantile hazard curves can be computed by specifying one or more
`quantile_hazard_curves` values (for example,
`quantile_hazard_curves = 0.15, 0.85`) in the job configuration.

Similar to mean curves, quantiles curves can be produced for a given
point/IMT/quantile level (in the range [0.0, 1.0]), there are two possible
approaches:

1. quantile, unweighted
2. quantile, weighted

As with mean curves, `unweighted quantiles` are calculated when Monte-Carlo
logic tree sampling is used and `weighted quantiles` are calculated when logic
tree end-branch enumeration is used.

The total number of mean curves calculated is

``T = Q * P * I``

where

* ``T`` is the total number of curves
* ``Q`` is the number of quantile levels
* ``P`` is the number of geographical points of interest
* ``I`` is the number of IMT/IML definitions

.. _hazard-maps:

Hazard Maps
===========

Hazard maps are geographical meshes of intensity values. Intensity values are
extracted from hazard curve functions by interpolating at a given probability
exceedance. To put it another way, hazard maps seek to answer the following
question: "At the given level probability, what intensity level is likely to be
exceeded at a given geographical points in the next X years?"

The resulting geographical mesh is often depicted graphically, with a color key
defining which color to plot at the given location for a given value or range
values.

Hazard maps bear the same metadata as
:ref:`hazard curves <hazard-curves>`, with the addition of the
probability at which the hazard maps were computed.

For a given calulcation, hazard maps are computed for each hazard curve. Maps
can be computed for one or more probabilities of exceedance, so the total
number of hazard maps is

``T = C * E``

where

* ``T`` is the total number of maps
* ``C`` is the total number of hazard curves (see the method for calculating
  the :ref:`number of hazard curves <hazard-curves>`)
* ``E`` is the total number of probabilities of exceedance

Statistical Maps
----------------

Hazard maps can be produced from any set of hazard curves, including mean and
quantile aggregates. There are no special methods required for computing these
maps; the process is the same for all hazard map computation.
"""
