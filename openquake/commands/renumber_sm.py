import logging
import operator
import collections
from openquake.baselib import parallel, general
from openquake.hazardlib import nrml, logictree


Source = collections.namedtuple('Source', 'node value')


def read_sm(fname):
    srcs = []
    root = nrml.read(fname)
    if root['xmlns'] == 'http://openquake.org/xmlns/nrml/0.4':
        srcs.extend(root[0])
    else:
        for srcgroup in root[0]:
            srcs.extend(srcgroup)
    sources = [Source(src, src.to_str()) for src in srcs]
    return root, fname, sources


def main(smlt_file):
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
    parallel.Starmap.shutdown()
    dic = general.groupby(srcs, operator.attrgetter('value'))
    n = 1
    for sources in dic.values():
        for src in sources:
            src.node['id'] = str(n)
        n += 1
    for fname, root in smodel.items():
        logging.info('Saving %s', fname)
        with open(fname, 'wb') as f:
            nrml.write(root, f, xmlns=root['xmlns'])


main.smlt_file = 'source model logic tree file'
