# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
This is an example with a source model logic tree containing uncertainties on
simple fault dip, and on incremental mfd. The GMPE is fixed as the Sadigh et
al. 1997 model.

The source model contains two simple faults: SFLT1 and SFLT2. SFLT1 has three
alternative MFD representations and three alternative dips (specified using
the relative dip option). SFLT2 has only one MFD, but three alternative
dips using the absolute dip option

27 curves output:
hazard_curve-smltp_b1_mfd1_high_dip_dip30-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd1_high_dip_dip45-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd1_high_dip_dip60-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd1_low_dip_dip30-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd1_low_dip_dip45-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd1_low_dip_dip60-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd1_mid_dip_dip30-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd1_mid_dip_dip45-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd1_mid_dip_dip60-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd2_high_dip_dip30-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd2_high_dip_dip45-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd2_high_dip_dip60-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd2_low_dip_dip30-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd2_low_dip_dip45-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd2_low_dip_dip60-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd2_mid_dip_dip30-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd2_mid_dip_dip45-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd2_mid_dip_dip60-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd3_high_dip_dip30-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd3_high_dip_dip45-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd3_high_dip_dip60-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd3_low_dip_dip30-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd3_low_dip_dip45-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd3_low_dip_dip60-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd3_mid_dip_dip30-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd3_mid_dip_dip45-gsimltp_Sad1997.csv
hazard_curve-smltp_b1_mfd3_mid_dip_dip60-gsimltp_Sad1997.csv
"""
