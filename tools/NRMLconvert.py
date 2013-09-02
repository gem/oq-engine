import sys
import time
import itertools
from openquake.nrmllib.convert import (
    convert_nrml_to_zip, convert_zip_to_nrml, build_node)
from openquake.nrmllib.readers import FileReader


def collect(fnames):
    xmlfiles, zipfiles, csvjsonfiles, otherfiles = [], [],  [], []
    for fname in sorted(fnames):
        if fname.endswith('.xml'):
            xmlfiles.append(fname)
        elif fname.endswith('.zip'):
            zipfiles.append(fname)
        elif fname.endswith(('.csv', '.json')):
            csvjsonfiles.append(fname)
        else:
            otherfiles.append(fname)
    return xmlfiles, zipfiles, csvjsonfiles, otherfiles


def create(factory, fname):
    t0 = time.time()
    try:
        out = factory(fname)
    except Exception as e:
        print e
        return
    dt = time.time() - t0
    print 'Created %s in %s seconds' % (out, dt)


def main(*fnames):
    if not fnames:
        sys.exit('Please provide some input files')

    xmlfiles, zipfiles, csvjsonfiles, otherfiles = collect(fnames)
    for xmlfile in xmlfiles:
        create(convert_nrml_to_zip, xmlfile)

    for zipfile in zipfiles:
        create(convert_zip_to_nrml, zipfile)

    for name, group in FileReader.getall('.', csvjsonfiles):
        def convert_to_nrml(out):
            build_node(group, open(out, 'wb+'))
            return out
        create(convert_to_nrml, name + '.xml')

    if not xmlfiles and not zipfiles:
        sys.exit('Could not convert %s' % ' '.join(csvjsonfiles + otherfiles))


if __name__ == '__main__':
    main(*sys.argv[1:])
