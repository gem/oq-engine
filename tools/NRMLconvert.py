#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import sys
import time
from openquake.nrmllib.convert import (
    convert_nrml_to_zip, convert_zip_to_nrml, build_node)
from openquake.nrmllib.tables import FileTable, collect_tables


def collect(fnames):
    xmlfiles, zipfiles, csvmdatafiles, otherfiles = [], [],  [], []
    for fname in sorted(fnames):
        if fname.endswith('.xml'):
            xmlfiles.append(fname)
        elif fname.endswith('.zip'):
            zipfiles.append(fname)
        elif fname.endswith(('.csv', '.mdata')):
            csvmdatafiles.append(fname)
        else:
            otherfiles.append(fname)
    return xmlfiles, zipfiles, csvmdatafiles, otherfiles


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

    xmlfiles, zipfiles, csvmdatafiles, otherfiles = collect(fnames)
    for xmlfile in xmlfiles:
        create(convert_nrml_to_zip, xmlfile)

    for zipfile in zipfiles:
        create(convert_zip_to_nrml, zipfile)

    for name, group in collect_tables(FileTable, '.', csvmdatafiles):
        def convert_to_nrml(out):
            build_node(group, open(out, 'wb+'))
            return out
        create(convert_to_nrml, name + '.xml')

    if not xmlfiles and not zipfiles:
        sys.exit('Could not convert %s' % ' '.join(csvmdatafiles + otherfiles))


if __name__ == '__main__':
    # TODO: this is a preliminary version
    # once all requirements for the command-line script will be
    # collected more features will be added and a proper argparse
    # interface will be designed.
    # For the moment the scripts only accepts file names in input.
    main(*sys.argv[1:])
