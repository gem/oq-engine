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
import time
import logging
import operator
from collections import Counter
import pandas
import numpy
from openquake.baselib import hdf5, sap, general, performance
from openquake.baselib.parallel import Starmap
from openquake.hazardlib.geo.utils import hex6
from openquake.commonlib.datastore import create_job_dstore
from openquake.risklib.asset import _get_exposure, Exposure
from openquake.qa_tests_data import mosaic

MOSAIC_DIR = os.path.dirname(mosaic.__file__)
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
B32 = (numpy.bytes_, 32)
CONV = {n: F32 for n in '''
BUILDINGS COST_CONTENTS_USD COST_NONSTRUCTURAL_USD
COST_STRUCTURAL_USD LATITUDE LONGITUDE OCCUPANTS_PER_ASSET
OCCUPANTS_PER_ASSET_AVERAGE OCCUPANTS_PER_ASSET_DAY
OCCUPANTS_PER_ASSET_NIGHT OCCUPANTS_PER_ASSET_TRANSIT
TOTAL_AREA_SQM'''.split()}
CONV['ASSET_ID'] = B32
for f in (None, 'ID_1', 'ID_2', 'ID_3', 'ID_4', 'BARRIO_ID', 'PARROQUIA_ID',
          'ZONA_ID', 'NAME_3', 'NAME_4_LGD', 'WFP_ID_1', 'WFP_ID_2'):
    CONV[f] = B32
TAGS = ['TAXONOMY', 'ID_0', 'ID_1', 'ID_2', 'NAME_1', 'NAME_2', 'OCCUPANCY']
IGNORE = set('NAME_0 SETTLEMENT TOTAL_REPL_COST_USD COST_PER_AREA_USD'.split())
FIELDS = {'TAXONOMY', 'COST_NONSTRUCTURAL_USD', 'LONGITUDE',
          'COST_CONTENTS_USD', 'ASSET_ID', 'OCCUPANCY',
          'OCCUPANTS_PER_ASSET', 'OCCUPANTS_PER_ASSET_AVERAGE',
          'OCCUPANTS_PER_ASSET_DAY', 'OCCUPANTS_PER_ASSET_NIGHT',
          'OCCUPANTS_PER_ASSET_TRANSIT', 'TOTAL_AREA_SQM',
          'BUILDINGS', 'COST_STRUCTURAL_USD', 'NAME_1', 'NAME_2',
          'LATITUDE', 'ID_0', 'ID_1', 'ID_2'}
HEX6 = (numpy.bytes_, 6)

class Indexer(object):
    """
    Class fine-tuned for our current world exposure containing ~72M assets
    """
    def __init__(self, name, maxsize=99_000_000):
        self.name = name
        self.maxsize = maxsize
        self.dic = {}
        self.indices = numpy.zeros(maxsize, U32)
        self.size = 0

    def add1(self, value):
        try:
            idx = self.dic[value]
        except KeyError:
            idx = len(self.dic)
            self.dic[value] = idx
        self.indices[self.size] = idx
        self.size += 1

    def add(self, values):
        for value in values:
            self.add1(value)

    def save(self, h5):
        tags = numpy.concatenate([[b'?'], numpy.array(list(self.dic))])
        indices = self.indices[:self.size]
        name = 'taxonomy' if self.name == 'TAXONOMY' else self.name
        # NOTE: with errors='ignore' encoding errors in the NAME_2 values
        # due to the truncation to 32 bytes will be ignored
        hdf5.create(
            h5, f'tagcol/{name}', hdf5.vstr, (len(tags),)
        )[:] = [x.decode('utf8', errors='ignore') for x in tags]
        hdf5.extend(h5[f'assets/{self.name}'], indices)

    def __repr__(self):
        return f'<Indexer[{self.name}]>'


def add_hex6(array):
    """
    Add field "hex6" to a structured array
    """
    if len(array) == 0:
        return ()
    dt = array.dtype
    dtlist = [('hex6', HEX6)] + [(n, dt[n]) for n in dt.names]
    out = numpy.zeros(len(array), dtlist)
    for n in dt.names:
        out[n] = array[n]
        out['hex6'] = hex6(array['LONGITUDE'], array['LATITUDE'])
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


def exposure_by_hex6(array, monitor):
    """
    Group the assets by a H3 string with 6 characters.
    Yields triples (hex6, array, name2dic)
    """
    array = add_hex6(array)
    fix(array)
    for h6 in numpy.unique(array['hex6']):
        yield h6, array[array['hex6'] == h6]


def store_tagcol(dstore, indexer):
    """
    A TagCollection is stored as arrays like taxonomy = [
    "?", "Adobe", "Concrete", "Stone-Masonry", "Unreinforced-Brick-Masonry",
    "Wood"] with attributes __pyclass__, tagnames, tagsize
    """
    tagsizes = []
    tagnames = []
    for idx in indexer.values():
        idx.save(dstore.hdf5)
        tagsizes.append(len(idx.dic) + 1)
        if idx.name == 'TAXONOMY':
            tagnames.append('taxonomy')
        else:
            tagnames.append(idx.name)
    dic = dict(__pyclass__='openquake.risklib.asset.TagCollection',
               tagnames=numpy.array(tagnames, hdf5.vstr),
               tagsizes=tagsizes)
    dstore.getitem('tagcol').attrs.update(dic)


def save_by_country(dstore):
    from openquake.calculators.views import text_table
    logging.info('Computing/storing assets_by_country')
    countries = dstore['tagcol/ID_0'][:]
    id0s, counts = numpy.unique(dstore['assets/ID_0'][:], return_counts=1)
    abc = numpy.zeros(len(id0s), [('country', 'S3'), ('counts', U32)])
    abc['country'] = countries[id0s + 1]
    abc['counts'] = counts
    dstore['assets_by_country'] = abc
    print(text_table(abc, ext='org'))


# in parallel
def gen_tasks(files, wfp, sample_assets, monitor):
    """
    Generate tasks of kind exposure_by_hex6 for large files
    """
    for file in files:
        # read CSV in chunks
        if file.admin2 and 'NAME_2' in file.header:
            usecols = file.fields | {'ID_2', 'NAME_2'}
        elif file.admin2:
            usecols = file.fields | {'ID_2'}
        else:
            usecols = file.fields
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
                    try:
                        array[col] = [x.encode('utf8') for x in arr]
                    except AttributeError:
                        raise ValueError(f'{file.fname=}: {col=}')
                else:
                    array[col] = arr
            if i == 0:
                yield from exposure_by_hex6(array, monitor)
            else:
                yield exposure_by_hex6, array
        print(os.path.basename(file.fname), nrows)


def keep_wfp(csvfile):
    return any(col.startswith('WFP_') for col in csvfile.header)


def store(exposures_xml, grm_dir, wfp, dstore, sanity_check=True):
    """
    Store the given exposures in the datastore
    """
    t0 = time.time()
    if grm_dir:
        n = store_world_tmap(grm_dir, dstore)
        logging.info('Stored %d taxonomy mappings', n)
    logging.info('Preallocating tag indices')
    indexer = {tagname: Indexer(tagname) for tagname in TAGS}
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
        [('ASSET_ID', B32)]
    for name, dt in dtlist:
        logging.info('Creating assets/%s', name)
    dstore['exposure'] = exposure
    for name, dt in dtlist:
        hdf5.create(dstore.hdf5, f'assets/{name}', dt,
                    compression='gzip' if name in TAGS else None)
    slc_dt = numpy.dtype([('hex6', HEX6), ('start', U32), ('stop', U32)])
    dstore.create_dset('assets/slice_by_hex6', slc_dt)
    dstore.swmr_on()
    sa = os.environ.get('OQ_SAMPLE_ASSETS')
    smap = Starmap.apply(gen_tasks, (files, wfp, sa),
                         concurrent_tasks=128,
                         weight=operator.attrgetter('size'),
                         h5=dstore.hdf5)
    num_assets = 0
    name2dic = {b'?': b'?'}
    mon = performance.Monitor('tag indexing', h5=dstore)
    for h6, arr in smap:
        name2dic.update(zip(arr['ID_2'], arr['NAME_2']))
        for name in commonfields:
            if name in TAGS:
                with mon:
                    indexer[name].add(arr[name])
            else:
                hdf5.extend(dstore['assets/' + name], arr[name])
        n = len(arr)
        slc = numpy.array([(h6, num_assets, num_assets + n)], slc_dt)
        hdf5.extend(dstore['assets/slice_by_hex6'], slc)
        num_assets += n
    Starmap.shutdown()
    store_tagcol(dstore, indexer)
    save_by_country(dstore)
    ID2s = dstore['tagcol/ID_2'][:]
    # NOTE: with errors='ignore' encoding errors in the NAME_2 values due to the
    # truncation to 32 bytes will be ignored
    dstore.create_dset('NAME_2', hdf5.vstr, len(ID2s))[:] = [
        name2dic[id2].decode('utf8', errors='ignore') for id2 in ID2s]

    dt = time.time() - t0
    logging.info('Stored {:_d} assets in {} in {:_d} seconds'.format(
        n, dstore.filename, int(dt)))

    if sanity_check:
        for name in commonfields:
            n = len(dstore['assets/' + name])
            assert n == num_assets, (name, n, num_assets)

        # check readable
        exp = Exposure.read_around(dstore.filename, hexes=[b"836606"])
        assert len(exp.assets), exp


def read_world_tmap(grm_dir):
    """
    :returns: a dict pathname -> longname
    """
    summary = os.path.join(MOSAIC_DIR, 'taxonomy_mapping.csv')
    tmap_df = pandas.read_csv(summary, index_col=['country'])
    dic = {}
    for fname, df in tmap_df.groupby('fname'):
        dic[fname] = '_'.join(sorted(df.index))
    n = len(dic)
    out = {}
    assert len(set(dic.values())) == n, sorted(dic.values())
    for cwd, dirs, files in os.walk(grm_dir):
        for f in files:
            if f in dic:
                out[os.path.join(cwd, f)] = dic[f]
            elif f.startswith('taxonomy_mapping'):
                raise NameError(f'{f} is not listed in {summary}')
    return out


def store_world_tmap(grm_dir, dstore):
    """
    Store the world taxonomy mapping
    """
    dic = read_world_tmap(grm_dir)
    for f, name in dic.items():
        df = pandas.read_csv(f)
        try:
            dstore.create_df('tmap/' + name, df)
        except ValueError:  # exists already
            print('Repeated %s' % name)
    return len(dic)


def main(exposures_xml, grm_dir='', wfp=False, sanity_check=False):
    """
    An utility to convert an exposure from XML+CSV format into HDF5.
    NB: works only for the exposures of the global risk model, having
    field names like LONGITUDE, LATITUDE, etc
    """
    log, dstore = create_job_dstore()
    with dstore, log:
        store(exposures_xml, wfp, dstore, sanity_check)
    return dstore.filename


main.exposures_xml = dict(help='Exposure pathnames', nargs='+')
main.grm_dir = 'Global risk model directory'
main.wfp = "WFP exposure"
main.sanity_check = "Perform a sanity check"

if __name__ == '__main__':
    # python -m openquake.commonlib.expo_to_hdf5 exposure.xml
    sap.run(main)
