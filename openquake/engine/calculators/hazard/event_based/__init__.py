# -*- coding: utf-8 -*-
# Copyright (c) 2010-2014, GEM Foundation.
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
The Event-Based Probabilistic Seismic Hazard Analysis (ePSHA) approach
allows calculation of ground-motion ﬁelds from stochastic event sets.
Eventually, Classical PSHA results - such as hazard curves - can be obtained
by post-processing the set of computed ground-motion ﬁelds.


*******
Outputs
*******

* :ref:`Stochastic Event Sets (SES) <ses>`
* :ref:`Ground Motion Fields (GMF) <gmf>`, optionally produced from SESs
* :ref:`Hazard Curves <eb-hazard-curves>`, optionally produced from GMFs

.. _ses:

SESs
====

Stochastic Event Sets are collections of ruptures, where each rupture is
composed of:

* magnitude value
* tectonic region type
* source type (indicating whether the rupture originated from a point/area
  source or from a fault source)
* details of the rupture geometry (including  lat/lon/depth coordinates,
  strike, dip, and rake)

SES results are structured into 3-level hierarchy, consisting of SES
"Collections", SESs, and Ruptures. For each end-branch of a logic tree, 1 SES
Collection is produced. For each SES Collection, Stochastic Event Sets are
computed in a quantity equal to the calculation parameter
`ses_per_logic_tree_path`. Finally, each SES contains a number of ruptures, but
the quantity is more or less random. There are a few factors which determine
the production of ruptures:

* the Magnitude-Frequency Distribution (MFD) each seismic source considered
* investigation time
* random seed

From a scientific standpoint, the MFD for each seismic source defines the
rupture "occurrence rate". Combined with the investigation time (specified by
the `investigation_time` parameter), these two factors determine the
probability of rupture occurrence, and thus determine how many ruptures will
occur in a given calculation scenario.

From a software implementation standpoint, the random seed also affects rupture
generation. A "base seed" is specified by the user in the calculation
configuration file (using the parameter `random_seed`). When a calculation
runs, the total work is divided into small, independent asynchronous tasks.
Given the base seed, additional "task seeds" are generated and passed to each
task. Each task then uses this seed to control the random sampling which occurs
during the SES calculation. Structuring the calculation in this way guarantees
consistent, reproducible results regardless of the operating system, task
execution order, or architecture (32-bit or 64-bit).

.. _gmf:

GMFs
====

Event-Based hazard calculations always produce SESs and ruptures. The user can
choose to perform additional computation and produce Ground Motion Fields from
each computed rupture. (In typical use cases, a user of the event-based hazard
calculator will want to compute GMFs.)

GMF results are structured into a hierarchy very similar to SESs, consisting of
GMF "Collections", GMF "Sets", and GMFs. Each GMF Collection is directly
associated with an SES Collection, and thus with a logic tree realization.
Each GMF Set is associated with an SES. For each rupture in an SES, 1 GMF is
calculated for each IMT (Intensity Measure Type). (IMTs are defined by the
config parameter `intensity_measure_types`.) Finally, each GMF consists of
multiple "nodes", where each node is composed of longitude, latitude, and
ground motion values (GMV). The sites (lon/lat) of each GMF are defined by the
calculation geometry, which is specified by the `region` or `sites`
configuration parameters. (In other words, if the calculation geometry consists
of 10 points/sites, each computed GMF will include 10 nodes, 1 for each
location.)

.. _eb-hazard-curves:

Hazard Curves
=============

It is possible to produce hazard curves from GMFs (as an alternative to hazard
curve calculation method employed in the Classical hazard calculator. The user
can activate this calculation option by specifying
`hazard_curves_from_gmfs = true` in the configuration parameters. All hazard
curve post-processing options are available as well: `mean_hazard_curves`,
`quantile_hazard_curves`, and `poes` (for producing hazard maps).

Hazard curves are computed from GMFs as follows:

* For each logic tree realization, IMT, and location, there exist a number of
  hzrdr.gmf records exactly equal to the `ses_per_logic_tree_path` parameter.
  Each record contains an array with a number of ground motion values; this
  number is determined by the number of ruptures in a given stochastic event
  (which is random--see the section "SESs" above). All of these lists of GMVs
  are flattened into a single list of GMVs (the size of which is unknown,
  due the random element mentioned above).
* With this list of GMVs, a list of IMLs (Intensity Measure Levels) for the
  given IMT (defined in the configuration file as
  `intensity_measure_types_and_levels`), `investigation_time`, and "duration"
  (computed as `investigation_time` * `ses_per_logic_tree_path`), we compute
  the PoEs (Probabilities of Exceedance). See
  :func:`openquake.engine.calculators.hazard.event_based.\
post_processing.gmvs_to_haz_curve`
  for implementation details.
* The PoEs make up the "ordinates" (y-axis values) of the produced hazard
  curve. The IMLs define the "abscissae" (x-axis values).

As with the Classical calculator, it is possible to produce mean and quantile
statistical aggregates of curve results.

Hazard Maps
===========

The Event-Based Hazard calculator is capable of producing hazard maps for each
logic tree realization, as well as mean and quantile aggregates. This method of
extracting maps from hazard curves is identical to the Classical calculator.

See `hazard maps <#hazard-maps>`_ for more information.
"""
