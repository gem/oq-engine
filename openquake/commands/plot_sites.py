from __future__ import division
import logging
from openquake.baselib import sap, datastore
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.commonlib import readinput


@sap.Script
def plot_sites(calc_id=-1):
    """
    Plot the sites and the bounding boxes of the sources, enlarged by
    the maximum distance
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
    from matplotlib.patches import Rectangle
    logging.basicConfig(level=logging.INFO)
    dstore = datastore.read(calc_id)
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    srcfilter = SourceFilter(sitecol, oq.maximum_distance)
    csm = readinput.get_composite_source_model(oq).filter(srcfilter)
    fig = p.figure()
    ax = fig.add_subplot(111)
    ax.grid(True)
    for src in csm.get_sources():
        llcorner, width, height = srcfilter.get_rectangle(src)
        ax.add_patch(Rectangle(llcorner, width, height, fill=False))
    p.scatter(sitecol.lons, sitecol.lats, marker='+')
    p.show()

plot_sites.arg('calc_id', 'a computation id', type=int)
