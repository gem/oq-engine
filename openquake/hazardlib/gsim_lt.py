# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2023, GEM Foundation
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

import io
import os
import ast
import copy
import json
import logging
import operator
import itertools
from collections import namedtuple, defaultdict
import toml
import numpy

from openquake.baselib import hdf5
from openquake.baselib.node import Node as N, context
from openquake.baselib.general import duplicated, BASE183, group_array
from openquake.hazardlib import valid, nrml, pmf, lt, InvalidFile
from openquake.hazardlib.gsim.mgmpe.avg_poe_gmpe import AvgPoeGMPE
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.imt import from_string

BranchTuple = namedtuple('BranchTuple', 'trt id gsim weight effective')


class InvalidLogicTree(Exception):
    pass


# manage the legacy logicTreeBranchingLevel nodes
def bsnodes(fname, branchinglevel):
    if branchinglevel.tag.endswith('logicTreeBranchingLevel'):
        if len(branchinglevel) > 1:
            raise InvalidLogicTree(
                '%s: Branching level %s has multiple branchsets'
                % (fname, branchinglevel['branchingLevelID']))
        return branchinglevel.nodes
    elif branchinglevel.tag.endswith('logicTreeBranchSet'):
        return [branchinglevel]
    else:
        raise ValueError('Expected BranchingLevel/BranchSet, got %s' %
                         branchinglevel)


def fix_bytes(record):
    # convert a record with bytes fields into a dictionary of strings
    dic = {}
    for n in record.dtype.names:
        v = record[n]
        dic[n] = v.decode('utf-8') if isinstance(v, bytes) else v
    return dic


class ImtWeight(object):
    """
    A composite weight by IMTs extracted from the gsim_logic_tree_file
    """
    @classmethod
    def new(cls, weight):
        self = object.__new__(cls)
        self.dic = {'weight': weight}
        return self

    def __init__(self, branch, fname):
        with context(fname, branch.uncertaintyWeight):
            nodes = list(branch.getnodes('uncertaintyWeight'))
            if 'imt' in nodes[0].attrib:
                raise InvalidLogicTree('The first uncertaintyWeight has an imt'
                                       ' attribute')
            self.dic = {'weight': float(nodes[0].text)}
            imts = []
            for n in nodes[1:]:
                self.dic[n['imt']] = float(n.text)
                imts.append(n['imt'])
            if len(set(imts)) < len(imts):
                raise InvalidLogicTree(
                    'There are duplicated IMTs in the weights')

    def __mul__(self, other):
        new = object.__new__(self.__class__)
        if isinstance(other, self.__class__):
            keys = set(self.dic) | set(other.dic)
            new.dic = {k: self[k] * other[k] for k in keys}
        else:  # assume a float
            new.dic = {k: self.dic[k] * other for k in self.dic}
        return new

    __rmul__ = __mul__

    def __add__(self, other):
        new = object.__new__(self.__class__)
        if isinstance(other, self.__class__):
            new.dic = {k: self.dic[k] + other[k] for k in self.dic}
        else:  # assume a float
            new.dic = {k: self.dic[k] + other for k in self.dic}
        return new

    __radd__ = __add__

    def __truediv__(self, other):
        new = object.__new__(self.__class__)
        if isinstance(other, self.__class__):
            new.dic = {k: self.dic[k] / other[k] for k in self.dic}
        else:  # assume a float
            new.dic = {k: self.dic[k] / other for k in self.dic}
        return new

    def is_one(self):
        """
        Check that all the inner weights are 1 up to the precision
        """
        return all(abs(v - 1.) < pmf.PRECISION for v in self.dic.values() if v)

    def __getitem__(self, imt):
        try:
            return self.dic[imt]
        except KeyError:
            return self.dic['weight']

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.dic)


def keyno(branch_id, bsno, brno, fname='', chars=BASE183):
    """
    :param branch_id: a branch ID string
    :param bsno: number of the branchset (starting from 0)
    :param brno: number of the branch in the branchset (starting from 0)
    :returns: a short unique alias for the branch_id
    """
    return chars[brno] + str(bsno)


class GsimLogicTree(object):
    """
    A GsimLogicTree instance is an iterable yielding `Realization`
    tuples with attributes `value`, `weight` and `lt_path`, where
    `value` is a dictionary {trt: gsim}, `weight` is a number in the
    interval 0..1 and `lt_path` is a tuple with the branch ids of the
    given realization.

    :param str fname:
        full path of the gsim_logic_tree file
    :param tectonic_region_types:
        a sequence of distinct tectonic region types
    :param ltnode:
        usually None, but it can also be a
        :class:`openquake.hazardlib.nrml.Node` object describing the
        GSIM logic tree XML file, to avoid reparsing it
    """
    @classmethod
    def from_(cls, gsim):
        """
        Generate a trivial GsimLogicTree from a single GSIM instance.
        """
        ltbranch = N('logicTreeBranch', {'branchID': 'b1'},
                     nodes=[N('uncertaintyModel', text=str(gsim)),
                            N('uncertaintyWeight', text='1.0')])
        lt = N('logicTree', {'logicTreeID': 'lt1'},
               nodes=[N('logicTreeBranchingLevel', {'branchingLevelID': 'bl1'},
                        nodes=[N('logicTreeBranchSet',
                                 {'applyToTectonicRegionType': '*',
                                  'branchSetID': 'bs1',
                                  'uncertaintyType': 'gmpeModel'},
                                 nodes=[ltbranch])])])
        return cls('fake/' + gsim.__class__.__name__, ['*'], ltnode=lt)

    def __init__(self, fname, tectonic_region_types=['*'], ltnode=None):
        # tectonic_region_types usually comes from the source models
        self.filename = fname
        trts = sorted(tectonic_region_types)
        if len(trts) > len(set(trts)):
            raise ValueError(
                'The given tectonic region types are not distinct: %s' %
                ','.join(trts))
        self.values = defaultdict(list)  # {trt: gsims}
        self._ltnode = ltnode or nrml.read(fname).logicTree
        self.bsetdict = {}
        self.shortener = {}
        self.branches = self._build_branches(trts)  # sorted by trt
        if trts != ['*']:
            # reduce self.values to the listed TRTs
            values = {}
            for trt in trts:
                values[trt] = self.values[trt]
                if not values[trt]:
                    raise InvalidLogicTree('%s is missing the TRT %r' %
                                           (fname, trt))
            self.values = values
        if trts and not self.branches:
            raise InvalidLogicTree(
                '%s is missing in %s' % (set(tectonic_region_types), fname))

    @property
    def req_site_params(self):
        site_params = set()
        for trt in self.values:
            for gsim in self.values[trt]:
                site_params.update(gsim.REQUIRES_SITES_PARAMETERS)
        return site_params

    def check_imts(self, imts):
        """
        Make sure the IMTs are recognized by all GSIMs in the logic tree
        """
        for trt in self.values:
            for gsim in self.values[trt]:
                for attr in dir(gsim):
                    coeffs = getattr(gsim, attr)
                    if not isinstance(coeffs, CoeffsTable):
                        continue
                    for imt in imts:
                        if imt.startswith('SA'):
                            try:
                                coeffs[from_string(imt)]
                            except KeyError:
                                raise ValueError(
                                    '%s is out of the period range defined '
                                    'for %s' % (imt, gsim))

    def __toh5__(self):
        weights = set()
        for branch in self.branches:
            weights.update(branch.weight.dic)
        dt = [('trt', hdf5.vstr), ('branch', hdf5.vstr),
              ('uncertainty', hdf5.vstr)] + [
            (weight, float) for weight in sorted(weights)]
        branches = [(b.trt, b.id, repr(b.gsim)) +
                    tuple(b.weight[weight] for weight in sorted(weights))
                    for b in self.branches if b.effective]
        dic = {'bsetdict': json.dumps(self.bsetdict)}
        if hasattr(self, 'filename'):
            # missing in EventBasedRiskTestCase case_1f
            dic['filename'] = self.filename
            dirname = os.path.dirname(self.filename)
            for gsims in self.values.values():
                for gsim in gsims:
                    for k, v in gsim.kwargs.items():
                        if v == None:
                            pass
                        else:
                            if k.endswith(('_file', '_table')):
                                fname = os.path.join(dirname, v)
                                with open(fname, 'rb') as f:
                                    dic[os.path.basename(v)] = f.read()
        return numpy.array(branches, dt), dic

    def __fromh5__(self, array, dic):
        self.bsetdict = json.loads(dic['bsetdict'])
        self.filename = dic['filename']
        self.branches = []
        self.shortener = {}
        self.values = defaultdict(list)
        dirname = os.path.dirname(dic['filename'])
        for bsno, branches in enumerate(group_array(array, 'trt').values()):
            for brno, branch in enumerate(branches):
                branch = fix_bytes(branch)
                br_id = branch['branch']
                gsim = valid.gsim(branch['uncertainty'], dirname)
                for k, v in gsim.kwargs.items():
                    if k.endswith(('_file', '_table')):
                        if v == None:
                            pass
                        else:
                            arr = numpy.asarray(dic[os.path.basename(v)][()])
                            gsim.kwargs[k] = io.BytesIO(bytes(arr))
                self.values[branch['trt']].append(gsim)
                weight = object.__new__(ImtWeight)
                # branch dtype ('trt', 'branch', 'uncertainty', 'weight', ...)
                weight.dic = {w: branch[w] for w in array.dtype.names[3:]}
                if len(weight.dic) > 1:
                    gsim.weight = weight
                bt = BranchTuple(branch['trt'], br_id, gsim, weight, True)
                self.branches.append(bt)
                self.shortener[br_id] = keyno(br_id, bsno, brno)

    def reduce(self, trts):
        """
        Reduce the GsimLogicTree.

        :param trts: a subset of tectonic region types
        :returns: a reduced GsimLogicTree instance
        """
        new = copy.deepcopy(self)
        new.values = {trt: self.values[trt] for trt in trts}
        if trts != {'*'}:
            new.branches = []
            for br in self.branches:
                if br.trt in trts:
                    branch = BranchTuple(br.trt, br.id, br.gsim, br.weight, 1)
                    new.branches.append(branch)
        return new

    def collapse(self, branchset_ids):
        """
        Collapse the GsimLogicTree by using AgvGMPE instances if needed

        :param branchset_ids: branchset ids to collapse
        :returns: a collapse GsimLogicTree instance
        """
        new = object.__new__(self.__class__)
        vars(new).update(vars(self))
        new.branches = []
        trti = 0
        for trt, grp in itertools.groupby(self.branches, lambda b: b.trt):
            bs_id = self.bsetdict[trt]
            brs = []
            gsims = []
            weights = []
            for br in grp:
                brs.append(br.id)
                gsims.append(br.gsim)
                weights.append(br.weight)
            if len(gsims) > 1 and bs_id in branchset_ids:
                kwargs = {}
                for brid, gsim, weight in zip(brs, gsims, weights):
                    kw = gsim.kwargs.copy()
                    kw['weight'] = weight.dic['weight']
                    kwargs[brid] = {gsim.__class__.__name__: kw}
                _toml = toml.dumps({'AvgPoeGMPE': kwargs})
                gsim = AvgPoeGMPE(**kwargs)
                gsim._toml = _toml
                new.values[trt] = [gsim]
                br_id = 'gA' + str(trti)
                new.shortener[br_id] = keyno(br_id, trti, 0, self.filename)
                branch = BranchTuple(trt, br_id, gsim, sum(weights), True)
                new.branches.append(branch)
            else:
                new.branches.append(br)
            trti += 1
        return new

    def get_num_branches(self):
        """
        Return the number of effective branches for tectonic region type,
        as a dictionary.
        """
        num = {}
        for trt, branches in itertools.groupby(
                self.branches, operator.attrgetter('trt')):
            num[trt] = sum(1 for br in branches if br.effective)
        return num

    def get_num_paths(self):
        """
        Return the effective number of paths in the tree.
        """
        num_branches = self.get_num_branches()
        if not sum(num_branches.values()):
            return 0
        num = 1
        for val in num_branches.values():
            if val:  # the branch is effective
                num *= val
        return num

    def _build_branches(self, tectonic_region_types):
        # do the parsing, called at instantiation time to populate .values
        trts = []
        branches = []
        branchids = []
        branchsetids = set()
        basedir = os.path.dirname(self.filename)
        for bsno, blnode in enumerate(self._ltnode):
            [branchset] = bsnodes(self.filename, blnode)
            if branchset['uncertaintyType'] != 'gmpeModel':
                raise InvalidLogicTree(
                    '%s: only uncertainties of type "gmpeModel" '
                    'are allowed in gmpe logic tree' % self.filename)
            bsid = branchset['branchSetID']
            if bsid in branchsetids:
                raise InvalidLogicTree(
                    '%s: Duplicated branchSetID %s' %
                    (self.filename, bsid))
            else:
                branchsetids.add(bsid)
            trt = branchset.get('applyToTectonicRegionType')
            if trt:  # missing in logictree_test.py
                self.bsetdict[trt] = bsid
                trts.append(trt)
            self.bsetdict[trt] = bsid
            # NB: '*' is used in scenario calculations to disable filtering
            effective = (tectonic_region_types == ['*'] or
                         trt in tectonic_region_types)
            weights = []
            branch_ids = []
            for brno, branch in enumerate(branchset):
                weight = ImtWeight(branch, self.filename)
                weights.append(weight)
                branch_id = 'g' + BASE183[brno] + str(bsno)
                branch_ids.append(branch_id)
                try:
                    gsim = valid.gsim(branch.uncertaintyModel, basedir)
                except Exception as exc:
                    raise ValueError(
                        "%s in file %s" % (exc, self.filename)) from exc
                if gsim in self.values[trt]:
                    raise InvalidLogicTree('%s: duplicated gsim %s' %
                                           (self.filename, gsim))
                if len(weight.dic) > 1:
                    gsim.weight = weight
                self.values[trt].append(gsim)
                bt = BranchTuple(
                    branchset['applyToTectonicRegionType'],
                    branch_id, gsim, weight, effective)
                if effective:
                    branches.append(bt)
                    self.shortener[branch_id] = keyno(
                        branch_id, bsno, brno, self.filename)
                if os.environ.get('OQ_REDUCE'):  # take the first branch only
                    bt.weight.dic['weight'] = 1.
                    break
            tot = sum(weights)
            assert tot.is_one(), '%s in branchset %s' % (
                tot, branchset.attrib['branchSetID'])
            if duplicated(branch_ids):
                raise InvalidLogicTree(
                    'There where duplicated branchIDs in %s' %
                    self.filename)
            branchids.extend(branch_ids)

        if len(trts) > len(set(trts)):
            raise InvalidLogicTree(
                '%s: Found duplicated applyToTectonicRegionType=%s' %
                (self.filename, trts))
        dupl = duplicated(branchids)
        if dupl:
            logging.debug(
                'There are duplicated branchIDs %s in %s', dupl, self.filename)
        branches.sort(key=lambda b: b.trt)
        return branches

    def get_weights(self, trt, imt='weight'):
        """
        Branch weights for the given TRT
        """
        weights = []
        for br in self.branches:
            if br.trt == trt:
                weights.append(br.weight[imt])
        return numpy.array(weights)

    def sample(self, n, seed, sampling_method='early_weights'):
        """
        :param n: number of samples
        :param seed: random seed
        :param sampling_method: by default 'early_weights'
        :returns: n Realization objects
        """
        m = len(self.values)  # number of TRTs
        probs = lt.random((n, m), seed, sampling_method)
        brlists = [lt.sample([b for b in self.branches if b.trt == trt],
                             probs[:, i], sampling_method)
                   for i, trt in enumerate(self.values)]
        rlzs = []
        for i in range(n):
            weight = ImtWeight.new(1.)
            lt_path = []
            lt_uid = []
            value = []
            for brlist in brlists:  # there is branch list for each TRT
                branch = brlist[i]
                lt_path.append(branch.id)
                lt_uid.append(branch.id if branch.effective else '.')
                weight *= branch.weight
                value.append(branch.gsim)
            rlz = lt.Realization(tuple(value), weight, i, tuple(lt_uid))
            rlzs.append(rlz)
        return rlzs

    def get_rlzs_by_gsim_trt(self, samples=0, seed=42,
                             sampling_method='early_weights'):
        """
        :param samples:
            number of realizations to sample (if 0, use full enumeration)
        :param seed:
            seed to use for the sampling
        :param sampling_method:
            sampling method, by default 'early_weights'
        :returns:
            dictionary trt -> gsim -> all_rlz_ordinals for each gsim in the trt
        """
        if samples:
            rlzs = self.sample(samples, seed, sampling_method)
        else:
            rlzs = list(self)
        ddic = {}
        for i, trt in enumerate(self.values):
            ddic[trt] = {gsim: [rlz.ordinal for rlz in rlzs
                                if rlz.value[i] == gsim]
                         for gsim in self.values[trt]}
        return ddic

    def __iter__(self):
        """
        Yield :class:`openquake.hazardlib.logictree.Realization` instances
        """
        groups = []
        # NB: branches are already sorted
        for trt in self.values:
            groups.append([b for b in self.branches if b.trt == trt])
        # with T tectonic region types there are T groups and T branches
        for i, branches in enumerate(itertools.product(*groups)):
            weight = ImtWeight.new(1.)
            lt_path = []
            lt_uid = []
            value = []
            for trt, branch in zip(self.values, branches):
                lt_path.append(branch.id)
                lt_uid.append(branch.id if branch.effective else '.')
                weight *= branch.weight
                value.append(branch.gsim)
            yield lt.Realization(tuple(value), weight, i, tuple(lt_uid))

    def __repr__(self):
        lines = ['%s,%s,%s,w=%s' %
                 (b.trt, b.id, b.gsim, b.weight['weight'])
                 for b in self.branches if b.effective]
        return '<%s\n%s>' % (self.__class__.__name__, '\n'.join(lines))


def rel_paths(toml):
    # the paths inside the toml describing the gsim
    paths = []
    for line in toml.splitlines():
        try:
            name, path = line.split('=')
        except ValueError:
            pass
        else:
            if name.rstrip().endswith(('_file', '_table')):
                paths.append(ast.literal_eval(path.strip()))
    return paths


def abs_paths(smlt, fnames):
    # relative -> absolute paths
    base_path = os.path.dirname(smlt)
    paths = []
    for fname in fnames:
        if os.path.isabs(fname):
            raise InvalidFile('%s: %s must be a relative path' % (smlt, fname))
        fname = os.path.abspath(os.path.join(base_path, fname))
        if os.path.exists(fname):  # consider only real paths
            paths.append(fname)
    return paths


def collect_files(gsim_lt_path):
    """
    Given a path to a gsim logic tree, collect all of the
    path names it contains (relevent for tabular/file-dependent GSIMs).
    """
    n = nrml.read(gsim_lt_path)
    try:
        blevels = n.logicTree
    except Exception:
        raise InvalidFile('%s is not a valid source_model_logic_tree_file'
                          % gsim_lt_path)
    paths = set()
    for blevel in blevels:
        for bset in bsnodes(gsim_lt_path, blevel):
            assert bset['uncertaintyType'] == 'gmpeModel', bset
            for br in bset:
                with context(gsim_lt_path, br):
                    relpaths = rel_paths(br.uncertaintyModel.text)
                    paths.update(abs_paths(gsim_lt_path, relpaths))
    return sorted(paths)
