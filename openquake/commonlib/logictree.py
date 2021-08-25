# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2021 GEM Foundation
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
    GsimLogicTree, Realization, bsnodes, fix_bytes, keyno)
from openquake.hazardlib.lt import (
    Branch, BranchSet, LogicTreeError, parse_uncertainty, random)

TRT_REGEX = re.compile(r'tectonicRegion="([^"]+?)"')
ID_REGEX = re.compile(r'id="([^"]+?)"')
SOURCE_TYPE_REGEX = re.compile(r'<(\w+Source)\b')

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


Info = collections.namedtuple('Info', 'smpaths, applytosources')


def collect_info(smlt):
    """
    Given a path to a source model logic tree, collect all of the
    path names to the source models it contains and build:

    1. a dictionary source model branch ID -> paths
    2. a dictionary source model branch ID -> source IDs in applyToSources

    :param smlt: source model logic tree file
    :returns: an Info namedtupled containing the two dictionaries
    """
    n = nrml.read(smlt)
    try:
        blevels = n.logicTree
    except Exception:
        raise InvalidFile('%s is not a valid source_model_logic_tree_file'
                          % smlt)
    paths = set()
    applytosources = collections.defaultdict(list)  # branchID -> source IDs
    for blevel in blevels:
        for bset in bsnodes(smlt, blevel):
            if 'applyToSources' in bset.attrib:
                applytosources[bset.get('applyToBranches')].extend(
                        bset['applyToSources'].split())
            if bset['uncertaintyType'] in 'sourceModel extendModel':
                for br in bset:
                    with context(smlt, br):
                        fnames = unique(br.uncertaintyModel.text.split())
                        paths.update(_abs_paths(smlt, fnames))
    return Info(sorted(paths), applytosources)


def _abs_paths(smlt, fnames):
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


def shorten(path, shortener):
    """
    :path:  sequence of strings
    :shortener: dictionary longstring -> shortstring
    :returns: shortened version of the path
    """
    return ''.join(shortener.get(key, key) for key in path)


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
    bsets = [set() for _ in lt.bsetdict]
    for path in cluster_paths:
        for b, chars in enumerate(path.strip('][').split('][')):
            bsets[b].add(chars)
    res = [lt.filename]
    for bs, bset in zip(sorted(lt.bsetdict), bsets):
        # a branch is reducible if there the same combinations for all paths
        try:
            [br_ids] = bset
        except ValueError:
            continue
        res.append((bs, [longener[c] for c in br_ids]))
    return res


# this is used in oq reduce_lt
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
    after = before / numpy.prod([len(p[1]) for p in p1 + p2])
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
               'applyToSourceType')

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
                   bsetdict='{"bs0": {"uncertaintyType": "sourceModel"}}')
        self.__fromh5__(arr, dic)
        return self

    def __init__(self, filename, seed=0, num_samples=0,
                 sampling_method='early_weights', test_mode=False):
        self.filename = filename
        self.basepath = os.path.dirname(filename)
        # NB: converting the random_seed into an integer is needed on Windows
        self.seed = int(seed)
        self.num_samples = num_samples
        self.sampling_method = sampling_method
        self.test_mode = test_mode
        self.branches = {}  # branch_id -> branch
        self.bsetdict = {}
        self.previous_branches = []
        self.tectonic_region_types = set()
        self.source_types = set()
        self.hdf5_files = set()
        self.root_branchset = None
        root = nrml.read(filename)
        try:
            tree = root.logicTree
        except AttributeError:
            raise LogicTreeError(
                root, self.filename, "missing logicTree node")
        self.shortener = {}
        self.parse_tree(tree)

    @property
    def on_each_source(self):
        """
        True if there is an applyToSources for each source.
        """
        return (self.info.applytosources and
                self.info.applytosources == self.source_ids)

    def parse_tree(self, tree_node):
        """
        Parse the whole tree and point ``root_branchset`` attribute
        to the tree's root.
        """
        self.info = collect_info(self.filename)
        self.source_ids = collections.defaultdict(list)
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
        filters = dict((filtername, branchset_node.attrib.get(filtername))
                       for filtername in self.FILTERS
                       if filtername in branchset_node.attrib)
        self.validate_filters(branchset_node, uncertainty_type, filters)

        filters = self.parse_filters(branchset_node, uncertainty_type, filters)
        branchset = BranchSet(uncertainty_type, len(self.bsetdict), filters)
        self.bsetdict[attrs.pop('branchSetID')] = attrs
        self.validate_branchset(branchset_node, depth, branchset)

        self.parse_branches(branchset_node, branchset)
        if self.root_branchset is None:  # not set yet
            self.num_paths = 1
            self.root_branchset = branchset
        else:
            apply_to_branches = branchset_node.attrib.get('applyToBranches')
            if apply_to_branches:
                self.apply_branchset(
                    apply_to_branches, branchset_node.lineno, branchset)
            else:
                for branch in self.previous_branches:
                    branch.bset = branchset
        self.previous_branches = branchset.branches
        self.num_paths *= len(branchset.branches)

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
        values = []
        for no, branchnode in enumerate(branches):
            weight = ~branchnode.uncertaintyWeight
            weight_sum += weight
            value_node = node_from_elem(branchnode.uncertaintyModel)
            if value_node.text is not None:
                values.append(value_node.text.strip())
            if branchset.uncertainty_type in ('sourceModel', 'extendModel'):
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
            self.shortener[branch_id] = keyno(branch_id, no, self.filename)
            branchset.branches.append(branch)
        if abs(weight_sum - 1.0) > pmf.PRECISION:
            raise LogicTreeError(
                branchset_node, self.filename,
                "branchset weights don't sum up to 1.0")
        if len(set(values)) < len(values):
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
                name = branches[0].value
                smlt_path_ids = [br.branch_id for br in branches]
                if self.sampling_method.startswith('early_'):
                    weight = 1. / self.num_samples  # already accounted
                elif self.sampling_method.startswith('late_'):
                    weight = numpy.prod([br.weight for br in branches])
                else:
                    raise NotImplementedError(self.sampling_method)
                yield Realization(name, weight, ordinal, tuple(smlt_path_ids))
                ordinal += 1
        else:  # full enumeration
            ordinal = 0
            for weight, branches in self.root_branchset.enumerate_paths():
                name = branches[0].value  # source model name
                branch_ids = [branch.branch_id for branch in branches]
                yield Realization(name, weight, ordinal, tuple(branch_ids))
                ordinal += 1

    def parse_filters(self, branchset_node, uncertainty_type, filters):
        """
        See superclass' method for description and signature specification.

        Converts "applyToSources" filter value by just splitting it to a list.
        """
        if 'applyToSources' in filters:
            filters['applyToSources'] = filters['applyToSources'].split()
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
        * Filter "applyToSourceType" must mention only source types
          that exist in source models.
        """
        if uncertainty_type == 'sourceModel' and filters:
            raise LogicTreeError(
                branchset_node, self.filename,
                'filters are not allowed on source model uncertainty')

        if len(filters) > 1:
            raise LogicTreeError(
                branchset_node, self.filename,
                "only one filter is allowed per branchset")

        if 'applyToTectonicRegionType' in filters:
            if not filters['applyToTectonicRegionType'] \
                    in self.tectonic_region_types:
                raise LogicTreeError(
                    branchset_node, self.filename,
                    "source models don't define sources of tectonic region "
                    "type '%s'" % filters['applyToTectonicRegionType'])

        if uncertainty_type in self.ABSOLUTE_UNCERTAINTIES:
            if not filters or not list(filters) == ['applyToSources'] \
                    or not len(filters['applyToSources'].split()) == 1:
                raise LogicTreeError(
                    branchset_node, self.filename,
                    "uncertainty of type '%s' must define 'applyToSources' "
                    "with only one source id" % uncertainty_type)
        if uncertainty_type in ('simpleFaultDipRelative',
                                'simpleFaultDipAbsolute'):
            if not filters or (not ('applyToSources' in filters) and not
                               ('applyToSourceType' in filters)):
                raise LogicTreeError(
                    branchset_node, self.filename,
                    "uncertainty of type '%s' must define either"
                    "'applyToSources' or 'applyToSourceType'"
                    % uncertainty_type)

        if 'applyToSourceType' in filters:
            if not filters['applyToSourceType'] in self.source_types:
                raise LogicTreeError(
                    branchset_node, self.filename,
                    "source models don't define sources of type '%s'" %
                    filters['applyToSourceType'])

        if 'applyToSources' in filters:
            if (len(self.source_ids) > 1 and 'applyToBranches' not in
                    branchset_node.attrib):
                raise LogicTreeError(
                    branchset_node, self.filename, "applyToBranch must be "
                    "specified together with applyToSources")
            for source_id in filters['applyToSources'].split():
                cnt = sum(source_id in source_ids
                          for source_ids in self.source_ids.values())
                if cnt == 0:
                    raise LogicTreeError(
                        branchset_node, self.filename,
                        "source with id '%s' is not defined in source "
                        "models" % source_id)

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
            if branch.bset is not None:
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
        hdf5_file = os.path.splitext(source_model)[0] + '.hdf5'
        if os.path.exists(hdf5_file):
            self.hdf5_files.add(hdf5_file)
        self.tectonic_region_types.update(TRT_REGEX.findall(xml))
        self.source_ids[branch_id].extend(ID_REGEX.findall(xml))
        self.source_types.update(SOURCE_TYPE_REGEX.findall(xml))

    def collapse(self, branchset_ids):
        """
        Set the attribute .collapsed on the given branchsets
        """
        for bsid, bset in self.bsetdict.items():
            if bsid in branchset_ids:
                bset.collapsed = True

    def bset_values(self, sm_rlz):
        """
        :param sm_rlz: an effective realization
        :returns: a list of B - 1 pairs (branchset, value)
        """
        return self.root_branchset.get_bset_values(sm_rlz.lt_path)[1:]

    # SourceModelLogicTree
    def __toh5__(self):
        tbl = []
        for brid, br in self.branches.items():
            dic = self.bsetdict[br.bs_id].copy()
            utype = dic['uncertaintyType']
            tbl.append((br.bs_id, brid, utype, str(br.value), br.weight))
        attrs = dict(bsetdict=json.dumps(self.bsetdict))
        attrs['seed'] = self.seed
        attrs['num_samples'] = self.num_samples
        attrs['sampling_method'] = self.sampling_method
        attrs['filename'] = self.filename
        attrs['num_paths'] = self.num_paths
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
            bset = BranchSet(utype, ordinal, filters=[])  # TODO: filters
            bset.id = bsid
            for no, row in enumerate(rows):
                br = Branch(bsid, row['branch'], row['weight'], row['uvalue'])
                self.branches[br.branch_id] = br
                self.shortener[br.branch_id] = keyno(
                    br.branch_id, no, attrs['filename'])
                bset.branches.append(br)
            bsets.append(bset)
        # bsets [<b11>, <b21 b22>, <b31 b32>]
        self.root_branchset = bsets[0]
        for i, childset in enumerate(bsets[1:]):
            dic = self.bsetdict[childset.id]
            atb = dic.get('applyToBranches')
            for branch in bsets[i].branches:  # parent branches
                if not atb or branch.branch_id in atb:
                    branch.bset = childset

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
        gid = self.trti[trt] * len(self.sm_rlzs) + int(smr)
        return gid

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
            sm_data.append((sm.value, sm.weight, '~'.join(sm.lt_path),
                            sm.samples))
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
