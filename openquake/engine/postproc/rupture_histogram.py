import numpy
from openquake.baselib import sap, parallel, performance
from openquake.hazardlib import contexts
from openquake.commonlib import datastore

def compute_hist(dstore, slc, cmaker, magbins, dstbins):
    with dstore:
        [ctx] = cmaker.read_ctxs(dstore, slc)
        magbin = numpy.searchsorted(magbins, ctx.mag)
        dstbin = numpy.searchsorted(dstbins, ctx.rrup)
        import pdb; pdb.set_trace()


def main(parent_id: int):
    """
    NB: this is meant to work only for parametric ruptures!
    """
    parent = datastore.read(parent_id)
    dstore, log = datastore.build_dstore_log(parent=parent)
    magbins = numpy.linspace(2, 10.2, 100)
    dstbins = contexts.sqrscale(0, 1000., 100)
    with dstore, log:
        cmakers = contexts.read_cmakers(dstore.parent)
        
        grp_ids = dstore.parent['rup/grp_id'][:]
        smap = parallel.Starmap(compute_hist, h5=dstore)
        for grp_id, slices in performance.get_slices(grp_ids).items():
            cmaker = cmakers[grp_id]
            for s0, s1 in slices:
                smap.submit((dstore, slice(s0, s1), cmaker, magbins, dstbins))

if __name__ == '__main__':
    sap.run(main)
