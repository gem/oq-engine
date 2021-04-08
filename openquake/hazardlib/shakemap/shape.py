# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2021 GEM Foundation
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
import logging

SPEED_WARN = '''\
    To increase the speed with which the shapefile is parsed,'
    you can install the following package(s): %s'''


def shapefile_to_shakemap(files):
    try:
        import geopandas as gpd
        try:
            gpd.options.use_pygeos = True
        except ImportError:
            logging.warning(SPEED_WARN % 'pygeos')
    except ModuleNotFoundError:
        logging.warning(SPEED_WARN % 'geopandas, optionally: pygeos')
        return ShapelyShakemap(files)
    return GeoPandasShakemap(files)


class ShapelyShakemap():
    pass


class GeoPandasShakemap():
    pass
