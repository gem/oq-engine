# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""
This module contains constants and some basic utilities and scaffolding to
assist with database interactions.
"""

# Tablespaces
HZRDI_TS = 'hzrdi'
ADMIN_TS = 'admin'
EQCAT_TS = 'eqcat'


# Table/column dicts.
# These can be used as a template for doing db inserts.
SIMPLE_FAULT = dict.fromkeys([
    # required:
    'owner_id', 'gid', 'dip', 'upper_depth', 'lower_depth', 'edge',
    # xor:
    'mfd_tgr_id', 'mgf_evd_id',
    # optional:
    'name', 'description', 'outline'])
SOURCE = dict.fromkeys([
    # required:
    'owner_id', 'simple_fault_id', 'gid', 'si_type', 'tectonic_region',
    # optional:
    'name', 'description', 'rake', 'hypocentral_depth', 'r_depth_distr_id',
    'input_id'])
MFD_EVD = dict.fromkeys([
    # required:
    'owner_id', 'magnitude_type', 'min_val', 'max_val', 'bin_size',
    'mfd_values',
    # optional:
    'total_cumulative_rate', 'total_moment_rate'])
MFD_TGR = dict.fromkeys([
    # required:
    'owner_id', 'magnitude_type', 'min_val', 'max_val', 'a_val', 'b_val',
    # optional:
    'total_cumulative_rate', 'total_moment_rate'])
