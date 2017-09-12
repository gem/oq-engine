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

from h5py._hl.dataset import Dataset
from h5py._hl.group import Group
import numpy
from openquake.baselib.general import CallableDict

# for instance extract('dstore/sids', dstore)
extract = CallableDict(lambda k: k.split('/', 1)[0])


class DatasetWrapper(object):
    """
    A pickleable wrapper over an HDF5 dataset
    """
    def __init__(self, array, attrs):
        vars(self).update(attrs)
        self.array = array


class DatagroupWrapper(object):
    """
    A pickleable wrapper over an HDF5 group
    """
    def __init__(self, array, attrs):
        vars(self).update(attrs)
        self.array = array


@extract.add('')
def extract_slash(dspath, dstore):
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


# TODO: add a way to invalidate the cache (easy) and somebody responsible
# for doing that (difficult: perhaps a recurrent task?)
asset_cache = {}  # job_id -> asset_values


@extract.add('asset_values')
def extract_asset_values(key, dstore):
    """
    :returns:
        (aid, loss_type1, ..., loss_typeN) composite array
    """
    sid = int(key.split('/')[1])
    try:
        data = asset_cache[dstore.calc_id]
    except KeyError:
        asset_refs = extract('/asset_refs', dstore).array
        assetcol = extract('/assetcol', dstore)
        assets_by_site = assetcol.assets_by_site()
        lts = assetcol.loss_types
        time_event = assetcol.time_event
        dt = numpy.dtype([('ref', asset_refs.dtype), ('aid', numpy.uint32)] +
                         [(str(lt), numpy.float32) for lt in lts])
        data = []
        for assets in assets_by_site:
            vals = numpy.zeros(len(assets), dt)
            for a, asset in enumerate(assets):
                vals[a]['ref'] = asset_refs[asset.idx]
                vals[a]['aid'] = asset.ordinal
                for lt in lts:
                    vals[a][lt] = asset.value(lt, time_event)
            data.append(vals)
        asset_cache[dstore.calc_id] = data
    return data[sid]
