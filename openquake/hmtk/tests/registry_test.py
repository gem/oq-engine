# -*- coding: utf-8 -*-
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
# 
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.
# -*- coding: utf-8 -*-


import unittest
import mock
from openquake.hmtk import registry


class Calculator(object):
    def calc(self, catalogue, config):
        return catalogue, config


def simple_calc(catalogue, param1, param2):
    return param1 + param2


class RegistryTestCase(unittest.TestCase):

    def test(self):
        reg = registry.CatalogueFunctionRegistry()
        reg.add('calc')(Calculator)
        catalogue, config = mock.Mock(), mock.Mock()

        self.assertEqual((catalogue, config),
                         reg['Calculator'](catalogue, config))

    def test_check_config(self):
        reg = registry.CatalogueFunctionRegistry()
        reg.add('calc', a_field=int, b_field=float)(Calculator)
        catalogue, config = mock.Mock(), {'a_field': 3}

        self.assertRaises(RuntimeError,
                          reg['Calculator'],
                          catalogue, config)

        config = {'a_field': 3, 'b_field': 1.0}
        self.assertEqual((catalogue, config),
                         reg['Calculator'](catalogue, config))

    def test_add_function(self):
        reg = registry.CatalogueFunctionRegistry()
        decorated = reg.add_function(param1=float, param2=int)(simple_calc)
        self.assertEqual(3, decorated(mock.Mock(), 1, 2))
        self.assertEqual(dict(param1=float, param2=int), decorated.fields)
