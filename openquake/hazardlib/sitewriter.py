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
Site model XML Writer
"""

import os
from openquake.baselib.general import CallableDict
from openquake.baselib.node import Node, node_to_dict
from openquake.hazardlib import nrml

obj_to_node = CallableDict(lambda obj: obj.__class__.__name__)

def get_site_attributes(site):
    """
    Retrieves a dictionary of site attributes from the site class

    :param site:
        Site as instance of :class:
        `openquake.hazardlib.site.Site`
    :returns:
        Dictionary of site attributes
    """
    return {"lat": site.location.latitude,
            "lon": site.location.longitude,
            "depth": site.location.depth,
            "vs30": site.vs30,
            "vs30Type": "measured" if site.vs30measured else "inferred",
            "z1pt0": site.z1pt0,
            "z2pt5": site.z2pt5,
            "backarc": site.backarc}


@obj_to_node.add('Site')
def build_site_model(site):
    return Node('site', get_site_attributes(site))


# ##################### generic source model writer ####################### #

def write_site_model(dest, sites, name=None):
    """
    Writes a site model to XML.

    :param str dest:
        Destination path
    :param SiteCollection sites:
        Site collection object of class SiteCollection
    :param str name:
        Name of the site model (if missing, extracted from the filename)
    """
    name = name or os.path.splitext(os.path.basename(dest))[0]
    nodes = list(map(obj_to_node, sorted(sites)))
    source_model = Node("siteModel", {"name": name}, nodes=nodes)
    with open(dest, 'wb') as f:
        nrml.write([source_model], f, '%s')
    return dest


# usage: hdf5write(datastore.hdf5, csm)
def hdf5write(h5file, obj, root=''):
    """
    Write a generic object serializable to a Node-like object into a :class:
    `openquake.baselib.hdf5.File`
    """
    dic = node_to_dict(obj_to_node(obj))
    h5file.save(dic, root)
