# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2023 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Logic tree parser, verifier and processor. See specs at
https://blueprints.launchpad.net/openquake-old/+spec/openquake-logic-tree-module

A logic tree object must be iterable and yielding realizations, i.e. objects
with attributes `value`, `weight`, `lt_path` and `ordinal`.
"""

import os
import re
import ast
import copy
import json
import time
import logging
import functools
import itertools
import collections
import operator
import numpy
from openquake.baselib import hdf5
from openquake.baselib.python3compat import decode
from openquake.baselib.node import node_from_elem, context
from openquake.baselib.general import groupby, AccumDict
from openquake.hazardlib import nrml, InvalidFile, pmf
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib.gsim_lt import (
    GsimLogicTree, bsnodes, fix_bytes, keyno, abs_paths)
from openquake.hazardlib.lt import (
    Branch, BranchSet, count_paths, Realization, CompositeLogicTree,
    dummy_branchset, LogicTreeError, parse_uncertainty, random)

TRT_REGEX = re.compile(r'tectonicRegion="([^"]+?)"')
ID_REGEX = re.compile(r'Source\s+id="([^"]+?)"')

U16 = numpy.uint16
U32 = numpy.uint32
I32 = numpy.int32
F32 = numpy.float32

rlz_dt = numpy.dtype([
    ('ordinal', U32),
    ('branch_path', hdf5.vstr),
    ('weight', F32)
])

source_model_dt = numpy.dtype([
    ('name', hdf5.vstr),
    ('weight', F32),
    ('path', hdf5.vstr),
    ('samples', U32),
])

src_group_dt = numpy.dtype(
    [('trt_smr', U32),
     ('name', hdf5.vstr),
     ('trti', U16),
     ('effrup', I32),
     ('totrup', I32),
     ('sm_id', U32)])

branch_dt = [('branchset', hdf5.vstr), ('branch', hdf5.vstr),
             ('utype', hdf5.vstr), ('uvalue', hdf5.vstr), ('weight', float)]


def prod(iterator):
    """
    Replacement of math.prod for Python < 3.8
    """
    res = 1
    for el in iterator:
        res *= el
    return res


def unique(objects, key=None):
    """
    Raise a ValueError if there is a duplicated object, otherwise
    returns the objects as they are.
    """
    dupl = []
    for obj, group in itertools.groupby(sorted(objects), key):
        if sum(1 for _ in group) > 1:
            dupl.append(obj)
    if dupl:
        raise ValueError('Found duplicates %s' % dupl)
    return objects


@functools.lru_cache()
def get_effective_rlzs(rlzs):
    """
    Group together realizations with the same path
    and yield the first representative of each group.
    """
    effective = []
    ordinal = 0
    for group in groupby(rlzs, operator.attrgetter('pid')).values():
        rlz = group[0]
        if all(path == '@' for path in rlz.lt_path):  # empty realization
            continue
        effective.append(
            Realization(rlz.value, sum(r.weight for r in group),
                        ordinal, rlz.lt_path, len(group)))
        ordinal += 1
    return effective


Info = collections.namedtuple('Info', 'smpaths h5paths applytosources')


def collect_info(smltpath, branchID=None):
    """
    Given a path to a source model logic tree, collect all of the
    path names to the source models it contains.

    :param smltpath: source model logic tree file
    :param branchID: if given, consider only that branch
    :returns: an Info namedtuple (smpaths, h5paths, applytosources)
    """
    n = nrml.read(smltpath)
    try:
        blevels = n.logicTree
    except Exception:
        raise InvalidFile('%s is not a valid source_model_logic_tree_file'
                          % smltpath)
    smpaths = set()
    h5paths = set()
    applytosources = collections.defaultdict(list)  # branchID -> source IDs
    for blevel in blevels:
        for bset in bsnodes(smltpath, blevel):
            if 'applyToSources' in bset.attrib:
                applytosources[bset.get('applyToBranches')].extend(
                        bset['applyToSources'].split())
            if bset['uncertaintyType'] in 'sourceModel extendModel':
                for br in bset:
                    if branchID and branchID != br['branchID']:
                        continue
                    with context(smltpath, br):
                        fnames = abs_paths(
                            smltpath, unique(br.uncertaintyModel.text.split()))
                        smpaths.update(fnames)
                        for fname in fnames:
                            hdf5file = os.path.splitext(fname)[0] + '.hdf5'
                            if os.path.exists(hdf5file):
                                h5paths.add(hdf5file)
                    if os.environ.get('OQ_REDUCE'):  # only take first branch
                        break
    return Info(sorted(smpaths), sorted(h5paths), applytosources)


def read_source_groups(fname):
    """
    :param fname: a path to a source model XML file
    :return: a list of SourceGroup objects containing source nodes
    """
    smodel = nrml.read(fname).sourceModel
    src_groups = []
    if smodel[0].tag.endswith('sourceGroup'):  # NRML 0.5 format
        for sg_node in smodel:
            sg = SourceGroup(sg_node['tectonicRegion'])
            sg.sources = sg_node.nodes
            src_groups.append(sg)
    else:  # NRML 0.4 format: smodel is a list of source nodes
        src_groups.extend(SourceGroup.collect(smodel))
    return src_groups


def shorten(path_tuple, shortener):
    """
    :path:  sequence of strings
    :shortener: dictionary longstring -> shortstring
    :returns: shortened version of the path
    """
    if len(shortener) == 1:
        return 'A'
    chars = []
    for key in path_tuple:
        if key[0] == '.':  # dummy branch
            chars.append('.')
        else:
            chars.append(shortener[key][0])
    return ''.join(chars)


# useful to print reduced logic trees
def collect_paths(paths, b1=ord('['), b2=ord(']'), til=ord('~')):
    """
    Collect branch paths belonging to the same cluster

    >>> collect_paths([b'0~A0', b'0~A1'])
    b'[0]~[A][01]'
    """
    n = len(paths[0])
    for path in paths[1:]:
        assert len(path) == n, (len(path), n)
    sets = [set() for _ in range(n)]
    for c, s in enumerate(sets):
        for path in paths:
            s.add(path[c])
    ints = []
    for s in sets:
        chars = sorted(s)
        if chars != [til]:
            ints.append(b1)
        ints.extend(chars)
        if chars != [til]:
            ints.append(b2)
    return bytes(ints)


def reducible(lt, cluster_paths):
    """
    :param lt: a logic tree with B branches
    :param cluster_paths: list of paths for a realization cluster
    :returns: a list [filename, (branchSetID, branchIDs), ...]
    """
    longener = {short: long for long, short in lt.shortener.items()}
    tuplesets = [set() for _ in lt.bsetdict]
    for path in cluster_paths:
        for b, chars in enumerate(path.strip('][').split('][')):
            tuplesets[b].add(tuple(c + str(i) for i, c in enumerate(chars)))
    res = [lt.filename]
    for bs, tupleset in zip(sorted(lt.bsetdict), tuplesets):
        # a branch is reducible if there is the same combinations for all paths
        try:
            [br_ids] = tupleset
        except ValueError:
            continue
        res.append((bs, [longener[brid] for brid in br_ids]))
    return res


# this is not used right now, but tested
def reduce_full(full_lt, rlz_clusters):
    """
    :param full_lt: a FullLogicTree instance
    :param rlz_clusters: list of paths for a realization cluster
    :returns: a dictionary with what can be reduced
    """
    smrlz_clusters = []
    gsrlz_clusters = []
    for path in rlz_clusters:
        smr, gsr = decode(path).split('~')
        smrlz_clusters.append(smr)
        gsrlz_clusters.append(gsr)
    f1, *p1 = reducible(full_lt.source_model_lt, smrlz_clusters)
    f2, *p2 = reducible(full_lt.gsim_lt, gsrlz_clusters)
    before = (full_lt.source_model_lt.get_num_paths() *
              full_lt.gsim_lt.get_num_paths())
    after = before / prod(len(p[1]) for p in p1 + p2)
    return {f1: dict(p1), f2: dict(p2), 'size_before_after': (before, after)}


class SourceModelLogicTree(object):
    """
    Source model logic tree parser.

    :param filename:
        Full pathname of logic tree file
    :raises LogicTreeError:
        If logic tree file has a logic error, which can not be prevented
        by xml schema rules (like referencing sources with missing id).
    """
    _xmlschema = None

    FILTERS = ('applyToTectonicRegionType',
               'applyToSources',
               'applyToBranches')

    ABSOLUTE_UNCERTAINTIES = ('abGRAbsolute', 'bGRAbsolute',
                              'maxMagGRAbsolute',
                              'simpleFaultGeometryAbsolute',
                              'truncatedGRFromSlipAbsolute',
                              'complexFaultGeometryAbsolute',
                              'setMSRAbsolute')

    @classmethod
    def fake(cls):
        """
        :returns: a fake SourceModelLogicTree with a single branch
        """
        self = object.__new__(cls)
        arr = numpy.array([('bs0', 'b0', 'sourceModel', 'fake.xml', 1)],
                          branch_dt)
        dic = dict(filename='fake.xml', seed=0, num_samples=0,
                   sampling_method='early_weights', num_paths=1,
                   source_ids="{}", is_source_specific=0,
                   bsetdict='{"bs0": {"uncertaintyType": "sourceModel"}}')
        self.__fromh5__(arr, dic)
        return self

    def __init__(self, filename, seed=0, num_samples=0,
                 sampling_method='early_weights', test_mode=False,
                 branchID=None):
        self.filename = filename
        self.basepath = os.path.dirname(filename)
        # NB: converting the random_seed into an integer is needed on Windows
        self.seed = int(seed)
        self.num_samples = num_samples
        self.sampling_method = sampling_method
        self.test_mode = test_mode
        self.branchID = branchID  # used to read only one sourceModel branch
        self.branches = {}  # branch_id -> branch
        self.bsetdict = {}
        self.previous_branches = []
        self.tectonic_region_types = set()
        self.root_branchset = None
        root = nrml.read(filename)
        try:
            tree = root.logicTree
        except AttributeError:
            raise LogicTreeError(
                root, self.filename, "missing logicTree node")
        self.shortener = {}
        self.branchsets = []
        self.parse_tree(tree)

        # determine if the logic tree is source specific
        dicts = list(self.bsetdict.values())[1:]
        if not dicts:
            self.is_source_specific = False
            self.num_paths = count_paths(self.root_branchset.branches)
            return
        src_ids = set()
        for dic in dicts:
            ats = dic.get('applyToSources')
            if not ats:
                self.is_source_specific = False
                self.num_paths = count_paths(self.root_branchset.branches)
                return
            elif len(ats.split()) != 1:
                self.is_source_specific = False
                self.num_paths = count_paths(self.root_branchset.branches)
                return
            src_ids.add(ats)
        # to be source-specific applyToBranches must be trivial
        self.is_source_specific = all(
            bset.applied is None for bset in self.branchsets)
        if self.is_source_specific:
            # fast algorithm, otherwise models like ZAF would hang
            self.num_paths = prod(
                sslt.num_paths for sslt in self.decompose().values())
        else:  # slow algorithm
            self.num_paths = count_paths(self.root_branchset.branches)

    def parse_tree(self, tree_node):
        """
        Parse the whole tree and point ``root_branchset`` attribute
        to the tree's root.
        """
        self.info = collect_info(self.filename, self.branchID)
        self.source_ids = collections.defaultdict(list)  # src_id->branchIDs
        t0 = time.time()
        for depth, blnode in enumerate(tree_node.nodes):
            [bsnode] = bsnodes(self.filename, blnode)
            self.parse_branchset(bsnode, depth)
        dt = time.time() - t0
        bname = os.path.basename(self.filename)
        logging.info('Validated %s in %.2f seconds', bname, dt)

    def parse_branchset(self, branchset_node, depth):
        """
        :param branchset_ node:
            ``etree.Element`` object with tag "logicTreeBranchSet".
        :param depth:
            The sequential number of this branching level, based on 0.

        Enumerates children branchsets and call :meth:`parse_branchset`,
        :meth:`validate_branchset`, :meth:`parse_branches` and finally
        :meth:`apply_branchset` for each.

        Keeps track of "open ends" -- the set of branches that don't have
        any child branchset on this step of execution. After processing
        of every branchset only those branches that are listed in it
        can have child branchsets (if there is one on the next level).
        """
        attrs = branchset_node.attrib.copy()
        uncertainty_type = branchset_node.attrib.get('uncertaintyType')
        dic = dict((filtername, branchset_node.attrib.get(filtername))
                   for filtername in self.FILTERS
                   if filtername in branchset_node.attrib)
        self.validate_filters(branchset_node, uncertainty_type, dic)
        filters = self.parse_filters(branchset_node, uncertainty_type, dic)

        ordinal = len(self.bsetdict)
        branchset = BranchSet(uncertainty_type, ordinal, filters)
        branchset.id = bsid = attrs.pop('branchSetID')
        if bsid in self.bsetdict:
            raise nrml.DuplicatedID('%s in %s' % (bsid, self.filename))
        self.bsetdict[bsid] = attrs
        self.validate_branchset(branchset_node, depth, branchset)
        self.parse_branches(branchset_node, branchset)
        dummies = []  # dummy branches in case of applyToBranches
        if self.root_branchset is None:  # not set yet
            self.root_branchset = branchset
        else:
            prev_ids = ' '.join(pb.branch_id for pb in self.previous_branches)
            app2brs = branchset_node.attrib.get('applyToBranches') or prev_ids
            if app2brs != prev_ids:
                branchset.applied = app2brs
                self.apply_branchset(
                    app2brs, branchset_node.lineno, branchset)
                for brid in set(prev_ids.split()) - set(app2brs.split()):
                    self.branches[brid].bset = dummy = dummy_branchset()
                    [dummybranch] = dummy.branches
                    self.branches[dummybranch.branch_id] = dummybranch
                    dummies.append(dummybranch)
            else:  # apply to all previous branches
                for branch in self.previous_branches:
                    branch.bset = branchset
        self.previous_branches = branchset.branches + dummies
        self.branchsets.append(branchset)

    def get_num_paths(self):
        """
        :returns: the number of paths in the logic tree
        """
        return self.num_samples if self.num_samples else self.num_paths

    def parse_branches(self, branchset_node, branchset):
        """
        Create and attach branches at ``branchset_node`` to ``branchset``.

        :param branchset_node:
            Same as for :meth:`parse_branchset`.
        :param branchset:
            An instance of :class:`BranchSet`.

        Checks that each branch has :meth:`valid <validate_uncertainty_value>`
        value, unique id and that all branches have total weight of 1.0.

        :return:
            ``None``, all branches are attached to provided branchset.
        """
        bs_id = branchset_node['branchSetID']
        weight_sum = 0
        branches = branchset_node.nodes
        if os.environ.get('OQ_REDUCE'):  # only take first branch
            branches = [branches[0]]
            branches[0].uncertaintyWeight.text = 1.
        values = []
        bsno = len(self.branchsets)
        for brno, branchnode in enumerate(branches):
            weight = ~branchnode.uncertaintyWeight
            weight_sum += weight
            value_node = node_from_elem(branchnode.uncertaintyModel)
            if value_node.text is not None:
                values.append(value_node.text.strip())
            if branchset.uncertainty_type in ('sourceModel', 'extendModel'):
                if self.branchID and branchnode['branchID'] != self.branchID:
                    continue
                try:
                    for fname in value_node.text.strip().split():
                        if (fname.endswith(('.xml', '.nrml'))  # except UCERF
                                and not self.test_mode):
                            self.collect_source_model_data(
                                branchnode['branchID'], fname)
                except Exception as exc:
                    raise LogicTreeError(
                        value_node, self.filename, str(exc)) from exc
            value = parse_uncertainty(branchset.uncertainty_type, value_node,
                                      self.filename)
            branch_id = branchnode.attrib.get('branchID')
            branch = Branch(bs_id, branch_id, weight, value)
            if branch_id in self.branches:
                raise LogicTreeError(
                    branchnode, self.filename,
                    "branchID '%s' is not unique" % branch_id)
            self.branches[branch_id] = branch
            self.shortener[branch_id] = keyno(
                branch_id, bsno, brno, self.filename)
            branchset.branches.append(branch)
        if abs(weight_sum - 1.0) > pmf.PRECISION:
            raise LogicTreeError(
                branchset_node, self.filename,
                "branchset weights don't sum up to 1.0")
        if ''.join(values) and len(set(values)) < len(values):
            raise LogicTreeError(
                branchset_node, self.filename,
                "there are duplicate values in uncertaintyModel: " +
                ' '.join(values))

    def __iter__(self):
        """
        Yield Realization tuples. Notice that the weight is homogeneous when
        sampling is enabled, since it is accounted for in the sampling
        procedure.
        """
        if self.num_samples:
            # random sampling of the logic tree
            probs = random((self.num_samples, len(self.bsetdict)),
                           self.seed, self.sampling_method)
            ordinal = 0
            for branches in self.root_branchset.sample(
                    probs, self.sampling_method):
                value = [br.value for br in branches]
                smlt_path_ids = [br.branch_id for br in branches]
                if self.sampling_method.startswith('early_'):
                    weight = 1. / self.num_samples  # already accounted
                elif self.sampling_method.startswith('late_'):
                    weight = numpy.prod([br.weight for br in branches])
                else:
                    raise NotImplementedError(self.sampling_method)
                yield Realization(value, weight, ordinal, tuple(smlt_path_ids))
                ordinal += 1
        else:  # full enumeration
            ordinal = 0
            for weight, branches in self.root_branchset.enumerate_paths():
                value = [br.value for br in branches]
                branch_ids = [branch.branch_id for branch in branches]
                yield Realization(value, weight, ordinal, tuple(branch_ids))
                ordinal += 1

    def parse_filters(self, branchset_node, uncertainty_type, filters):
        """
        Converts "applyToSources" and "applyToBranches" filters by
        splitting into lists.
        """
        if 'applyToSources' in filters:
            filters['applyToSources'] = filters['applyToSources'].split()
        if 'applyToBranches' in filters:
            filters['applyToBranches'] = filters['applyToBranches'].split()
        return filters

    def validate_filters(self, branchset_node, uncertainty_type, filters):
        """
        See superclass' method for description and signature specification.

        Checks that the following conditions are met:

        * "sourceModel" uncertainties can not have filters.
        * Absolute uncertainties must have only one filter --
          "applyToSources", with only one source id.
        * All other uncertainty types can have either no or one filter.
        * Filter "applyToSources" must mention only source ids that
          exist in source models.
        * Filter "applyToTectonicRegionType" must mention only tectonic
          region types that exist in source models.
        """
        f = filters.copy()

        if 'applyToBranches' in f:
            del f['applyToBranches']

        if uncertainty_type == 'sourceModel' and f:
            raise LogicTreeError(
                branchset_node, self.filename,
                'filters are not allowed on source model uncertainty')

        if len(f) > 1:
            raise LogicTreeError(
                branchset_node, self.filename,
                "only one filter is allowed per branchset")

        if 'applyToTectonicRegionType' in f:
            if not f['applyToTectonicRegionType'] \
                    in self.tectonic_region_types:
                raise LogicTreeError(
                    branchset_node, self.filename,
                    "source models don't define sources of tectonic region "
                    "type '%s'" % f['applyToTectonicRegionType'])

        if uncertainty_type in self.ABSOLUTE_UNCERTAINTIES:
            if not f or not list(f) == ['applyToSources'] \
                    or not len(f['applyToSources'].split()) == 1:
                raise LogicTreeError(
                    branchset_node, self.filename,
                    "uncertainty of type '%s' must define 'applyToSources' "
                    "with only one source id" % uncertainty_type)
        if uncertainty_type in ('simpleFaultDipRelative',
                                'simpleFaultDipAbsolute'):
            if not f or 'applyToSources' not in f:
                raise LogicTreeError(
                    branchset_node, self.filename,
                    "uncertainty of type '%s' must define 'applyToSources'"
                    % uncertainty_type)

        if 'applyToSources' in f:
            for source_id in f['applyToSources'].split():
                branchIDs = self.source_ids[source_id]
                if not branchIDs:
                    raise LogicTreeError(
                        branchset_node, self.filename,
                        "source with id '%s' is not defined in source "
                        "models" % source_id)
                elif (len(branchIDs) > 1 and 'applyToBranches' not in
                      branchset_node.attrib):
                    raise LogicTreeError(
                        branchset_node, self.filename,
                        f"{source_id} belongs to multiple branches {branchIDs}"
                        ": applyToBranches"" must be specified together with"
                        " applyToSources")

    def validate_branchset(self, branchset_node, depth, branchset):
        """
        See superclass' method for description and signature specification.

        Checks that the following conditions are met:

        * First branching level must contain exactly one branchset, which
          must be of type "sourceModel".
        * All other branchsets must not be of type "sourceModel"
          or "gmpeModel".
        """
        if depth == 0:
            if branchset.uncertainty_type != 'sourceModel':
                raise LogicTreeError(
                    branchset_node, self.filename,
                    'first branchset must define an uncertainty '
                    'of type "sourceModel"')
        else:
            if branchset.uncertainty_type == 'sourceModel':
                raise LogicTreeError(
                    branchset_node, self.filename,
                    'uncertainty of type "sourceModel" can be defined '
                    'on first branchset only')
            elif branchset.uncertainty_type == 'gmpeModel':
                raise LogicTreeError(
                    branchset_node, self.filename,
                    'uncertainty of type "gmpeModel" is not allowed '
                    'in source model logic tree')

    def apply_branchset(self, apply_to_branches, lineno, branchset):
        """
        See superclass' method for description and signature specification.

        Parses branchset node's attribute ``@applyToBranches`` to apply
        following branchests to preceding branches selectively. Branching
        level can have more than one branchset exactly for this: different
        branchsets can apply to different open ends.

        Checks that branchset tries to be applied only to branches on previous
        branching level which do not have a child branchset yet.
        """
        for branch_id in apply_to_branches.split():
            if branch_id not in self.branches:
                raise LogicTreeError(
                    lineno, self.filename,
                    "branch '%s' is not yet defined" % branch_id)
            branch = self.branches[branch_id]
            if not branch.is_leaf():
                raise LogicTreeError(
                    lineno, self.filename,
                    "branch '%s' already has child branchset" % branch_id)
            branch.bset = branchset

    def _get_source_model(self, source_model_file):
        # NB: do not remove this, it is meant to be overridden in the tests
        return open(os.path.join(self.basepath, source_model_file),
                    encoding='utf-8')

    def collect_source_model_data(self, branch_id, source_model):
        """
        Parse source model file and collect information about source ids,
        source types and tectonic region types available in it. That
        information is used then for :meth:`validate_filters` and
        :meth:`validate_uncertainty_value`.
        """
        # using regular expressions is a lot faster than parsing
        with self._get_source_model(source_model) as sm:
            xml = sm.read()
        self.tectonic_region_types.update(TRT_REGEX.findall(xml))
        for src_id in ID_REGEX.findall(xml):
            self.source_ids[src_id].append(branch_id)

    def collapse(self, branchset_ids):
        """
        Set the attribute .collapsed on the given branchsets
        """
        for bsid, bset in self.bsetdict.items():
            if bsid in branchset_ids:
                bset.collapsed = True

    def bset_values(self, lt_path):
        """
        :param sm_rlz: an effective realization
        :returns: a list of B - 1 pairs (branchset, value)
        """
        return self.root_branchset.get_bset_values(lt_path)[1:]

    # used in the sslt page of the advanced manual
    def decompose(self):
        """
        If the logic tree is source specific, returns a dictionary
        source ID -> SourceLogicTree instance
        """
        assert self.is_source_specific
        bsets = collections.defaultdict(list)
        bsetdict = collections.defaultdict(dict)
        for bset in self.branchsets[1:]:
            if bset.filters['applyToSources']:
                [src_id] = bset.filters['applyToSources']
                bsets[src_id].append(bset)
                bsetdict[src_id][bset.id] = self.bsetdict[bset.id]
        root = self.branchsets[0]
        if len(root) > 1:
            out = {None: SourceLogicTree(None, [root], self.bsetdict[root.id])}
        else:
            out = {}
        # src_id -> SourceLogicTree
        for src_id in bsets:
            out[src_id] = SourceLogicTree(
                src_id, bsets[src_id], bsetdict[src_id])
        return out

    # SourceModelLogicTree
    def __toh5__(self):
        tbl = []
        for brid, br in self.branches.items():
            if br.bs_id.startswith('dummy'):
                continue  # don't store dummy branches
            dic = self.bsetdict[br.bs_id].copy()
            utype = dic['uncertaintyType']
            tbl.append((br.bs_id, brid, utype, repr(br.value), br.weight))
        attrs = dict(bsetdict=json.dumps(self.bsetdict))
        attrs['seed'] = self.seed
        attrs['num_samples'] = self.num_samples
        attrs['sampling_method'] = self.sampling_method
        attrs['filename'] = self.filename
        attrs['num_paths'] = self.num_paths
        attrs['is_source_specific'] = self.is_source_specific
        return numpy.array(tbl, branch_dt), attrs

    # SourceModelLogicTree
    def __fromh5__(self, array, attrs):
        # this is rather tricky; to understand it, run the test
        # SerializeSmltTestCase which has a logic tree with 3 branchsets
        # with the form b11[b21[b31, b32], b22[b31, b32]] and 1 x 2 x 2 rlzs
        vars(self).update(attrs)
        bsets = []
        self.branches = {}
        self.bsetdict = json.loads(attrs['bsetdict'])
        self.shortener = {}
        acc = AccumDict(accum=[])  # bsid -> rows
        for rec in array:
            rec = fix_bytes(rec)
            # NB: it is important to keep the order of the branchsets
            acc[rec['branchset']].append(rec)
        for ordinal, (bsid, rows) in enumerate(acc.items()):
            utype = rows[0]['utype']
            filters = {}
            ats = self.bsetdict[bsid].get('applyToSources')
            atb = self.bsetdict[bsid].get('applyToBranches')
            if ats:
                filters['applyToSources'] = ats.split()
            if atb:
                filters['applyToBranches'] = atb.split()
            bset = BranchSet(utype, ordinal, filters)
            bset.id = bsid
            for no, row in enumerate(rows):
                try:
                    uvalue = ast.literal_eval(row['uvalue'])
                except (SyntaxError, ValueError):
                    uvalue = row['uvalue']  # not really deserializable :-(
                br = Branch(bsid, row['branch'], row['weight'], uvalue)
                self.branches[br.branch_id] = br
                self.shortener[br.branch_id] = keyno(
                    br.branch_id, ordinal, no, attrs['filename'])
                bset.branches.append(br)
            bsets.append(bset)
        CompositeLogicTree(bsets)  # perform attach_to_branches
        self.branchsets = bsets
        # bsets [<b11>, <b21 b22>, <b31 b32>]
        self.root_branchset = bsets[0]

    def __str__(self):
        return '<%s%s>' % (self.__class__.__name__, repr(self.root_branchset))


def capitalize(words):
    """
    Capitalize words separated by spaces.
    """
    return ' '.join(w.capitalize() for w in decode(words).split(' '))


def get_field(data, field, default):
    """
    :param data: a record with a field `field`, possibily missing
    """
    try:
        return data[field]
    except ValueError:  # field missing in old engines
        return default


class LtRealization(object):
    """
    Composite realization build on top of a source model realization and
    a GSIM realization.
    """
    def __init__(self, ordinal, sm_lt_path, gsim_rlz, weight):
        self.ordinal = ordinal
        self.sm_lt_path = tuple(sm_lt_path)
        self.gsim_rlz = gsim_rlz
        self.weight = weight

    def __repr__(self):
        return '<%d,w=%s>' % (self.ordinal, self.weight)

    @property
    def gsim_lt_path(self):
        return self.gsim_rlz.lt_path

    def __lt__(self, other):
        return self.ordinal < other.ordinal

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __ne__(self, other):
        return repr(self) != repr(other)

    def __hash__(self):
        return hash(repr(self))


class FullLogicTree(object):
    """
    The full logic tree as composition of

    :param source_model_lt: :class:`SourceModelLogicTree` object
    :param gsim_lt: :class:`GsimLogicTree` object
    """
    @classmethod
    def fake(cls, gsimlt=None):
        """
        :returns:
            a fake `FullLogicTree` instance with the given gsim logic tree
            object; if None, builds automatically a fake gsim logic tree
        """
        gsim_lt = gsimlt or GsimLogicTree.from_('[FromFile]')
        fakeSM = Realization(
            'scenario', weight=1,  ordinal=0, lt_path='b1', samples=1)
        self = object.__new__(cls)
        self.source_model_lt = SourceModelLogicTree.fake()
        self.gsim_lt = gsim_lt
        self.sm_rlzs = [fakeSM]
        return self

    def __init__(self, source_model_lt, gsim_lt):
        self.source_model_lt = source_model_lt
        self.gsim_lt = gsim_lt
        self.init()  # set .sm_rlzs and .trts

    def init(self):
        if self.source_model_lt.num_samples:
            # NB: the number of effective rlzs can be less than the number
            # of realizations in case of sampling
            self.sm_rlzs = get_effective_rlzs(self.source_model_lt)
        else:  # full enumeration
            samples = self.gsim_lt.get_num_paths()
            self.sm_rlzs = []
            for sm_rlz in self.source_model_lt:
                sm_rlz.samples = samples
                self.sm_rlzs.append(sm_rlz)
        self.trti = {trt: i for i, trt in enumerate(self.gsim_lt.values)}
        self.trts = list(self.gsim_lt.values)

    def get_smr_by_ltp(self):
        """
        :returns: a dictionary sm_lt_path -> effective realization index
        """
        return {'~'.join(sm_rlz.lt_path): i
                for i, sm_rlz in enumerate(self.sm_rlzs)}

    def trt_by(self, trt_smr):
        """
        :returns: the TRT associated to trt_smr
        """
        if len(self.trts) == 1:
            return self.trts[0]
        return self.trts[trt_smr // len(self.sm_rlzs)]

    @property
    def seed(self):
        """
        :returns: the source_model_lt seed
        """
        return self.source_model_lt.seed

    @property
    def num_samples(self):
        """
        :returns: the source_model_lt ``num_samples`` parameter
        """
        return self.source_model_lt.num_samples

    @property
    def sampling_method(self):
        """
        :returns: the source_model_lt ``sampling_method`` parameter
        """
        return self.source_model_lt.sampling_method

    def get_trti_smr(self, trt_smr):
        """
        :returns: (trti, smr)
        """
        return divmod(trt_smr, len(self.sm_rlzs))

    def get_trt_smr(self, trt, smr):
        """
        :returns: trt_smr
        """
        if self.trti == {'*': 0}:  # passed gsim=XXX in the job.ini
            return int(smr)
        return self.trti[trt] * len(self.sm_rlzs) + int(smr)

    def get_trt_smrs(self, smr):
        """
        :param smr: effective realization index
        :returns: array of T group IDs, being T the number of TRTs
        """
        nt = len(self.gsim_lt.values)
        ns = len(self.sm_rlzs)
        return smr + numpy.arange(nt) * ns

    def gsim_by_trt(self, rlz):
        """
        :returns: a dictionary trt->gsim for the given realization
        """
        return dict(zip(self.gsim_lt.values, rlz.gsim_rlz.value))

    def get_num_paths(self):
        """
        :returns: number of the paths in the full logic tree
        """
        if self.num_samples:
            return self.num_samples
        return len(self.sm_rlzs) * self.gsim_lt.get_num_paths()

    def get_realizations(self):
        """
        :returns: the complete list of LtRealizations
        """
        rlzs = []
        self._gsims_by_trt = AccumDict(accum=set())  # trt -> gsims
        if self.num_samples:  # sampling
            sm_rlzs = []
            for sm_rlz in self.sm_rlzs:
                sm_rlzs.extend([sm_rlz] * sm_rlz.samples)
            gsim_rlzs = self.gsim_lt.sample(self.num_samples, self.seed + 1,
                                            self.sampling_method)
            for t, trt in enumerate(self.gsim_lt.values):
                self._gsims_by_trt[trt].update(g.value[t] for g in gsim_rlzs)
            for i, gsim_rlz in enumerate(gsim_rlzs):
                rlz = LtRealization(i, sm_rlzs[i].lt_path, gsim_rlz,
                                    sm_rlzs[i].weight * gsim_rlz.weight)
                rlzs.append(rlz)
        else:  # full enumeration
            gsim_rlzs = list(self.gsim_lt)
            self._gsims_by_trt = self.gsim_lt.values
            i = 0
            for sm_rlz in self.sm_rlzs:
                for gsim_rlz in gsim_rlzs:
                    rlz = LtRealization(i, sm_rlz.lt_path, gsim_rlz,
                                        sm_rlz.weight * gsim_rlz.weight)
                    rlzs.append(rlz)
                    i += 1
        assert rlzs, 'No realizations found??'
        if self.num_samples and self.sampling_method.startswith('early_'):
            assert len(rlzs) == self.num_samples, (len(rlzs), self.num_samples)
            for rlz in rlzs:
                for k in rlz.weight.dic:
                    rlz.weight.dic[k] = 1. / self.num_samples
        else:  # keep the weights
            tot_weight = sum(rlz.weight for rlz in rlzs)
            if not tot_weight.is_one():
                # this may happen for rounding errors; we ensure the sum of
                # the weights is 1
                for rlz in rlzs:
                    rlz.weight = rlz.weight / tot_weight
        return rlzs

    def get_rlzs_by_smr(self):
        """
        :returns: a dict smr -> rlzs
        """
        smltpath = operator.attrgetter('sm_lt_path')
        smr_by_ltp = self.get_smr_by_ltp()
        rlzs = self.get_realizations()
        dic = {smr_by_ltp['~'.join(ltp)]: rlzs for ltp, rlzs in groupby(
            rlzs, smltpath).items()}
        return dic

    def _rlzs_by_gsim(self, grp_id):
        """
        :returns: a dictionary gsim -> array of rlz indices
        """
        if not hasattr(self, '_rlzs_by_grp'):
            smr_by_ltp = self.get_smr_by_ltp()
            rlzs = self.get_realizations()
            acc = AccumDict(accum=AccumDict(accum=[]))  # trt_smr->gsim->rlzs
            for sm in self.sm_rlzs:
                for gid in self.get_trt_smrs(sm.ordinal):
                    trti, smr = divmod(gid, len(self.sm_rlzs))
                    for rlz in rlzs:
                        idx = smr_by_ltp['~'.join(rlz.sm_lt_path)]
                        if idx == smr:
                            acc[gid][rlz.gsim_rlz.value[trti]].append(
                                rlz.ordinal)
            self._rlzs_by_grp = {}
            for gid, dic in acc.items():
                self._rlzs_by_grp[gid] = {
                    gsim: U32(rlzs) for gsim, rlzs in sorted(dic.items())}
        return self._rlzs_by_grp[grp_id]

    def get_rlzs_by_gsim(self):
        """
        :returns: a dictionary trt_smr -> gsim -> rlzs
        """
        dic = {}
        for sm in self.sm_rlzs:
            for trt_smr in self.get_trt_smrs(sm.ordinal):
                dic[trt_smr] = self._rlzs_by_gsim(trt_smr)
        return dic

    def get_rlzs_by_grp(self):
        """
        :returns: a dictionary grp_id -> [rlzis, ...]
        """
        dic = {}
        for sm in self.sm_rlzs:
            for trt_smr in self.get_trt_smrs(sm.ordinal):
                grp = 'grp-%02d' % trt_smr
                dic[grp] = list(self._rlzs_by_gsim(trt_smr).values())
        return {grp_id: dic[grp_id] for grp_id in sorted(dic)}

    def get_rlzs_by_gsim_list(self, list_of_trt_smrs):
        """
        :returns: a list of dictionaries rlzs_by_gsim, one for each grp_id
        """
        out = []
        for grp_id, trt_smrs in enumerate(list_of_trt_smrs):
            dic = AccumDict(accum=[])
            for trt_smr in trt_smrs:
                for gsim, rlzs in self._rlzs_by_gsim(trt_smr).items():
                    dic[gsim].extend(rlzs)
            out.append(dic)
        return out

    # FullLogicTree
    def __toh5__(self):
        sm_data = []
        for sm in self.sm_rlzs:
            sm_data.append((str(sm.value), sm.weight,
                            '~'.join(sm.lt_path), sm.samples))
        return (dict(
            source_model_lt=self.source_model_lt,
            gsim_lt=self.gsim_lt,
            sm_data=numpy.array(sm_data, source_model_dt)),
                dict(seed=self.seed, num_samples=self.num_samples,
                     trts=hdf5.array_of_vstr(self.gsim_lt.values)))

    # FullLogicTree
    def __fromh5__(self, dic, attrs):
        # TODO: this is called more times than needed, maybe we should cache it
        sm_data = dic['sm_data']
        vars(self).update(attrs)
        self.source_model_lt = dic['source_model_lt']
        self.gsim_lt = dic['gsim_lt']
        self.sm_rlzs = []
        for sm_id, rec in enumerate(sm_data):
            path = tuple(str(decode(rec['path'])).split('~'))
            sm = Realization(
                rec['name'], rec['weight'], sm_id, path, rec['samples'])
            self.sm_rlzs.append(sm)

    def get_num_rlzs(self, sm_rlz=None):
        """
        :param sm_rlz: a Realization instance (or None)
        :returns: the number of realizations per source model (or all)
        """
        if sm_rlz is None:
            return sum(self.get_num_rlzs(sm) for sm in self.sm_rlzs)
        if self.num_samples:
            return sm_rlz.samples
        return self.gsim_lt.get_num_paths()

    def get_num_potential_paths(self):
        """
         :returns: the number of potential realizations
        """
        return self.gsim_lt.get_num_paths() * self.source_model_lt.num_paths

    @property
    def rlzs(self):
        """
        :returns: an array of realizations
        """
        sh1 = self.source_model_lt.shortener
        sh2 = self.gsim_lt.shortener
        tups = []
        for r in self.get_realizations():
            path = '%s~%s' % (shorten(r.sm_lt_path, sh1),
                              shorten(r.gsim_rlz.lt_path, sh2))
            tups.append((r.ordinal, path, r.weight['weight']))
        return numpy.array(tups, rlz_dt)

    def get_gsims_by_trt(self):
        """
        :returns: a dictionary trt -> sorted gsims
        """
        if not hasattr(self, '_gsims_by_trt'):
            self.get_realizations()
        return {trt: sorted(gs) for trt, gs in self._gsims_by_trt.items()}

    def get_sm_by_grp(self):
        """
        :returns: a dictionary trt_smr -> sm_id
        """
        return {trt_smr: sm.ordinal for sm in self.sm_rlzs
                for trt_smr in self.get_trt_smrs(sm.ordinal)}

    def __repr__(self):
        info_by_model = {}
        for sm in self.sm_rlzs:
            info_by_model[sm.lt_path] = (
                '~'.join(map(decode, sm.lt_path)),
                decode(sm.value), sm.weight, self.get_num_rlzs(sm))
        summary = ['%s, %s, weight=%s: %d realization(s)' % ibm
                   for ibm in info_by_model.values()]
        return '<%s\n%s>' % (self.__class__.__name__, '\n'.join(summary))


class SourceLogicTree(object):
    """
    Source specific logic tree (full enumeration)
    """
    def __init__(self, source_id, branchsets, bsetdict):
        self.source_id = source_id
        self.bsetdict = bsetdict
        branchsets = [copy.copy(bset) for bset in branchsets]
        self.root_branchset = branchsets[0]
        self.num_paths = 1
        for child, parent in zip(branchsets[1:] + [None], branchsets):
            branches = [copy.copy(br) for br in parent.branches]
            for br in branches:
                br.bset = child
            parent.branches = branches
            self.num_paths *= len(branches)
        self.branchsets = branchsets
        self.num_samples = 0

    __iter__ = SourceModelLogicTree.__iter__

    def get_num_paths(self):
        return self.num_paths

    def __repr__(self):
        return '<SSLT:%s %s>' % (self.source_id, self.branchsets)


def compose(source_model_lt, gsim_lt):
    """
    :returns: a CompositeLogicTree instance
    """
    bsets = []
    dic = groupby(gsim_lt.branches, operator.attrgetter('trt'))
    bsno = len(source_model_lt.branchsets)
    for trt, btuples in dic.items():
        bsid = gsim_lt.bsetdict[trt]
        bset = BranchSet('gmpeModel', bsno)
        bset.branches = [Branch(bsid, bt.id, bt.weight['weight'], bt.gsim)
                         for bt in btuples]  # branch ID fixed later
        bsets.append(bset)
        bsno += 1
    clt = CompositeLogicTree(source_model_lt.branchsets + bsets)
    return clt
