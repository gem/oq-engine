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

import os
import sys
import time
from openquake.nrmllib.csvmanager import CSVManager, mkarchive


def create(convert, fname):
    t0 = time.time()
    try:
        out = convert(fname)
    except Exception as e:
        raise
        print e
        return
    dt = time.time() - t0
    print 'Created %s in %s seconds' % (out, dt)
    return out


def print_invalid(man, limit):
    invalid = man.find_invalid(limit)
    for inv in invalid:
        print inv
    if invalid:
        sys.exit('Found %d invalid records' % len(invalid))


def main(input, output=None):
    if input.endswith('.xml'):
        if not output:
            sys.exit('Please specify an output archive')
        name, _ = os.path.splitext(os.path.basename(input))
        csv = create(CSVManager(mkarchive(output, 'w'), name).
                     convert_from_nrml, input)
        print_invalid(csv, limit=None)
        return
    inp_archive = mkarchive(input, 'r+')
    csv = CSVManager(inp_archive, os.path.basename(input))
    print_invalid(csv, limit=None)
    out_archive = mkarchive(output, 'a') if output else inp_archive
    create(lambda n: csv.convert_to_nrml(out_archive), os.path.basename(input))


if __name__ == '__main__':
    # TODO: this is a preliminary version
    # once all requirements for the command-line script will be
    # collected more features will be added and a proper argparse
    # interface will be designed.
    # For the moment the scripts only accepts file names in input.
    main(*sys.argv[1:])
