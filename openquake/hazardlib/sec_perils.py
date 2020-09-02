# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import abc
import inspect


class SecondaryPeril(metaclass=abc.ABCMeta):
    @classmethod
    def instances(cls, oqparam):
        inst = []
        for clsname in oqparam.secondary_perils:
            c = globals()[clsname]
            lst = []
            for param in inspect.signature(c).parameters:
                lst.append(getattr(oqparam, param))
            inst.append(c(*lst))
        return inst

    outputs = abc.abstractproperty()

    @abc.abstractmethod
    def prepare(self, sites):
        """Add attributes to sites"""

    @abc.abstractmethod
    def compute(self, mag, gmfs, sites):
        # gmv is an array with (N, M) elements
        return gmfs[:, 0] * .1,  # fake formula

    def __repr__(self):
        return '<%s %s>' % self.__class__.__name__


class FakePeril(SecondaryPeril):
    outputs = ['fake']

    def prepare(self, sites):
        pass

    def compute(self, mag, gmfs, sites):
        # gmv is an array with (N, M) elements
        return gmfs[:, 0] * .1,  # fake formula


class NewarkDisplacement(SecondaryPeril):
    outputs = ['newark_disp', 'prob_disp']

    def __init__(self, c1=-2.71, c2=2.335, c3=-1.478, c4=0.424,
                 crit_accel_threshold=0.05):
        self.c1 = c1
        self.c2 = c2
        self.c3 = c3
        self.c4 = c4
        self.crit_accel_threshold = crit_accel_threshold

    def prepare(self, sites):
        sites.add_col('Fs', float, static_factor_of_safety(
            slope=sites.slope,
            cohesion=sites.cohesion_mid,
            friction_angle=sites.friction_mid,
            saturation_coeff=sites.saturation,
            soil_dry_density=sites.dry_density))
        sites.add_col('crit_accel', float,
                      newmark_critical_accel(sites.Fs, sites.slope))

    def compute(self, mag, gmfs, sctx):
        nd = newmark_displ_from_pga_M(
            gmfs[:, 0], sctx.critical_accel, mag,
            self.c1, self.c2, self.c3, self.c4, self.crit_accel_threshold)
        return nd, prob_failure_given_displacement(nd)


class HazusLiquefaction(SecondaryPeril):
    outputs = ['liq_prob']

    def __init__(self, map_proportion_flag):
        self.map_proportion_flag = map_proportion_flag

    def prepare(self, sites):
        pass

    def compute(self, mag, gmfs, sites):
        return hazus_liquefaction_probability(
            pga=gmfs[:, 0], mag=mag,
            liq_susc_cat=sites.liq_susc_cat,
            groundwater_depth=sites.gwd,
            do_map_proportion_correction=self.map_proportion_flag),


supported = [cls.__name__ for cls in SecondaryPeril.__subclasses__()]
