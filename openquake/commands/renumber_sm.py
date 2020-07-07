import logging
import operator
import collections
from openquake.baselib import sap, parallel, general
from openquake.commonlib import logictree
from openquake.hazardlib import nrml


Source = collections.namedtuple('Source', 'id node value')


def read_sm(fname):
    srcs = []
    root = nrml.read(fname)
    if root['xmlns'] == 'http://openquake.org/xmlns/nrml/0.4':
        srcs.extend(root[0])
    else:
        for srcgroup in root[0]:
            srcs.extend(srcgroup)
    sources = [Source(src['id'], src, src.to_str()) for src in srcs]
    return root[0], fname, sources


@sap.Script
def renumber_sm(smlt_file):
    """
    Renumber the sources belonging to the same source model, even if split
    in multiple files, to avoid duplicated source IDs. NB: it changes the
    XML files in place, without making a backup, so be careful.
    """
    logging.basicConfig(level=logging.INFO)
    smpaths = logictree.collect_info(smlt_file).smpaths
    smap = parallel.Starmap(read_sm, [(path,) for path in smpaths])
    smodel, srcs = {}, []
    for sm, fname, sources in smap:
        smodel[fname] = sm
        srcs.extend(sources)
    dic = general.groupby(srcs, operator.attrgetter('id', 'value'))
    n = 1
    for sources in dic.values():
        for src in sources:
            src.node['id'] = str(n)
        n += 1
    for fname, sm in smodel.items():
        with open(fname, 'wb') as f:
            nrml.write([sm], f)


renumber_sm.arg('smlt_file', 'source model logic tree file')

if __name__ == '__main__':
    renumber_sm.callfunc()
