"""NZSHM exporting."""
import attrs
# import re
# import os
# import sys
# import itertools
# import collections
import numpy as np
import pandas as pd

# from openquake.baselib.general import deprecated, DictArray
# from openquake.baselib import hdf5, writers
# from openquake.baselib.python3compat import decode
# from openquake.hazardlib.imt import from_string
# from openquake.calculators.views import view, text_table
# from openquake.calculators.extract import extract, get_sites, get_info
from openquake.calculators.export import export
# from openquake.commonlib import hazard_writers, calc, util

#new imports
from openquake.commonlib import datastore
from .hazard import get_kkf

F32 = np.float32
F64 = np.float64
U8 = np.uint8
U16 = np.uint16
U32 = np.uint32

# with compression you can save 60% of space by losing only 10% of saving time
savez = np.savez_compressed


@attrs.define(frozen=True)
class HazardCurveFactory():
    """Hazard Object with oq Hazard Curve extraction"""
    external_id: str

@attrs.define(frozen=True)
class HazardCurve():
    """Hazard Object with oq Hazard Curve extraction"""
    iml_measure: str


@export.add(('hcurves', 'nzshm'))
def export_hcurves(ekey, dstore):
    """
    Exports some exports.
    """
    oq = dstore['oqparam']
    R = dstore['full_lt'].get_num_rlzs()
    key, kind, fmt = get_kkf(ekey)

    # res = []
    # # res.append(str(ekey))
    # res.append(f"calc_id {dstore.calc_id}")
    # res.append(f"{(key, kind, fmt)}")
    # # res.append(f"{dstore}")

    # res += oq.get_kinds(kind, R)
    return oq.get_kinds(kind, R)


def explore(calc_id: int):
    """
    do some exploration
    """
    dstore = None

    dstore = datastore.read(calc_id)

    print(dstore)
    print(dstore.calc_id)

    #print(dir(dstore))
    """
    ['_MutableMapping__marker', '__abstractmethods__', '__class__', '__contains__', '__delattr__', '__delitem__', '__dict__', '__dir__', '__doc__',
    '__enter__', '__eq__', '__exit__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__getstate__', '__gt__', '__hash__', '__init__',
    '__init_subclass__', '__iter__', '__le__', '__len__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__',
    '__reversed__', '__setattr__', '__setitem__', '__sizeof__', '__slots__', '__str__', '__subclasshook__', '__weakref__', '_abc_impl',
    'build_fname', 'calc_id', 'clear', 'close', 'closed', 'create_df', 'create_dset', 'datadir', 'export_dir', 'export_path', 'filename',
    'flush', 'get', 'get_attr', 'get_attrs', 'get_file', 'getitem', 'getsize', 'hdf5', 'items', 'job', 'keys', 'metadata', 'mode', 'open', '
    opened', 'parent', 'pop', 'popitem', 'ppath', 'read_df', 'read_unique', 'retrieve_files', 'sel', 'set_attrs', 'set_shape_descr', 'setdefault',
    'store_files', 'swmr_on', 'tempname', 'update', 'values']
    """

    top = vars(dstore)

    print(dstore.keys())
    print(top.keys())
    """dict_keys(['filename', 'ppath', 'calc_id', 'tempname', 'parent', 'datadir', 'mode', 'hdf5'])"""


    oqparam = vars(dstore['oqparam'])
    print(oqparam.keys())
    """
    dict_keys(['base_path', 'inputs', 'description', 'calculation_mode', 'random_seed', 'sites', 'number_of_logic_tree_samples', 'concurrent_tasks',
        'rupture_mesh_spacing', 'complex_fault_mesh_spacing', 'width_of_mfd_bin', 'area_source_discretization', 'reference_vs30_value',
        'reference_depth_to_1pt0km_per_sec', 'reference_depth_to_2pt5km_per_sec', 'investigation_time', 'truncation_level', 'maximum_distance',
        'uniform_hazard_spectra', 'quantiles', 'poes', 'exports', 'mean', 'individual_rlzs', 'hazard_imtls', 'all_cost_types', 'minimum_asset_loss',
        'export_dir'])
    """
    print("base_path", oqparam['base_path'])
    print("sites", oqparam['sites'])

def unpack(calc_id: int):
    """
    do some exploration
    """

    dstore = datastore.read(calc_id)
    oqparam = vars(dstore['oqparam'])


    print("lt realizations")
    print("================")
    lt = pd.DataFrame(dstore['full_lt'].rlzs).drop('ordinal',axis=1)
    print(lt.head())
    print()


    def rlz_tuple(rlz: 'Realization'):
        """Create a tuple from a Realization instance."""
        return (rlz.ordinal, rlz.value, rlz.weight, rlz.lt_path, rlz.samples)


    print("gsim_lt")
    print("================")
    gsim_lt = pd.DataFrame([rlz_tuple(r) for r in dstore['full_lt'].gsim_lt])
    print(gsim_lt)

    print("sources")
    print("================")
    slt = pd.DataFrame([rlz_tuple(r) for r in dstore['full_lt'].source_model_lt])
    print(slt)

    print("quantiles (some)")
    print("================")
    print(oqparam['quantiles'][:5])
    print()

    print("hazard_imtls (some)")
    print("====================")
    print(oqparam['hazard_imtls'].keys())
    print(oqparam['hazard_imtls']['PGA'][:5])


    #from H5 sections
    print("weights")
    print("================")
    print(dstore['weights'][:].tolist())

    print("realizations")
    print("================")
    hcurves_rlzs = np.moveaxis(dstore['hcurves-rlzs'][:], 1, 3) # [site,imt,imtl,realizations (source*gmpe) ] (order after moveaxis)
    print("[site,imt,imtl,realizations (source*gmpe) ] (order after moveaxis)")

    #print(hcurves_rlzs)

    for i in range(hcurves_rlzs.shape[0]):
        print(i) # hcurves_rlzs[i,:])

    # #print(hcurves_rlzs[0][0][0].tolist())


    print(hcurves_rlzs.reshape(1, -1).shape)
    dataset = pd.DataFrame(hcurves_rlzs.reshape(1, -1))

    # assert 0
    # data = hcurves_rlzs
    # dataset = pd.DataFrame(columns = {'site': data[:, 0], 'imt': data[:, 1], 'imtl': data[:, 2]}, rows = data[:, 3],  index=[i for i in range(data.shape[0])])
    print(dataset)
    assert 0




    print("statistics")
    print("==========")
    hcurves_stats = np.moveaxis(dstore['hcurves-stats'][:], 1, 3) #[site,imt,imtl,mean+quantiles] (order after moveaxis)
    print("[site,imt,imtl,mean+quantiles] (order after moveaxis)")
    print(hcurves_stats.shape)


    print(hcurves_stats[0][0][0].tolist())


if __name__ == "__main__":
    #explore(50)
    unpack(50)
