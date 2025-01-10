# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2025 GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Module: openquake.hmtk.faults.fault_model implements the set of classes
to allow for a calculation of the magnitude frequency distribution from
the geological slip rate
"""
import numpy as np
from math import fabs

from openquake.hazardlib.scalerel import get_available_scalerel
from openquake.hazardlib.mfd.evenly_discretized import EvenlyDiscretizedMFD
from openquake.hmtk.models import IncrementalMFD
from openquake.hmtk.faults.fault_geometries import (
    SimpleFaultGeometry,
    ComplexFaultGeometry,
)
from openquake.hmtk.sources.simple_fault_source import mtkSimpleFaultSource
from openquake.hmtk.sources.complex_fault_source import mtkComplexFaultSource
from openquake.hmtk.faults import mfd


MFD_MAP = mfd.get_available_mfds()
SCALE_REL_MAP = get_available_scalerel()
DEFAULT_MSR_SIGMA = [(0.0, 1.0)]


def _update_slip_rates_with_aseismic(slip_rate, aseismic):
    """
    For all the slip rates in the slip rate tuple, multiply by the aseismic
    coefficient
    :param list slip_rate:
        List of tuples (Slip Value, Weight) defining the slip distribution
    :param float aseismic:
        Fractional proportion of slip release aseismically

    :returns:
        slip - List of tuples (Slip Value, Weight) for adjusted slip rates
    """

    return [
        (slip_val * (1.0 - aseismic), weight) for slip_val, weight in slip_rate
    ]


class RecurrenceBranch(object):
    """
    :class:`openquake.hmtk.faults.fault_model.RecurrenceBranch` is an object
    to store a set of parameters for recurrence calculations and the
    corresponding total weight

    :param str branch_id:
        Unique branch id
    :param float area:
        Fault area (km ^ 2)
    :param float slip:
        Fault slip rate (mm / yr)
    :param msr:
        Magnitude scaling relation as instance of
        :class: openquake.hazardlib.scale_rel.base.BaseASR
    :param float rake:
        Rake of fault (degrees)
    :param float shear_modulus:
        Shear modulus of fault (GPa)
    :param float disp_length_ratio:
        Displacement to length ratio of the fault
    :param float weight:
        Weight of recurrence model branch
    :param recurrence:
        Magnitude frquency distribution as instance of
        :class: openquake.hmtk.models.IncrementalMFD
    :param float max_mag:
        Maximum magnitude from the magnitude frequency distribution
    :param numpy.ndarray magnitudes:
        Magnitudes of MFD

    """

    def __init__(
        self,
        area,
        slip,
        msr,
        rake,
        shear_modulus,
        disp_length_ratio=None,
        msr_sigma=0.0,
        weight=1.0,
    ):
        self.branch_id = None
        self.area = area
        self.slip = slip
        self.msr = msr
        self.msr_sigma = msr_sigma
        self.rake = rake
        self.shear_modulus = shear_modulus
        self.disp_length_ratio = disp_length_ratio
        self.weight = weight
        self.recurrence = None
        self.max_mag = None
        self.magnitudes = None

    def update_weight(self, new_weight):
        """
        Updates the weight by multiplying by the new weight

        :param float new_weight:
            Weight to be multiplied by existing weight
        """
        self.weight = self.weight * new_weight

    def get_recurrence(self, config):
        """
        Calculates the recurrence model for the given settings as
        an instance of the openquake.hmtk.models.IncrementalMFD

        :param dict config:
            Configuration settings of the magnitude frequency distribution.
        """
        model = MFD_MAP[config["Model_Name"]]()
        model.setUp(config)
        model.get_mmax(config, self.msr, self.rake, self.area)
        model.mmax = model.mmax + (self.msr_sigma * model.mmax_sigma)
        # As the Anderson & Luco arbitrary model requires the input of the
        # displacement to length ratio

        if "AndersonLucoAreaMmax" in config["Model_Name"]:
            if not self.disp_length_ratio:
                # If not defined then default to 1.25E-5
                self.disp_length_ratio = 1.25e-5
            min_mag, bin_width, occur_rates = model.get_mfd(
                self.slip,
                self.area,
                self.shear_modulus,
                self.disp_length_ratio,
            )

        else:
            min_mag, bin_width, occur_rates = model.get_mfd(
                self.slip, self.area, self.shear_modulus
            )

        self.recurrence = IncrementalMFD(min_mag, bin_width, occur_rates)
        self.magnitudes = (
            min_mag
            + np.cumsum(bin_width * np.ones(len(occur_rates), dtype=float))
            - bin_width
        )
        self.max_mag = np.max(self.magnitudes)


class mtkActiveFault(object):
    """
    Main class to represent fault source

    :param int identifier:
        Identifier Code
    :param str name:
        Fault Name
    :param geometry:
        Instance of
        :class:`openquake.hmtk.faults.fault_model.SimpleFaultGeometry` or
        :class:`openquake.hmtk.faults.fault_model.ComplexFaultGeometry`
    :param list slip_rate:
        Slip rate (mm/yr) as list of tuples [(Value, Weight)]
    :param float aseismic:
        Aseismic slip coefficient
    :param float rake:
        Rake of the fault slip (degrees)
    :param neotectonic_fault:
        Instance of
        :class:`openquake.hmtk.faults.faulted_earth.NeotectonicFault`
    :param str trt:
        Tectonic region type
    :param scale_rel:
        Scaling relation as list of tuples [(:class:
        openquake.hazardlib.scalerel.base.BaseASR, Weight)]
    :param float aspect_ratio:
        Aspect ratio on fault
    :param tuple mfd:
        Tuple ([MFD], [Weight], [Scale_Rel]) defining the magnitude
        frequency distribution
    :param list shear_modulus:
        Shear Modulus (GPa) as list of tuples [(Value, Weight)]
    :param list disp_length_ratio:
        Displacement to length ratio as list of tuples [(Value, Weight)]
    :param list mfd_models:
        Magnitude frequency distributions as list of instances of :class:
        openquake.hmtk.faults.fault_model.RecurrenceBranch
    :param list mfd_models:
        Magnitude frequency distributions as list of instances of :class:
        openquake.hmtk.models.IncrementalMFD
    :param float area:
        Area of fault (km ^ 2)
    :param dict config:
        Dictionary of configuration paramters for magnitude freuency
        distribution calculation
    """

    def __init__(
        self,
        identifier,
        name,
        geometry,
        slip_rate,
        rake,
        trt,
        aseismic=0.0,
        msr_sigma=None,
        neotectonic_fault=None,
        scale_rel=None,
        aspect_ratio=None,
        shear_modulus=None,
        disp_length_ratio=None,
    ):
        """ """
        self.id = identifier
        self.name = name

        msr_sigma = msr_sigma or DEFAULT_MSR_SIGMA

        cond = not isinstance(
            geometry, SimpleFaultGeometry
        ) and not isinstance(geometry, ComplexFaultGeometry)
        if cond:
            msg = (
                "Geometry must be instance of "
                + "openquake.hmtk.faults.fault_geometries.BaseFaultGeometry"
            )
            raise IOError(msg)

        self.geometry = geometry
        self.aseismic = aseismic
        # Assert that the sum of the slip rates  is 1.0
        if fabs(np.sum([val[1] for val in slip_rate]) - 1.0) > 1e-7:
            raise ValueError("Slip rate weightings must sum to 1.0")
        self.slip = _update_slip_rates_with_aseismic(slip_rate, self.aseismic)

        self.rake = rake
        self.neotectonic_fault = neotectonic_fault
        self.trt = trt
        self.rupt_aspect_ratio = aspect_ratio
        self.mfd = ([], [], [])
        self.shear_modulus = shear_modulus
        self.disp_length_ratio = disp_length_ratio
        self.mfd_models = []
        self.msr = scale_rel
        self.msr_sigma = msr_sigma
        self.area = self.geometry.get_area()
        self.config = None
        self.regionalisation = None
        self.catalogue = None

    def get_tectonic_regionalisation(self, regionalisation, region_type=None):
        """
        Defines the tectonic region and updates the shear modulus,
        magnitude scaling relation and displacement to length ratio using
        the regional values, if not previously defined for the fault

        :param regionalistion:
            Instance of the :class:
            openquake.hmtk.faults.tectonic_regionalisaion.TectonicRegionalisation
        :param str region_type:
            Name of the region type - if not in regionalisation an error will
            be raised
        """
        if region_type:
            self.trt = region_type
        if self.trt not in regionalisation.key_list:
            raise ValueError(
                "Tectonic region classification missing or "
                "not defined in regionalisation"
            )

        for iloc, key_val in enumerate(regionalisation.key_list):
            if self.trt in key_val:
                self.regionalisation = regionalisation.regionalisation[iloc]

                # Update undefined shear modulus from tectonic regionalisation
                if not self.shear_modulus:
                    self.shear_modulus = self.regionalisation.shear_modulus
                # Update undefined scaling relation from tectonic
                # regionalisation
                if not self.msr:
                    self.msr = self.regionalisation.scaling_rel
                # Update undefined displacement to length ratio from tectonic
                # regionalisation
                if not self.disp_length_ratio:
                    self.disp_length_ratio = (
                        self.regionalisation.disp_length_ratio
                    )
                break
        return

    def select_catalogue(
        self,
        selector,
        distance,
        distance_metric="rupture",
        upper_eq_depth=None,
        lower_eq_depth=None,
    ):
        """
        Select earthquakes within a specied distance of the fault
        """
        if selector.catalogue.get_number_events() < 1:
            raise ValueError("No events found in catalogue!")

        # rupture metric is selected
        if "rupture" in distance_metric:
            # Use rupture distance
            self.catalogue = selector.within_rupture_distance(
                self.geometry.surface,
                distance,
                upper_depth=upper_eq_depth,
                lower_depth=lower_eq_depth,
            )
        else:
            # Use Joyner-Boore distance
            self.catalogue = selector.within_joyner_boore_distance(
                self.geometry.surface,
                distance,
                upper_depth=upper_eq_depth,
                lower_depth=lower_eq_depth,
            )

    def _generate_branching_index(self):
        """
        Generates a branching index (i.e. a list indicating the number of
        branches in each branching level. Current branching levels are:
        1) Slip
        2) MSR
        3) Shear Modulus
        4) DLR
        5) MSR_Sigma
        6) Config

        :returns:
            * branch_index - A 2-D numpy.ndarray where each row is a pointer
            to a particular combination of values
            * number_branches - Total number of branches (int)

        """
        branch_count = np.array(
            [
                len(self.slip),
                len(self.msr),
                len(self.shear_modulus),
                len(self.disp_length_ratio),
                len(self.msr_sigma),
                len(self.config),
            ]
        )
        n_levels = len(branch_count)
        number_branches = np.prod(branch_count)
        branch_index = np.zeros([number_branches, n_levels], dtype=int)
        cumval = 1
        dstep = 1e-9
        for iloc in range(0, n_levels):
            idx = np.linspace(
                0.0,
                float(branch_count[iloc]) - dstep,
                number_branches // cumval,
            )
            branch_index[:, iloc] = np.reshape(
                np.tile(idx, [cumval, 1]), number_branches
            )
            cumval *= branch_count[iloc]

        return branch_index.tolist(), number_branches

    def generate_config_set(self, config):
        """
        Generates a list of magnitude frequency distributions and renders as
        a tuple

        :param dict/list config:
            Configuration paramters of magnitude frequency distribution
        """
        if isinstance(config, dict):
            # Configuration list contains only one element
            self.config = [(config, 1.0)]
        elif isinstance(config, list):
            # Multiple configurations with correscponding weights
            total_weight = 0.0
            self.config = []
            for params in config:
                weight = params["Model_Weight"]
                total_weight += params["Model_Weight"]
                self.config.append((params, weight))
            if fabs(total_weight - 1.0) > 1e-7:
                raise ValueError(
                    "MFD config weights do not sum to 1.0 for "
                    "fault %s" % self.id
                )
        else:
            raise ValueError("MFD config must be input as dictionary or list!")

    def generate_recurrence_models(
        self, collapse=False, bin_width=0.1, config=None, rendered_msr=None
    ):
        """
        Iterates over the lists of values defining epistemic uncertainty
        in the parameters and calculates the corresponding recurrence model
        At present epistemic uncertainty is supported for: 1) slip rate,
        2) magnitude scaling relation, 3) shear modulus, 4) displacement
        to length ratio) and 5) recurrence model.

        :param list config:
            List of MFD model configurations
        :param bool collapse:
            Boolean flag indicating whether to collapse the logic tree branches
        :param float bin_width:
            If collapsing the logic tree branches the reference mfd must be
            defined. The minimum and maximum magnitudes are updated from the
            model, but the bin width must be specified here
        :param list/dict config:
            Configuration (or sets of configurations) of the recurrence
            calculations
        :param rendered_msr:
            If collapsing the logic tree branches a resulting magnitude
            scaling relation must be defined as instance of
            :class: openquake.hazardlib.scalerel.base.BaseASR
        """
        if collapse and not rendered_msr:
            raise ValueError(
                "Collapsing logic tree branches requires input "
                "of a single msr for rendering sources"
            )

        # Generate a set of tuples with corresponding weights
        if config is not None:
            self.generate_config_set(config)
        if not isinstance(self.config, list):
            raise ValueError(
                "MFD configuration missing or incorrectly " "formatted"
            )

        # Generate the branching index
        branch_index, _number_branches = self._generate_branching_index()
        mmin = np.inf
        mmax = -np.inf
        for idx in branch_index:
            tuple_list = []
            # Get slip
            tuple_list.append(self.slip[idx[0]])
            # Get msr
            tuple_list.append(self.msr[idx[1]])
            # Get shear modulus
            tuple_list.append(self.shear_modulus[idx[2]])
            # Get displacement length ratio
            tuple_list.append(self.disp_length_ratio[idx[3]])
            # Get msr sigma
            tuple_list.append(self.msr_sigma[idx[4]])
            # Get config
            tuple_list.append(self.config[idx[5]])
            # Calculate branch weight as product of tuple weights
            branch_weight = np.prod(np.array([val[1] for val in tuple_list]))
            # Instantiate recurrence model
            model = RecurrenceBranch(
                self.area,
                tuple_list[0][0],
                tuple_list[1][0],
                self.rake,
                tuple_list[2][0],
                tuple_list[3][0],
                tuple_list[4][0],
                weight=branch_weight,
            )
            model.get_recurrence(tuple_list[5][0])
            self.mfd_models.append(model)
            # Update the total minimum and maximum magnitudes for the fault
            if model.recurrence.min_mag < mmin:
                mmin = model.recurrence.min_mag
            if np.max(model.magnitudes) > mmax:
                mmax = np.max(model.magnitudes)
        if collapse:
            self.mfd = (
                [self.collapse_branches(mmin, bin_width, mmax)],
                [1.0],
                [rendered_msr],
            )
        else:
            mfd_mods = []
            mfd_wgts = []
            mfd_msr = []
            for model in self.mfd_models:
                mfd_mods.append(
                    IncrementalMFD(
                        model.recurrence.min_mag,
                        model.recurrence.bin_width,
                        model.recurrence.occur_rates,
                    )
                )
                mfd_wgts.append(model.weight)
                mfd_msr.append(model.msr)
            self.mfd = (mfd_mods, mfd_wgts, mfd_msr)

    def collapse_branches(self, mmin, bin_width, mmax):
        """
        Collapse the logic tree branches into a single IncrementalMFD

        :param float mmin:
            Minimum magnitude of reference mfd
        :param float bin_width:
            Bin width of reference mfd
        :param float mmax:
            Maximum magnitude of reference mfd

        :returns:
            :class: openquake.hmtk.models.IncrementalMFD
        """
        master_mags = np.arange(mmin, mmax + (bin_width / 2.0), bin_width)
        master_rates = np.zeros(len(master_mags), dtype=float)
        for model in self.mfd_models:
            id0 = np.logical_and(
                master_mags >= np.min(model.magnitudes) - 1e-9,
                master_mags <= np.max(model.magnitudes) + 1e-9,
            )
            # Use interpolation in log10-y values

            yvals = np.log10(model.recurrence.occur_rates)
            interp_y = np.interp(master_mags[id0], model.magnitudes, yvals)
            master_rates[id0] = master_rates[id0] + (
                model.weight * 10.0**interp_y
            )
        return IncrementalMFD(mmin, bin_width, master_rates)

    def generate_fault_source_model(self):
        """
        Creates a resulting `openquake.hmtk` fault source set.

        :returns:
            source_model - list of instances of either the :class:
            `openquake.hmtk.sources.simple_fault_source.mtkSimpleFaultSource`
            or :class:
            `openquake.hmtk.sources.complex_fault_source.mtkComplexFaultSource`
            model_weight - Corresponding weights for each source model
        """
        source_model = []
        model_weight = []
        for iloc in range(0, self.get_number_mfd_models()):
            model_mfd = EvenlyDiscretizedMFD(
                self.mfd[0][iloc].min_mag,
                self.mfd[0][iloc].bin_width,
                self.mfd[0][iloc].occur_rates.tolist(),
            )

            if isinstance(self.geometry, ComplexFaultGeometry):
                # Complex fault class
                source = mtkComplexFaultSource(
                    self.id,
                    self.name,
                    self.trt,
                    self.geometry.surface,
                    self.mfd[2][iloc],
                    self.rupt_aspect_ratio,
                    model_mfd,
                    self.rake,
                )
                source.fault_edges = self.geometry.trace
            else:
                # Simple Fault source
                source = mtkSimpleFaultSource(
                    self.id,
                    self.name,
                    self.trt,
                    self.geometry.surface,
                    self.geometry.dip,
                    self.geometry.upper_depth,
                    self.geometry.lower_depth,
                    self.mfd[2][iloc],
                    self.rupt_aspect_ratio,
                    model_mfd,
                    self.rake,
                )
                source.fault_trace = self.geometry.trace
            source_model.append(source)
            model_weight.append(self.mfd[1][iloc])
        return source_model, model_weight

    def get_number_mfd_models(self):
        """
        Returns the number of mfd models for a given fault model
        """
        return len(self.mfd[0])
