# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen, OGS
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.pfd.primary_surf_displ.base` defines abstract base
classes for :class:`BasePrimarySurfDispl <BasePrimarySurfDispl>` and
 :class:`BaseSecondarySurfDispl <BaseSecondarySurfDispl>`
"""

import abc


#: Recognised displacement *definitions* (which ruptures participate in the
#: displacement a model predicts), after the taxonomy of Sarmiento et al.
#: (2025, Earthquake Spectra, "Database for the Fault Displacement Hazard
#: Initiative Project", Table 1). There is NO conversion between definitions
#: (ibid.), so the tool never mixes them:
#:
#: - ``"principal"``        single-strand principal-fault displacement
#:                          (Sarmiento D_P,*);
#: - ``"sum-of-principal"`` displacement summed across the principal strands
#:                          crossed by a profile (Sarmiento D_SP,*);
#: - ``"aggregate"``        total displacement across principal AND
#:                          distributed ruptures in the measurement aperture
#:                          (Sarmiento D_AG,*) -- an aggregate-definition
#:                          principal-slot model already contains the
#:                          distributed contribution, so the hazard kernel
#:                          runs it as a SINGLE bucket and the secondary
#:                          slot is forbidden (FDLT-013);
#: - ``"distributed"``      off-fault (secondary/distributed) rupture
#:                          displacement only.
DISPLACEMENT_DEFINITIONS = ("principal", "sum-of-principal", "aggregate",
                            "distributed")

#: Recognised displacement (slip) *components*, i.e. the vector component a
#: model was regressed on (Sarmiento et al. 2025, Table 1 subscripts):
#: ``"vertical"`` (V), ``"lateral"`` (L, fault-parallel horizontal),
#: ``"net"`` (N/N*, resultant slip vector). Mixing components inside one
#: branch set is advisory-only (FDLT-105): unlike definitions, components
#: measure the same event differently rather than different events.
DISPLACEMENT_COMPONENTS = ("vertical", "lateral", "net")


class BasePrimarySurfDispl(metaclass=abc.ABCMeta):
    """Abstract base class for principal (primary) fault-displacement models.

    Subclasses implement :meth:`get_prob`, returning the probability that the
    principal displacement exceeds a given value (in metres).
    """

    #: Reference-line treatment this model needs when the source has no
    #: continuous fault trace (multiFaultSource / kite sections); one of
    #: 'lcp', 'ecs', 'segments'. Declarative, mirroring hazardlib's
    #: REQUIRES_DISTANCES pattern: the FDHA context maker computes the union
    #: of declared requirements once per rupture. Irrelevant for single-strand
    #: sources, whose trace is used directly.
    MULTIFAULT_REFERENCE_LINE = "lcp"

    #: Displacement definition this model was calibrated for; one of
    #: :data:`DISPLACEMENT_DEFINITIONS`. STATIC -- the class choice IS the
    #: definition: papers that publish several definitions get one model
    #: class per definition (e.g. ``Lavrentiadis2023PrimaryFD_aggregate`` [aggregate]
    #: vs ``Lavrentiadis2023PrimaryFD_principal`` [sum-of-principal],
    #: following the ``Petersen2011PrimaryFD_*`` variant idiom); no model
    #: parameter may change it. The default is ``"principal"`` (the classic
    #: single-strand principal-fault definition); every concrete model
    #: declares its own value with the source of the assignment in its
    #: class docstring. ``"aggregate"`` switches the hazard kernel to the
    #: single-bucket path (rate * P_sr * P_fd_aggregate * W_p, no distributed
    #: term) and forbids the secondary slot (docs/design/
    #: rupture_location_uncertainty.md, D8; validator FDLT-013).
    DISPLACEMENT_DEFINITION = "principal"

    #: Slip component this model predicts; one of
    #: :data:`DISPLACEMENT_COMPONENTS`. Metadata only (no routing effect);
    #: mixing components within one logic-tree branch set draws the advisory
    #: FDLT-105 warning.
    DISPLACEMENT_COMPONENT = "net"

    @abc.abstractmethod
    def get_prob(self):
        """
        Return the probability that the primary displacement will exceed
        a certain value [m]
        """

    def __str__(self):
        """
        Returns the name of the class
        """
        return self.__class__.__name__

    def __repr__(self):
        """
        Returns the name of the class in angular brackets
        """
        return "<%s>" % self.__class__.__name__


class BaseSecondarySurfDispl(metaclass=abc.ABCMeta):
    """Abstract base class for distributed (secondary) fault-displacement models.

    Subclasses implement :meth:`get_prob`, returning the probability that the
    distributed displacement exceeds a given value (in metres).
    """

    #: See BasePrimarySurfDispl.MULTIFAULT_REFERENCE_LINE.
    MULTIFAULT_REFERENCE_LINE = "lcp"

    #: Distributed-contribution pipeline the hazard kernel routes this model
    #: through; see BaseSecondarySurfRup.SECONDARY_PIPELINE. ``"generic"``
    #: (default) = adapter ``P(SR) x P(FD)``; ``"visini"`` = combined
    #: A/B/C + rank-2 Monte Carlo path. Declared on the class so the kernel
    #: never matches model names.
    SECONDARY_PIPELINE = "generic"

    #: Displacement definition (see :data:`DISPLACEMENT_DEFINITIONS`); every
    #: model in this slot predicts off-fault displacement, so the base-class
    #: default is ``"distributed"``.
    DISPLACEMENT_DEFINITION = "distributed"

    #: Slip component (see :data:`DISPLACEMENT_COMPONENTS`); concrete models
    #: declare their own value with its source in the class docstring.
    DISPLACEMENT_COMPONENT = "net"

    #: Declared applicability of the model's distance regression, in the
    #: model's OWN distance metric (the same one selected by
    #: :attr:`MULTIFAULT_REFERENCE_LINE`; e.g. Visini 2025 declares its range
    #: in the segments-r metric its regressions were fit on). ``None``
    #: (default) = no declared range. Otherwise a dict with any of:
    #:
    #: - ``'r_min_km'``:    inner edge of the calibration data;
    #: - ``'r_max_km'``:    outer edge, both walls;
    #: - ``'r_max_hw_km'`` / ``'r_max_fw_km'``: per-wall outer edges
    #:   (hanging wall = ``rx >= 0``, footwall = ``rx < 0``, the tool-wide
    #:   sign convention);
    #: - ``'source'``:      citation for the numbers (required).
    #:
    #: Used at run time for a once-per-model-per-run ``logging.warning``
    #: when sites are evaluated outside the range (extrapolation); it never
    #: changes results (the oq-pfdha hazard kernel).
    APPLICABILITY_RANGE = None

    #: Near-field regularisation for the distributed *displacement* evaluation,
    #: applied at the calc/ adapter boundary so model files stay paper-faithful.
    #: ``None`` (default) means no floor: bounded models (Takao exponential,
    #: Visini's own 5 m exclusion) leave this alone. ``"footprint_half"`` clamps
    #: the distance fed to the displacement regression to
    #: ``max(r, NEAR_FIELD_FLOOR_KM)`` -- a fixed 12.5 m (half a 25-m Petersen
    #: cell), hard-coded in model_adapter.py, deliberately independent of any
    #: occurrence cell size (pixel_size) -- a tool regularisation of Petersen
    #: (2011) eq.18's r -> 0 divergence (docs/design/
    #: rupture_location_uncertainty.md, decision D7).
    NEAR_FIELD_FLOOR = None

    @abc.abstractmethod
    def get_prob(self):
        """
        Return the probability that the secondary displacement will exceed
        a certain value [m]
        """

    def __str__(self):
        """
        Returns the name of the class
        """
        return self.__class__.__name__

    def __repr__(self):
        """
        Returns the name of the class in angular brackets
        """
        return "<%s>" % self.__class__.__name__