from openquake.baselib import hdf5, sap
from openquake.hazardlib import nrml


@sap.Script
def multipoint2hdf5(fname):
    sm = nrml.to_python(fname)
    with hdf5.File(fname.replace('.xml', '.hdf5', 'w')) as f:
        for grp in sm:
            for src in grp:
                if src.__class__.__name__ == 'MultiPointSource':
                    f[src.source_id] = src


multipoint2hdf5.arg('fname', 'source model file in XML format')

if __name__ == '__main__':
    multipoint2hdf5.callfunc()
