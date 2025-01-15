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
import h5py
from openquake.baselib import hdf5, sap, general
from openquake.baselib.parallel import Starmap
from openquake.hazardlib.geo.utils import geohash3
from openquake.commonlib.datastore import create_job_dstore
from openquake.risklib.asset import _get_exposure

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
CONV = {n: F32 for n in '''
BUILDINGS COST_CONTENTS_USD COST_NONSTRUCTURAL_USD
COST_STRUCTURAL_USD LATITUDE LONGITUDE OCCUPANTS_PER_ASSET
OCCUPANTS_PER_ASSET_AVERAGE OCCUPANTS_PER_ASSET_DAY
OCCUPANTS_PER_ASSET_NIGHT OCCUPANTS_PER_ASSET_TRANSIT
TOTAL_AREA_SQM'''.split()}
CONV['ASSET_ID'] = (numpy.bytes_, 24)
for f in (None, 'ID_1'):
    CONV[f] = str
TAGS = {'TAXONOMY': [], 'ID_0': [], 'ID_1': [], 'OCCUPANCY': []}
IGNORE = set('NAME_0 NAME_1 SETTLEMENT TOTAL_REPL_COST_USD COST_PER_AREA_USD'
             .split())
FIELDS = {'TAXONOMY', 'COST_NONSTRUCTURAL_USD', 'LONGITUDE',
          'COST_CONTENTS_USD', 'ASSET_ID', 'OCCUPANCY',
          'OCCUPANTS_PER_ASSET', 'OCCUPANTS_PER_ASSET_AVERAGE',
          'OCCUPANTS_PER_ASSET_DAY', 'OCCUPANTS_PER_ASSET_NIGHT',
          'OCCUPANTS_PER_ASSET_TRANSIT', 'TOTAL_AREA_SQM',
          'BUILDINGS', 'COST_STRUCTURAL_USD',
          'LATITUDE', 'ID_0', 'ID_1'}


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
    arr['ASSET_ID'] = numpy.char.add(numpy.array(ID0, 'S3'), arr['ASSET_ID'])
    for i, (id0, id1) in enumerate(zip(ID0, ID1)):
        if not id1.startswith(id0):
            ID1[i] = '%s-%s' % (id0, ID1[i])


def exposure_by_geohash(array, monitor):
    """
    Yields pairs (geohash, array)
    """
    array = add_geohash3(array)
    fix(array)
    for gh in numpy.unique(array['geohash3']):
        yield gh, array[array['geohash3']==gh]


def store_tagcol(dstore):
    """
    A TagCollection is stored as arrays like taxonomy = [
    "?", "Adobe", "Concrete", "Stone-Masonry", "Unreinforced-Brick-Masonry",
    "Wood"] with attributes __pyclass__, tagnames, tagsize
    """
    tagsizes = []
    tagnames = []
    for tagname in TAGS:
        name = 'taxonomy' if tagname == 'TAXONOMY' else tagname
        tagnames.append(name)
        tagvalues = numpy.concatenate(TAGS[tagname])
        uvals, inv, counts = numpy.unique(
            tagvalues, return_inverse=1, return_counts=1)
        size = len(uvals) + 1
        tagsizes.append(size)
        logging.info('Storing %s[%d/%d]', tagname, size, len(inv))
        hdf5.extend(dstore[f'assets/{tagname}'], inv + 1)  # indices start from 1
        dstore['tagcol/' + name] = numpy.concatenate([['?'], uvals])
        if name == 'ID_0':
            dtlist = [('country', (numpy.bytes_, 3)), ('counts', int)]
            arr = numpy.empty(len(uvals), dtlist)
            arr['country'] = uvals
            arr['counts'] = counts
            dstore['assets_by_country'] = arr

    dic = dict(__pyclass__='openquake.risklib.asset.TagCollection',
               tagnames=numpy.array(tagnames, hdf5.vstr),
               tagsizes=tagsizes)
    dstore.getitem('tagcol').attrs.update(dic)


def gen_tasks(files, sample_assets, monitor):
    """
    Generate tasks of kind exposure_by_geohash for large files
    """
    for file in files:
        # read CSV in chunks
        dfs = pandas.read_csv(
            file.fname, names=file.header, dtype=CONV,
            usecols=file.fields, skiprows=1, chunksize=1_000_000)
        for i, df in enumerate(dfs):
            if sample_assets:
                df = general.random_filter(df, float(sample_assets))
            if len(df) == 0:
                continue
            if 'ID_1' not in df.columns:  # happens for many islands
                df['ID_1'] = '???'
            dt = hdf5.build_dt(CONV, df.columns, file.fname)
            array = numpy.zeros(len(df), dt)
            for col in df.columns:
                array[col] = df[col].to_numpy()
            if i == 0:
                yield from exposure_by_geohash(array, monitor)
            else:
                print(file.fname)
                yield exposure_by_geohash, array


def store(exposures_xml, dstore):
    """
    Store the given exposures in the datastore
    """
    csvfiles = []
    for xml in exposures_xml:
        exposure, _ = _get_exposure(xml)
        csvfiles.extend(exposure.datafiles)
    files = hdf5.sniff(csvfiles, ',', IGNORE)
    dtlist = [(t, U32) for t in TAGS] + \
        [(f, F32) for f in set(CONV)-set(TAGS)-{'ASSET_ID', None}] + \
        [('ASSET_ID', h5py.string_dtype('ascii', 25))]
    for name, dt in dtlist:
        logging.info('Creating assets/%s', name)
    dstore['exposure'] = exposure
    dstore.create_df('assets', dtlist, 'gzip')
    slc_dt = numpy.dtype([('gh3', U16), ('start', U32), ('stop', U32)])
    dstore.create_dset('assets/slice_by_gh3', slc_dt, fillvalue=None)
    dstore.swmr_on()
    sa = os.environ.get('OQ_SAMPLE_ASSETS')
    smap = Starmap.apply(gen_tasks, (files, sa),
                         weight=operator.attrgetter('size'), h5=dstore.hdf5)
    num_assets = 0
    # NB: we need to keep everything in memory to make gzip efficient
    acc = general.AccumDict(accum=[])
    for gh3, arr in smap:
        for name in FIELDS:
            if name in TAGS:
                TAGS[name].append(arr[name])
            else:
                acc[name].append(arr[name])
        n = len(arr)
        slc = numpy.array([(gh3, num_assets, num_assets + n)], slc_dt)
        hdf5.extend(dstore['assets/slice_by_gh3'], slc)
        num_assets += n
    Starmap.shutdown()
    for name in sorted(acc):
        lst = acc.pop(name)
        arr = numpy.concatenate(lst, dtype=lst[0].dtype)
        logging.info(f'Storing assets/{name}')
        hdf5.extend(dstore['assets/' + name], arr)
    store_tagcol(dstore)

    # sanity check
    for name in FIELDS:
        n = len(dstore['assets/' + name])
        assert n == num_assets, (name, n, num_assets)

    logging.info('Stored {:_d} assets in {}'.format(n, dstore.filename))


def main(exposures_xml):
    """
    An utility to convert an exposure from XML+CSV format into HDF5.
    NB: works only for the exposures of the global risk model, having
    field names like LONGITUDE, LATITUDE, etc
    """
    log, dstore = create_job_dstore()
    with dstore, log:
        store(exposures_xml, dstore)
    return dstore.filename

main.exposure_xml = dict(help='Exposure pathnames', nargs='+')


if __name__ == '__main__':
    # python -m openquake.commonlib.expo_to_hdf5 exposure.xml
    sap.run(main)
