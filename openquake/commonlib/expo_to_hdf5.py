# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025, GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
import operator
import pandas
import numpy
from openquake.baselib import hdf5, sap, general, performance
from openquake.baselib.parallel import Starmap
from openquake.hazardlib.geo.utils import geohash3
from openquake.commonlib.datastore import create_job_dstore
from openquake.risklib.asset import _get_exposure

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
B30 = (numpy.bytes_, 30)
CONV = {n: F32 for n in '''
BUILDINGS COST_CONTENTS_USD COST_NONSTRUCTURAL_USD
COST_STRUCTURAL_USD LATITUDE LONGITUDE OCCUPANTS_PER_ASSET
OCCUPANTS_PER_ASSET_AVERAGE OCCUPANTS_PER_ASSET_DAY
OCCUPANTS_PER_ASSET_NIGHT OCCUPANTS_PER_ASSET_TRANSIT
TOTAL_AREA_SQM'''.split()}
CONV['ASSET_ID'] = B30
for f in (None, 'ID_1', 'ID_2', 'NAME_1', 'NAME_2',
          'WFP_ID_1', 'WFP_ID_2', 'WFP_NAME_1', 'WFP_NAME_2'):
    CONV[f] = B30
TAGS = ['TAXONOMY', 'ID_0', 'ID_1', 'ID_2', 'NAME_1', 'NAME_2', 'OCCUPANCY']
IGNORE = set('NAME_0 SETTLEMENT TOTAL_REPL_COST_USD COST_PER_AREA_USD'.split())
FIELDS = {'TAXONOMY', 'COST_NONSTRUCTURAL_USD', 'LONGITUDE',
          'COST_CONTENTS_USD', 'ASSET_ID', 'OCCUPANCY',
          'OCCUPANTS_PER_ASSET', 'OCCUPANTS_PER_ASSET_AVERAGE',
          'OCCUPANTS_PER_ASSET_DAY', 'OCCUPANTS_PER_ASSET_NIGHT',
          'OCCUPANTS_PER_ASSET_TRANSIT', 'TOTAL_AREA_SQM',
          'BUILDINGS', 'COST_STRUCTURAL_USD', 'NAME_1', 'NAME_2',
          'LATITUDE', 'ID_0', 'ID_1', 'ID_2'}


def add_geohash3(array):
    """
    Add field "geohash3" to a structured array
    """
    if len(array) == 0:
        return ()
    dt = array.dtype
    dtlist = [('geohash3', U16)] + [(n, dt[n]) for n in dt.names]
    out = numpy.zeros(len(array), dtlist)
    for n in dt.names:
        out[n] = array[n]
        out['geohash3'] = geohash3(array['LONGITUDE'], array['LATITUDE'])
    return out


def fix(arr):
    # prepend the country to ASSET_ID and ID_1
    ID0 = arr['ID_0']
    ID1 = arr['ID_1']
    country = numpy.array(ID0, 'S3')
    arr['ASSET_ID'] = numpy.char.add(country, arr['ASSET_ID'])
    for i, (id0, id1) in enumerate(zip(ID0, ID1)):
        if not id1.startswith(id0):
            ID1[i] = country[i] + ID1[i]


def exposure_by_geohash(array, monitor):
    """
    Yields pairs (geohash, tempfname)
    """
    names = array.dtype.names
    array = add_geohash3(array)
    fix(array)
    for gh in numpy.unique(array['geohash3']):
        fname = general.gettemp(suffix='.hdf5')
        with hdf5.File(fname, 'w') as f:
            arr = array[array['geohash3']==gh]
            for name in names:
                f[name] = arr[name]
        yield gh, fname


def store_tagcol(dstore, tagname, tagvalues):
    """
    A TagCollection is stored as arrays like taxonomy = [
    "?", "Adobe", "Concrete", "Stone-Masonry", "Unreinforced-Brick-Masonry",
    "Wood"] with attributes __pyclass__, tagnames, tagsize
    """
    tagsizes = []
    tagnames = []
    mon = performance.Monitor(h5=dstore)

    name = 'taxonomy' if tagname == 'TAXONOMY' else tagname
    tagnames.append(name)
    with mon('unique tags', savemem=True):
        uvals, inv = numpy.unique(tagvalues, return_inverse=1)
    size = len(uvals) + 1
    tagsizes.append(size)
    logging.info('Storing %s[%d/%d]', tagname, size, len(inv))
    hdf5.extend(dstore[f'assets/{tagname}'], inv + 1)  # indices from 1
    vals = numpy.concatenate([[b'?'], uvals])
    dset = dstore.create_dset(
        'tagcol/' + name, hdf5.vstr, len(vals), 'gzip')
    dset[:] = [x.decode('utf8') for x in vals]
    return size


# in parallel
def gen_tasks(files, wfp, sample_assets, monitor):
    """
    Generate tasks of kind exposure_by_geohash for large files
    """
    for file in files:
        # read CSV in chunks
        usecols = file.fields | ({'ID_2'} if file.admin2 else set())
        dfs = pandas.read_csv(
            file.fname, names=file.header, dtype=CONV,
            usecols=usecols, skiprows=1, chunksize=1_000_000)
        nrows = 0
        for i, df in enumerate(dfs):
            if sample_assets:
                df = general.random_filter(df, float(sample_assets))
            if len(df) == 0:
                continue
            if wfp:
                for col in df.columns:
                    if col.startswith('WFP_'):
                        # i.e. overwrite ID_1 with WFP_ID_1
                        df[col[4:]] = df.pop(col)
            nrows += len(df)
            if 'ID_1' not in df.columns:  # happens for many islands
                df['ID_1'] = '???'
            if 'ID_2' not in df.columns:  # happens for many contries
                df['ID_2'] = df['ID_1']
            if 'NAME_2' not in df.columns:  # happens in Taiwan
                df['NAME_2'] = df['NAME_1']
            elif wfp:  # work around bad exposures with ID_2 ending with ".0"
                df['ID_2'] = [x[:-2] if x.endswith(b'.0') else x
                              for x in df['ID_2']]
            dt = hdf5.build_dt(CONV, df.columns, file.fname)
            array = numpy.zeros(len(df), dt)
            for col in df.columns:
                arr = df[col].to_numpy()
                if len(arr) and hasattr(arr[0], 'encode'):
                    array[col] = [x.encode('utf8') for x in arr]
                else:
                    array[col] = arr
            if i == 0:
                yield from exposure_by_geohash(array, monitor)
            else:
                yield exposure_by_geohash, array
        print(os.path.basename(file.fname), nrows)


def keep_wfp(csvfile):
    return any(col.startswith('WFP_') for col in csvfile.header)


def store(exposures_xml, wfp, dstore, h5tmp):
    """
    Store the given exposures in the datastore
    """
    csvfiles = []
    for xml in exposures_xml:
        exposure, _ = _get_exposure(xml)
        csvfiles.extend(exposure.datafiles)
    files = hdf5.sniff(csvfiles, ',', IGNORE,
                       keep=keep_wfp if wfp else lambda csvfile: True)
    if wfp:
        files = [f for f in files if any(field.startswith('WFP_')
                                         for field in f.header)]
    commonfields = sorted({'ID_2', 'NAME_2'} | files[0].fields & FIELDS)
    dtlist = [(t, U32) for t in TAGS] + \
        [(f, F32) for f in set(CONV)-set(TAGS)-{'ASSET_ID', None}] + \
        [('ASSET_ID', B30)]
    for name, dt in dtlist:
        logging.info('Creating assets/%s', name)
    dstore['exposure'] = exposure
    for name, dt in dtlist:
        hdf5.create(dstore.hdf5, f'assets/{name}', dt,
                    compression='gzip' if name in TAGS else None)
    slc_dt = numpy.dtype([('gh3', U16), ('start', U32), ('stop', U32)])
    dstore.create_dset('assets/slice_by_gh3', slc_dt)
    dstore.swmr_on()
    sa = os.environ.get('OQ_SAMPLE_ASSETS')
    smap = Starmap.apply(gen_tasks, (files, wfp, sa),
                         weight=operator.attrgetter('size'), h5=dstore.hdf5)
    num_assets = 0
    for tagname in TAGS:
        hdf5.create(h5tmp, tagname, hdf5.vstr)
    pairs = list(smap)
    Starmap.shutdown()
    logging.info('Building name2dic and slice_by_gh3')
    name2dic = {b'?': b'?'}
    for gh3, fname in pairs:
        with hdf5.File(fname, 'r') as f:
            id2 = f['ID_2'][:]
            name2 = f['NAME_2'][:]
            name2dic.update(zip(id2, name2))
        n = len(id2)
        slc = numpy.array(
            [(gh3, num_assets, num_assets + n)], slc_dt)
        hdf5.extend(dstore['assets/slice_by_gh3'], slc)
        num_assets += n

    tagsizes = []
    logging.info('Storing assets/indices')
    for name in commonfields:
        arrays = []
        for gh3, fname in pairs:
            with hdf5.File(fname, 'r') as f:
                arr = f[name][:]
                if name in TAGS:
                    arrays.append(arr)
                else:
                    hdf5.extend(dstore['assets/' + name], arr)
        if name in TAGS:
            size = store_tagcol(dstore, name, numpy.concatenate(arrays))
            tagsizes.append(size)
    for gh3, fname in pairs:
        os.remove(fname)
    dic = dict(__pyclass__='openquake.risklib.asset.TagCollection',
               tagnames=numpy.array(TAGS, hdf5.vstr),
               tagsizes=tagsizes)
    dstore.getitem('tagcol').attrs.update(dic)
    ID2s = dstore['tagcol/ID_2'][:]
    dstore.create_dset('NAME_2', hdf5.vstr, len(ID2s))[:] = [
        name2dic[id2].decode('utf8') for id2 in ID2s]

    # sanity check
    for name in commonfields:
        n = len(dstore['assets/' + name])
        assert n == num_assets, (name, n, num_assets)

    logging.info('Stored {:_d} assets in {}'.format(n, dstore.filename))


def main(exposures_xml, wfp=False):
    """
    An utility to convert an exposure from XML+CSV format into HDF5.
    NB: works only for the exposures of the global risk model, having
    field names like LONGITUDE, LATITUDE, etc
    """
    log, dstore = create_job_dstore()
    with dstore, log, hdf5.File(dstore.tempname, 'w') as h5tmp:
        store(exposures_xml, wfp, dstore, h5tmp)
    os.remove(dstore.tempname)
    return dstore.filename

main.exposures_xml = dict(help='Exposure pathnames', nargs='+')


if __name__ == '__main__':
    # python -m openquake.commonlib.expo_to_hdf5 exposure.xml
    sap.run(main)
