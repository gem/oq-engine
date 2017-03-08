from __future__ import division
from openquake.baselib import sap
from openquake.commonlib import datastore
from openquake.hazardlib.calc.filters import SourceFilter


@sap.Script
def plot_sites(calc_id):
    """
    Plot the sites and the bounding boxes of the sources, enlarged by
    the maximum distance
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
    from matplotlib.patches import Rectangle
    dstore = datastore.read(calc_id)
    sitecol = dstore['sitecol']
    csm = dstore['composite_source_model']
    oq = dstore['oqparam']
    rfilter = SourceFilter(sitecol, oq.maximum_distance)
    fig = p.figure()
    ax = fig.add_subplot(111)
    ax.grid(True)
    for src in csm.get_sources():
        llcorner, width, height = rfilter.get_rectangle(src)
        ax.add_patch(Rectangle(llcorner, width, height, fill=False))
    p.scatter(sitecol.lons, sitecol.lats, marker='+')
    p.show()

plot_sites.arg('calc_id', 'a computation id', type=int)
