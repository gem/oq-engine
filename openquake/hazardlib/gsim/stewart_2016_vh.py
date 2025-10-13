# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
Module exports :class:`StewartEtAl2016VH`,
               :class:`StewartEtAl2016RegCHNVH`,
               :class:`StewartEtAl2016RegJPNVH`,
               :class:`StewartEtAl2016NoSOFVH`,
               :class:`StewartEtAl2016RegCHNNoSOFVH`,
               :class:`StewartEtAl2016RegJPNNoSOFVH`,
"""
from openquake.hazardlib.gsim import (
    bozorgnia_campbell_2016_vh, boore_2014, stewart_2016)
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class StewartEtAl2016VH(bozorgnia_campbell_2016_vh.BozorgniaCampbell2016VH):
    """
    Implements the SBSA15b GMPE by Stewart et al. (2016)
    vertical-to-horizontal ratio (V/H) for ground motions from the PEER
    NGA-West2 Project.

    This V/H model is combined from SBSA15 by Stewart et al. (2016) as the
    vertical model, and BSSA14 by Boore et al. (2014) as the horizontal model.

    Note that this is a more updated version than the GMPE described in the
    original PEER Report 2013/24.

    Reference:

    Stewart, J., Boore, D., Seyhan, E., & Atkinson, G. (2016). NGA-West2
    Equations for Predicting Vertical-Component PGA, PGV, and 5%-Damped PSA
    from Shallow Crustal Earthquakes. Earthquake Spectra, 32(2), 1005-1031.
    """
    VGMPE = stewart_2016.StewartEtAl2016()
    HGMPE = boore_2014.BooreEtAl2014()

    #: Supported tectonic region type is active shallow crust; see title.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground velocity and peak ground acceleration; see title.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the
    #: :attr:`~openquake.hazardlib.const.IMC.VERTICAL_TO_HORIZONTAL_RATIO`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = (
        const.IMC.VERTICAL_TO_HORIZONTAL_RATIO)

    #: Supported standard deviation types are inter-event, intra-event
    #: and total; see the section for "Aleatory Variability Model".
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are taken from the V and H models
    REQUIRES_SITES_PARAMETERS = (
        VGMPE.REQUIRES_SITES_PARAMETERS |
        HGMPE.REQUIRES_SITES_PARAMETERS)

    #: Required rupture parameters are taken from the V and H models
    REQUIRES_RUPTURE_PARAMETERS = (
        VGMPE.REQUIRES_RUPTURE_PARAMETERS |
        HGMPE.REQUIRES_RUPTURE_PARAMETERS)

    #: Required distance measures are taken from the V and H models
    REQUIRES_DISTANCES = (
        VGMPE.REQUIRES_DISTANCES |
        HGMPE.REQUIRES_DISTANCES)


class StewartEtAl2016RegCHNVH(StewartEtAl2016VH):
    """
    This class implements the Stewart et al. (2016) V/H model considering the
    correction to the path scaling term for High Q regions (e.g. China)
    """
    VGMPE = stewart_2016.StewartEtAl2016(region='CHN')
    HGMPE = boore_2014.BooreEtAl2014HighQ()


class StewartEtAl2016RegJPNVH(StewartEtAl2016VH):
    """
    This class implements the Stewart et al. (2016) V/H model considering the
    correction to the path scaling term for Low Q regions (e.g. Japan)
    """
    VGMPE = stewart_2016.StewartEtAl2016(region='JPN')
    HGMPE = boore_2014.BooreEtAl2014LowQ()


class StewartEtAl2016NoSOFVH(StewartEtAl2016VH):
    """
    The Stewart et al. (2016) V/H GMPE can consider the case in which the
    style-of-faulting is unspecified. In this case the GMPE is no longer
    dependent on rake.
    """
    VGMPE = stewart_2016.StewartEtAl2016(sof=False)
    HGMPE = boore_2014.BooreEtAl2014(sof=False)


class StewartEtAl2016RegCHNNoSOFVH(StewartEtAl2016RegCHNVH):
    """
    The Stewart et al. (2016) V/H GMPE, implemented for High Q regional
    datasets, (e.g. China) for the case in which the style-of-faulting is
    unspecified. In this case the GMPE is no longer
    dependent on rake.
    """
    VGMPE = stewart_2016.StewartEtAl2016(region='CHN', sof=False)
    HGMPE = boore_2014.BooreEtAl2014HighQ(sof=False)


class StewartEtAl2016RegJPNNoSOFVH(StewartEtAl2016RegJPNVH):
    """
    The Stewart et al. (2016) V/H GMPE, implemented for Low Q regional
    datasets, (e.g. Japan) for the case in which the style-of-faulting is
    unspecified. In this case the GMPE is no longer dependent on rake.
    """
    VGMPE = stewart_2016.StewartEtAl2016(region='JPN', sof=False)
    HGMPE = boore_2014.BooreEtAl2014LowQ(sof=False)
