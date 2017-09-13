#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2017, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import collections
from h5py._hl.dataset import Dataset
from h5py._hl.group import Group
import numpy
try:
    from functools import lrucache
except ImportError:
    from openquake.risklib.utils import memoized
else:
    memoized = lrucache(100)


class Extract(collections.OrderedDict):

    def add(self, key, cache=False):
        def decorator(func):
            self[key] = memoized(func) if cache else func
            return func
        return decorator

    def __call__(self, dstore, key):
        try:
            k, v = key.split('/', 1)
        except ValueError:   # no slashes
            k, v = key, ''
        return self[k](dstore, v)

extract = Extract()


class DatasetWrapper(object):
    """
    A pickleable wrapper over an HDF5 dataset
    """
    def __init__(self, array, attrs):
        vars(self).update(attrs)
        self.array = array

    def __iter__(self):
        return iter(self.array)

    def __len__(self):
        return len(self.array)

    def __getitem__(self, idx):
        return self.array[idx]

    @property
    def dtype(self):
        return self.array.dtype


class DatagroupWrapper(object):
    """
    A pickleable wrapper over an HDF5 group
    """
    def __init__(self, array, attrs):
        vars(self).update(attrs)
        self.array = array

    def __iter__(self):
        return iter(self.array)

    def __len__(self):
        return len(self.array)

    def __getitem__(self, idx):
        return self.array[idx]


@extract.add('')
def extract_slash(dstore, dspath):
    """
    Extracts an HDF5 path object from the datastore, for instance
    extract('/sitecol', dstore)
    """
    obj = dstore[dspath]
    if isinstance(obj, Dataset):
        return DatasetWrapper(obj.value, obj.attrs)
    elif isinstance(obj, Group):
        return DatagroupWrapper(numpy.array(list(obj)), obj.attrs)
    else:
        return obj


@extract.add('asset_values', cache=True)
def extract_asset_values(dstore, sid):
    """
    :returns:
        (aid, loss_type1, ..., loss_typeN) composite array
    """
    if sid:
        return extract(dstore, 'asset_values')[int(sid)]
    asset_refs = extract(dstore, '/asset_refs')
    assetcol = extract(dstore, '/assetcol')
    assets_by_site = assetcol.assets_by_site()
    lts = assetcol.loss_types
    time_event = assetcol.time_event
    dt = numpy.dtype([('aref', asset_refs.dtype), ('aid', numpy.uint32)] +
                     [(str(lt), numpy.float32) for lt in lts])
    data = []
    for assets in assets_by_site:
        vals = numpy.zeros(len(assets), dt)
        for a, asset in enumerate(assets):
            vals[a]['aref'] = asset_refs[asset.idx]
            vals[a]['aid'] = asset.ordinal
            for lt in lts:
                vals[a][lt] = asset.value(lt, time_event)
        data.append(vals)
    return data
