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
from openquake.nrmllib.csvmanager import CSVManager, DirArchive, ZipArchive


def create(convert, fname):
    t0 = time.time()
    try:
        out = convert(fname)
    except Exception as e:
        print e
        return
    dt = time.time() - t0
    print 'Created %s in %s seconds' % (out, dt)


def main(inp_out):
    try:
        inp, out = inp_out
    except ValueError:
        sys.exit('Please provide both input and output')

    if out.endswith('.zip'):
        out_archive = ZipArchive(out, 'w')
    elif out != 'inplace':
        out_archive = DirArchive(out, 'w')

    fname = os.path.basename(inp)
    name, inp_ext = os.path.splitext(fname)
    outname, out_ext = os.path.splitext(out)

    if inp_ext == '.xml':
        man = CSVManager(out_archive, name)
        create(man.convert_from_nrml, inp)
    elif inp_ext == '.zip' or os.path.isdir(inp):
        if inp.endswith('.zip'):
            inp_archive = ZipArchive(inp, 'a')
        elif os.path.isdir(inp):
            inp_archive = DirArchive(inp)
        if out == 'inplace':
            create(lambda n: CSVManager(inp_archive, n).convert_to_nrml(),
                   name)
        else:
            raise SystemExit('Invalid output: %s; '
                             'expected "inplace"' % out)
    else:
        raise SystemExit('Invalid input: %s' % inp)


if __name__ == '__main__':
    # TODO: this is a preliminary version
    # once all requirements for the command-line script will be
    # collected more features will be added and a proper argparse
    # interface will be designed.
    # For the moment the scripts only accepts file names in input.
    main(sys.argv[1:])
