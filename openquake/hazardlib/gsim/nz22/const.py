# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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
from numpy import array

# correlation coefficients from AG20
periods_AG20 = array([
    0.01,
    0.02,
    0.03,
    0.05,
    0.075,
    0.10,
    0.15,
    0.2,
    0.25,
    0.3,
    0.4,
    0.5,
    0.6,
    0.75,
    1.0,
    1.5,
    2.0,
    2.5,
    3.0,
    4.0,
    5.0,
    6.0,
    7.5,
    10.0,
])

rho_Ws = array([
    1.0,
    0.99,
    0.99,
    0.97,
    0.95,
    0.92,
    0.9,
    0.87,
    0.84,
    0.82,
    0.74,
    0.66,
    0.59,
    0.5,
    0.41,
    0.33,
    0.3,
    0.27,
    0.25,
    0.22,
    0.19,
    0.17,
    0.14,
    0.1,
])

rho_Bs = array([
    1.0,
    0.99,
    0.99,
    0.985,
    0.98,
    0.97,
    0.96,
    0.94,
    0.93,
    0.91,
    0.86,
    0.8,
    0.78,
    0.73,
    0.69,
    0.62,
    0.56,
    0.52,
    0.495,
    0.43,
    0.4,
    0.37,
    0.32,
    0.28,
])

periods = array([
    0.0,
    0.02,
    0.05,
    0.075,
    0.1,
    0.15,
    0.2,
    0.25,
    0.3,
    0.4,
    0.5,
    0.6,
    0.75,
    1.0,
    1.5,
    2.0,
    2.5,
    3.0,
    4.0,
    5.0,
    6.0,
    7.5,
    10.0,
])

theta7s = array([
    1.0988,
    1.0988,
    1.2536,
    1.4175,
    1.3997,
    1.3582,
    1.1648,
    0.994,
    0.8821,
    0.7046,
    0.5799,
    0.5021,
    0.3687,
    0.1746,
    -0.082,
    -0.2821,
    -0.4108,
    -0.4466,
    -0.4344,
    -0.4368,
    -0.4586,
    -0.4433,
    -0.4828,
])

theta8s = array([
    -1.42,
    -1.42,
    -1.65,
    -1.8,
    -1.8,
    -1.69,
    -1.49,
    -1.3,
    -1.18,
    -0.98,
    -0.82,
    -0.7,
    -0.54,
    -0.34,
    -0.05,
    0.12,
    0.25,
    0.3,
    0.3,
    0.3,
    0.3,
    0.3,
    0.3,
])
