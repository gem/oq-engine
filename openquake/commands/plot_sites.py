from __future__ import division
import math
import numpy
from openquake.commonlib import sap, datastore
from openquake.hazardlib.site import Tile


def make_tiles(sitecol, sites_per_tile, maximum_distance):
    tiles = []
    hint = math.ceil(len(sitecol) / sites_per_tile)
    for sites in sitecol.split_in_tiles(hint):
        tiles.append(Tile(sites, maximum_distance))
    return tiles


@sap.Script
def plot_sites(calc_id):
    """
    Plot the hazard sites of a calculations with one ore more a bounding boxes
    (a box for each tile). If point sources are present, prints them too as
    circles of radius `integration_distance + max rupture radius`.
    """
    import matplotlib.pyplot as p
    from matplotlib.patches import Rectangle
    dstore = datastore.read(calc_id)
    sitecol = dstore['sitecol']
    csm = dstore['composite_source_model']
    oq = dstore['oqparam']
    fig = p.figure()
    ax = fig.add_subplot(111)
    ax.grid(True)
    tiles = make_tiles(sitecol, oq.sites_per_tile, oq.maximum_distance)
    print('There are %d tiles' % len(tiles))
    for tile in tiles:
        xs = []
        ys = []
        area = []
        for src in csm.get_sources():
            if src in tile and getattr(src, 'location', None):
                xs.append(src.location.x)
                ys.append(src.location.y)
                radius = src._get_max_rupture_projection_radius()
                r = (tile.maximum_distance[src.tectonic_region_type] +
                     radius) / tile.KM_ONE_DEGREE
                a = numpy.pi * r ** 2
                area.append(a)
        ax.add_patch(Rectangle(*tile.get_rectangle(), fill=False))
        p.scatter(tile.fix_lons(xs), ys, marker='o', s=area)
        p.scatter(tile.fix_lons(sitecol.lons), sitecol.lats, marker='+')
    p.show()

plot_sites.arg('calc_id', 'a computation id', type=int)
