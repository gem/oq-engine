import numpy
from openquake.baselib import sap, parallel, performance, general
from openquake.hazardlib import contexts
from openquake.commonlib import datastore

def compute_hist(dstore, slc, cmaker, magbins, dstbins):
    dic = general.AccumDict(accum=0)  # (magi, dsti) -> counts
    with dstore:
        [ctxt] = cmaker.read_ctxs(dstore, slc)
        ctxt.magi = numpy.searchsorted(magbins, ctxt.mag)
        for magi in numpy.unique(ctxt.magi):
            ctx = ctxt[ctxt.magi == magi]
            dstbin = numpy.searchsorted(dstbins, ctx.rrup)
            d_idx, d_counts = numpy.unique(dstbin, return_counts=True)
            for dsti, counts in zip(d_idx, d_counts):
                dic[magi, dsti] += counts
    return dic


def main(parent_id: int, mbins=100, dbins=100):
    """
    NB: this is meant to work only for parametric ruptures!
    """
    parent = datastore.read(parent_id)
    dstore, log = datastore.build_dstore_log(parent=parent)
    magbins = numpy.linspace(2, 10.2, mbins)
    dstbins = contexts.sqrscale(0, 1000., dbins)
    with dstore, log:
        cmakers = contexts.read_cmakers(dstore.parent)
        grp_ids = dstore.parent['rup/grp_id'][:]
        dstore.swmr_on()
        smap = parallel.Starmap(compute_hist, h5=dstore)
        for grp_id, slices in performance.get_slices(grp_ids).items():
            cmaker = cmakers[grp_id]
            for s0, s1 in slices:
                smap.submit((dstore, slice(s0, s1), cmaker, magbins, dstbins))
        acc = smap.reduce()
        counts = numpy.zeros((mbins, dbins), int)
        for k, v in acc.items():
            counts[k] = v
        dstore['counts'] = counts
    assert counts.sum() == len(grp_ids)  # sanity check
    print('Counts saved in %s' % dstore)


if __name__ == '__main__':
    sap.run(main)
