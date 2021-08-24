# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2021, GEM Foundation
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
import json
import string
import operator
import itertools
from collections import namedtuple, defaultdict
import toml
import numpy

from openquake.baselib import hdf5
from openquake.baselib.node import Node as N, context
from openquake.baselib.general import duplicated
from openquake.hazardlib import valid, nrml, pmf, lt
from openquake.hazardlib.gsim.mgmpe.avg_gmpe import AvgGMPE
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


def keyno(branch_id, no, fname='',
          chars=string.digits + string.ascii_uppercase):
    """
    :param branch_id: a branch ID string
    :param no: number of the branch in the branchset (starting from 0)
    :returns: a 1-char string for the branch_id based on the branch number
    """
    try:
        valid.branch_id(branch_id)
    except ValueError as ex:
        raise ValueError('%s %s' % (ex, fname))
    try:
        return chars[no]
    except IndexError:
        return branch_id


class Realization(object):
    """
    Generic Realization object with attributes value, weight, ordinal, lt_path,
    samples.
    """
    def __init__(self, value, weight, ordinal, lt_path, samples=1):
        self.value = value
        self.weight = weight
        self.ordinal = ordinal
        self.lt_path = lt_path
        self.samples = samples

    @property
    def pid(self):
        return '~'.join(self.lt_path)  # path ID

    @property
    def name(self):
        """
        Compact representation for the names
        """
        names = self.value.split()
        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return ' '.join(names)
        else:
            return ' '.join([names[0], '...', names[-1]])

    def __repr__(self):
        samples = ', samples=%d' % self.samples if self.samples > 1 else ''
        return '<%s #%d %s, path=%s, weight=%s%s>' % (
            self.__class__.__name__, self.ordinal, self.value,
            '~'.join(self.lt_path), self.weight, samples)


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
        self.branches = self._build_trts_branches(trts)  # sorted by trt
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
        for no, branch in enumerate(array):
            branch = fix_bytes(branch)
            br_id = branch['branch']
            gsim = valid.gsim(branch['uncertainty'])
            for k, v in gsim.kwargs.items():
                if k.endswith(('_file', '_table')):
                    arr = numpy.asarray(dic[os.path.basename(v)][()])
                    gsim.kwargs[k] = io.BytesIO(bytes(arr))
            gsim.__init__(**gsim.kwargs)
            self.values[branch['trt']].append(gsim)
            weight = object.__new__(ImtWeight)
            # branch has dtype ('trt', 'branch', 'uncertainty', 'weight', ...)
            weight.dic = {w: branch[w] for w in array.dtype.names[3:]}
            if len(weight.dic) > 1:
                gsim.weight = weight
            bt = BranchTuple(branch['trt'], br_id, gsim, weight, True)
            self.branches.append(bt)
            self.shortener[br_id] = keyno(br_id, no)

    def reduce(self, trts):
        """
        Reduce the GsimLogicTree.

        :param trts: a subset of tectonic region types
        :returns: a reduced GsimLogicTree instance
        """
        new = object.__new__(self.__class__)
        vars(new).update(vars(self))
        if trts != {'*'}:
            new.branches = []
            for br in self.branches:
                branch = BranchTuple(br.trt, br.id, br.gsim, br.weight,
                                     br.trt in trts)
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
                _toml = toml.dumps({'AvgGMPE': kwargs})
                gsim = AvgGMPE(**kwargs)
                gsim._toml = _toml
                new.values[trt] = [gsim]
                branch = BranchTuple(trt, bs_id, gsim, sum(weights), True)
                new.branches.append(branch)
            else:
                new.branches.append(br)
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

    def _build_trts_branches(self, tectonic_region_types):
        # do the parsing, called at instantiation time to populate .values
        trts = []
        branches = []
        branchsetids = set()
        basedir = os.path.dirname(self.filename)
        no = 0
        for blnode in self._ltnode:
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
            for branch in branchset:
                weight = ImtWeight(branch, self.filename)
                weights.append(weight)
                branch_id = branch['branchID']
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
                        branch_id, no, self.filename)
                    no += 1
            tot = sum(weights)
            assert tot.is_one(), '%s in branch %s' % (tot, branch_id)
            if duplicated(branch_ids):
                raise InvalidLogicTree(
                    'There where duplicated branchIDs in %s' %
                    self.filename)
        if len(trts) > len(set(trts)):
            raise InvalidLogicTree(
                '%s: Found duplicated applyToTectonicRegionType=%s' %
                (self.filename, trts))
        branches.sort(key=lambda b: (b.trt, b.id))
        # TODO: add an .idx to each GSIM ?
        return branches

    def get_gsims(self, trt):
        """
        :param trt: tectonic region type
        :returns: sorted list of available GSIMs for that trt
        """
        if trt == '*' or trt == b'*':  # fake logictree
            [trt] = self.values
        return sorted(self.values[trt])

    def sample(self, n, seed, sampling_method):
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
            weight = 1
            lt_path = []
            lt_uid = []
            value = []
            for brlist in brlists:  # there is branch list for each TRT
                branch = brlist[i]
                lt_path.append(branch.id)
                lt_uid.append(branch.id if branch.effective else '@')
                weight *= branch.weight
                value.append(branch.gsim)
            rlz = Realization(tuple(value), weight, i, tuple(lt_uid))
            rlzs.append(rlz)
        return rlzs

    def get_rlzs_by_gsim_trt(self):
        """
        :returns:
            dictionary trt -> gsim -> all_rlz_ordinals for each gsim in the trt
        """
        rlzs = list(self)
        ddic = {}
        for i, trt in enumerate(self.values):
            ddic[trt] = {gsim: [rlz.ordinal for rlz in rlzs
                                if rlz.value[i] == gsim]
                         for gsim in self.values[trt]}
        return ddic

    def __iter__(self):
        """
        Yield :class:`openquake.commonlib.logictree.Realization` instances
        """
        groups = []
        # NB: branches are already sorted
        for trt in self.values:
            groups.append([b for b in self.branches if b.trt == trt])
        # with T tectonic region types there are T groups and T branches
        for i, branches in enumerate(itertools.product(*groups)):
            weight = 1
            lt_path = []
            lt_uid = []
            value = []
            for trt, branch in zip(self.values, branches):
                lt_path.append(branch.id)
                lt_uid.append(branch.id if branch.effective else '@')
                weight *= branch.weight
                value.append(branch.gsim)
            yield Realization(tuple(value), weight, i, tuple(lt_uid))

    def __repr__(self):
        lines = ['%s,%s,%s,w=%s' %
                 (b.trt, b.id, b.gsim, b.weight['weight'])
                 for b in self.branches if b.effective]
        return '<%s\n%s>' % (self.__class__.__name__, '\n'.join(lines))

