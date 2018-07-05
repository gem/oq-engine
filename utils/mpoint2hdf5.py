from openquake.baselib import hdf5, sap
from openquake.hazardlib import nrml, sourceconverter


@sap.Script
def multipoint2hdf5(fname):
    sc = sourceconverter.SourceConverter(
        area_source_discretization=10, width_of_mfd_bin=.1)
    sm = nrml.to_python(fname, sc)
    with hdf5.File(fname.replace('.xml', '.hdf5'), 'w') as f:
        for grp in sm:
            for src in grp:
                if hasattr(src, '__toh5__'):
                    print('saving', src)
                    f[src.source_id] = src


multipoint2hdf5.arg('fname', 'source model file in XML format')

if __name__ == '__main__':
    multipoint2hdf5.callfunc()
