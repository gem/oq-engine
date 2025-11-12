# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2025 GEM Foundation
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
from openquake.baselib import hdf5, node
from openquake.baselib.python3compat import decode
from openquake.baselib.node import node_from_elem, context, Node
from openquake.baselib.general import (
    cached_property, groupby, group_array, AccumDict, BASE183)
from openquake.hazardlib import nrml, InvalidFile, pmf, valid
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib.gsim_lt import (
    GsimLogicTree, bsnodes, fix_bytes, keyno, abs_paths)
from openquake.hazardlib.lt import (
    Branch, BranchSet, count_paths, Realization, CompositeLogicTree,
    dummy_branchset, LogicTreeError, parse_uncertainty)

U16 = numpy.uint16
U32 = numpy.uint32
I32 = numpy.int32
F32 = numpy.float32
TWO24 = 2 ** 24

rlz_dt = numpy.dtype([
    ('ordinal', U32),
    ('branch_path', hdf5.vstr),
    ('weight', F32),
])

source_dt = numpy.dtype([
    ('branch', hdf5.vstr),
    ('trt', hdf5.vstr),
    ('fname', hdf5.vstr),  # useful to reduce the XML files
    ('source', hdf5.vstr),
])

source_model_dt = numpy.dtype([
    ('name', hdf5.vstr),
    ('weight', F32),
    ('path', hdf5.vstr),
    ('samples', U32),
])

src_group_dt = numpy.dtype([
    ('trt_smr', U32),
    ('name', hdf5.vstr),
    ('trti', U16),
    ('effrup', I32),
    ('totrup', I32),
    ('sm_id', U32),
])

branch_dt = numpy.dtype([
    ('branchset', hdf5.vstr),
    ('branch', hdf5.vstr),
    ('utype', hdf5.vstr),
    ('uvalue', hdf5.vstr),
    ('weight', float),
])

TRT_REGEX = re.compile(r'tectonicRegion="([^"]+?)"')
ID_REGEX = re.compile(r'Source\s+id="([^"]+?)"')
OQ_REDUCE = os.environ.get('OQ_REDUCE') == 'smlt'


def check_unique_uncertainties(source_specific_lts):
    """
    Make sure that each uncertainty in the underlying logic trees is unique
    """
    for sslt in source_specific_lts:
        utypes = [bset.uncertainty_type for bset in sslt.branchsets]
        if len(utypes) > len(set(utypes)):
            raise nrml.DuplicatedID(utypes)


# this is very fast
def get_trt_by_src(source_model_file, source_id=''):
    """
    :returns: a dictionary source ID -> tectonic region type of the source
    """
    xml = source_model_file.read()
    trt_by_src = {}
    if "http://openquake.org/xmlns/nrml/0.5" in xml:
        # fast lane using regex, tectonicRegion is always before Source id
        pieces = TRT_REGEX.split(xml.replace("'", '"'))  # fix single quotes
        for text, trt in zip(pieces[2::2], pieces[1::2]):
            for src_id in ID_REGEX.findall(text):
                # disagg/case_12
                src_id = src_id.split(':')[0]  # colon convention
                if source_id:
                    if src_id.startswith(source_id):
                        trt_by_src[src_id] = trt
                else:
                    trt_by_src[src_id] = trt
    else:  # parse the XML with ElementTree
        for src in node.fromstring(xml)[0]:
            src_id = src.attrib['id'].split(':')[0]  # colon convention
            if source_id:
                if src_id.startswith(source_id):
                    trt_by_src[src_id] = src.attrib['tectonicRegion']
            else:
                trt_by_src[src_id] = src.attrib['tectonicRegion']
    return trt_by_src


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

    :param rlzs: a list of Realization instances with a .pid property
    """
    effective = []
    ordinal = 0
    for group in groupby(rlzs, operator.attrgetter('pid')).values():
        rlz = group[0]
        effective.append(
            Realization(rlz.value, sum(r.weight for r in group),
                        ordinal, rlz.lt_path, len(group)))
        ordinal += 1
    return effective


def get_eff_rlzs(sm_rlzs, gsim_rlzs):
    """
    Group together realizations with the same path
    and yield the first representative of each group
    """
    triples = []  # pid, sm_rlz, gsim_rlz
    for sm_rlz, gsim_rlz in zip(sm_rlzs, gsim_rlzs):
        triples.append((sm_rlz.pid + '~' + gsim_rlz.pid, sm_rlz, gsim_rlz))
    ordinal = 0
    effective = []
    for rows in groupby(triples, operator.itemgetter(0)).values():
        _pid, sm_rlz, gsim_rlz = rows[0]
        weight = numpy.array([len(rows) / len(triples)])
        effective.append(
            LtRealization(ordinal, sm_rlz.lt_path, gsim_rlz, weight))
        ordinal += 1
    return effective


Info = collections.namedtuple('Info', 'smpaths h5paths applytosources')


def collect_info(smltpath, branchID=''):
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
                    if OQ_REDUCE:  # only take first branch
                        break
    return Info(sorted(smpaths), sorted(h5paths), applytosources)


def reduce_fnames(fnames, source_id):
    """
    If the source ID is ambiguous (i.e. there is "!") only returns
    the filenames containing the source, otherwise return all the filenames
    """
    try:
        _srcid, fname = source_id.split('!')
    except ValueError:
        return fnames
    return [f for f in fnames if fname in f]


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


def shorten(path_tuple, shortener, kind):
    """
    :param path: sequence of strings
    :param shortener: dictionary longstring -> shortstring
    :param kind: 'smlt' or 'gslt'
    :returns: shortened version of the path
    """
    # NB: path_tuple can have the form ('EDF_areas',
    # 'Mmax:10-br#0', 'Mmax:11-br#0', ..., 'ab:4014-br#23')
    # with shortener['EDF_areas'] = 'A0',
    # shortener['ab:4014-br#23'] = 'X138'
    if len(shortener) == 1:
        return 'A'
    chars = []
    for bsno, key in enumerate(path_tuple):
        if key[0] == '.':  # dummy branch
            chars.append('.')
        else:
            # shortener[key] has the form letter+number
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

    @classmethod
    def trivial(cls, source_model_file, sampling_method='early_weights',
                source_id=''):
        """
        :returns: a trivial SourceModelLogicTree with a single branch
        """
        self = object.__new__(cls)
        self.basepath = os.path.dirname(source_model_file)
        self.source_id = source_id
        self.source_data = []
        if source_model_file == '_fake.xml':
            self.tectonic_region_types = {'*'}
        else:
            self.tectonic_region_types = set()
            self.collect_source_model_data('br0', source_model_file)
        self.source_data = numpy.array(self.source_data, source_dt)
        self.info = Info([source_model_file], [],
                         collections.defaultdict(list))
        arr = numpy.array(
            [('bs0', 'br0', 'sourceModel', source_model_file, 1)], branch_dt)
        dic = dict(filename=source_model_file, seed=0, num_samples=0,
                   sampling_method=sampling_method, num_paths=1,
                   is_source_specific=0, source_data=self.source_data,
                   tectonic_region_types=self.tectonic_region_types,
                   source_id=source_id, branchID='',
                   bsetdict='{"bs0": {"uncertaintyType": "sourceModel"}}')
        self.__fromh5__(arr, dic)
        return self

    @classmethod
    def fake(cls):
        """
        :returns: a fake SourceModelLogicTree with a single branch
        """
        return cls.trivial('_fake.xml')

    def __init__(self, filename, seed=0, num_samples=0,
                 sampling_method='early_weights', test_mode=False,
                 branchID='', source_id=''):
        self.filename = filename
        self.basepath = os.path.dirname(filename)
        # NB: converting the random_seed into an integer is needed on Windows
        self.seed = int(seed)
        self.num_samples = num_samples
        self.sampling_method = sampling_method
        self.test_mode = test_mode
        self.branchID = branchID  # used to read only one sourceModel branch
        self.source_id = source_id
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
        self.set_num_paths()

    def set_num_paths(self):
        """
        Count the total number of paths in a smart way
        """
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
            sslts = self.decompose().values()
            self.num_paths = prod(sslt.num_paths for sslt in sslts)
            check_unique_uncertainties(sslts)
        else:  # slow algorithm
            self.num_paths = count_paths(self.root_branchset.branches)

    def reduce(self, source_id, num_samples=None):
        """
        :returns: a new logic tree reduced to a single source
        """
        # NB: source_id contains "@" in the case of a split multi fault source
        num_samples = self.num_samples if num_samples is None else num_samples
        new = self.__class__(self.filename, self.seed, num_samples,
                             self.sampling_method, self.test_mode,
                             self.branchID, source_id)
        return new

    def parse_tree(self, tree_node):
        """
        Parse the whole tree and point ``root_branchset`` attribute
        to the tree's root.
        """
        t0 = time.time()
        self.info = collect_info(self.filename, self.branchID)
        # the list is populated in collect_source_model_data
        self.source_data = []
        for bsno, bnode in enumerate(tree_node.nodes):
            [bsnode] = bsnodes(self.filename, bnode)
            self.parse_branchset(bsnode, bsno)
        self.source_data = numpy.array(self.source_data, source_dt)
        unique = numpy.unique(self.source_data['fname'])
        dt = time.time() - t0
        logging.debug('Validated source model logic tree with %d underlying '
                      'files in %.2f seconds', len(unique), dt)

    def parse_branchset(self, branchset_node, bsno):
        """
        :param branchset_ node:
            ``etree.Element`` object with tag "logicTreeBranchSet".
        :param bsno:
            The sequential number of the branchset, starting from 0.

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
        if 'applyToSources' in filters and not filters['applyToSources']:
            return  # ignore the branchset

        branchset = BranchSet(uncertainty_type, filters, len(self.bsetdict))
        branchset.id = bsid = attrs.pop('branchSetID')
        if bsid in self.bsetdict:
            raise nrml.DuplicatedID('%s in %s' % (bsid, self.filename))
        self.bsetdict[bsid] = attrs
        self.validate_branchset(branchset_node, bsno, branchset)
        self.parse_branches(branchset_node, branchset)

        dummies = []  # dummy branches in case of applyToBranches
        if self.root_branchset is None:  # not set yet
            self.root_branchset = branchset
        if not branchset.branches:
            del self.bsetdict[bsid]
            return
        prev_ids = ' '.join(pb.branch_id for pb in self.previous_branches)
        app2brs = branchset_node.attrib.get('applyToBranches') or prev_ids
        missing = set(prev_ids.split()) - set(app2brs.split())
        if missing:
            # apply only to some branches
            branchset.applied = app2brs
            self.apply_branchset(
                app2brs, branchset_node.lineno, branchset)
            not_applied = set(prev_ids.split()) - set(app2brs.split())
            for brid in not_applied:
                if brid in self.branches:
                    self.branches[brid].bset = dummy = dummy_branchset()
                    [dummybranch] = dummy.branches
                    self.branches[dummybranch.branch_id] = dummybranch
                    dummies.append(dummybranch)
        else:
            # apply to all previous branches
            for branch in self.previous_branches:
                branch.bset = branchset
        self.previous_branches = branchset.branches + dummies
        self.branchsets.append(branchset)

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
        if OQ_REDUCE:  # only take first branch
            branches = [branches[0]]
            branches[0].uncertaintyWeight.text = 1.
        values = []
        bsno = len(self.branchsets)
        zeros = []
        maxlen = len(BASE183)
        if self.branchID == '' and len(branches) > maxlen:
            msg = ('%s: the branchset %s has too many branches (%d > %d)\n'
                   'you should split it, see https://docs.openquake.org/'
                   'oq-engine/advanced/latest/logic_trees.html')
            raise InvalidFile(
                msg % (self.filename, bs_id, len(branches), maxlen))
        for brno, branchnode in enumerate(branches):
            weight = ~branchnode.uncertaintyWeight
            value_node = node_from_elem(branchnode.uncertaintyModel)
            if value_node.text is not None:
                values.append(value_node.text.strip())
            value = parse_uncertainty(branchset.uncertainty_type,
                                      value_node, self.filename)
            if branchset.uncertainty_type in ('sourceModel', 'extendModel'):
                vals = []  # filenames with sources in it
                try:
                    for fname in value_node.text.split():
                        if (fname.endswith(('.xml', '.nrml'))
                                and not self.test_mode):
                            ok = self.collect_source_model_data(
                                branchnode['branchID'], fname)
                            if ok:
                                vals.append(fname)
                except Exception as exc:
                    raise LogicTreeError(
                        value_node, self.filename, str(exc)) from exc
                if (self.branchID and self.branchID not in
                        branchnode['branchID']):
                    value = ''  # reduce all branches except branchID
                elif self.source_id:  # only the files containing source_id
                    srcid = self.source_id.split('@')[0]
                    value = ' '.join(reduce_fnames(vals, srcid))
            branch_id = branchnode.attrib.get('branchID')
            if branch_id in self.branches:
                raise LogicTreeError(
                    branchnode, self.filename,
                    "branchID '%s' is not unique" % branch_id)
            if value == '':
                # with logic tree reduction a branch can be empty
                # see case_68_bis
                zero_id = branch_id
                zeros.append(weight)
            else:
                branch = Branch(branch_id, value, weight, bs_id)
                self.branches[branch_id] = branch
                branchset.branches.append(branch)
            self.shortener[branch_id] = keyno(branch_id, bsno, brno, BASE183)
            weight_sum += weight
        if zeros:
            branch = Branch(zero_id, '', sum(zeros), bs_id)
            self.branches[branch_id] = branch
            branchset.branches.append(branch)

        if abs(weight_sum - 1.0) > pmf.PRECISION:
            raise LogicTreeError(
                branchset_node, self.filename,
                f"branchset weights sum up to {weight_sum}, not 1")
        if ''.join(values) and len(set(values)) < len(values):
            raise LogicTreeError(
                branchset_node, self.filename,
                "there are duplicate values in uncertaintyModel: " +
                ' '.join(values))

    def get_num_paths(self):
        """
        :returns: the number of paths in the logic tree
        """
        return self.num_samples if self.num_samples else self.num_paths

    __iter__ = CompositeLogicTree.__iter__

    def parse_filters(self, branchset_node, uncertainty_type, filters):
        """
        Converts "applyToSources" and "applyToBranches" filters by
        splitting into lists.
        """
        if 'applyToSources' in filters:
            srcs = filters['applyToSources'].split()
            if self.source_id:
                srcs = [src for src in srcs if src == self.source_id]
            filters['applyToSources'] = srcs
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
            if f['applyToTectonicRegionType'] \
                    not in self.tectonic_region_types:
                raise LogicTreeError(
                    branchset_node, self.filename,
                    "source models don't define sources of tectonic region "
                    "type '%s'" % f['applyToTectonicRegionType'])

        if (uncertainty_type.endswith('Absolute') and
                len(self.source_data) > 1):  # there is more than one source
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
            if self.source_id:
                srcids = [s for s in f['applyToSources'].split()
                          if s == self.source_id]
            else:
                srcids = f['applyToSources'].split()
            for source_id in srcids:
                branchIDs = {
                    brid for (brid, trt, fname, srcid) in self.source_data
                    if srcid == source_id}
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

    def validate_branchset(self, branchset_node, bsno, branchset):
        """
        See superclass' method for description and signature specification.

        Checks that the following conditions are met:

        * First branching level must contain exactly one branchset, which
          must be of type "sourceModel".
        * All other branchsets must not be of type "sourceModel"
          or "gmpeModel".
        """
        if bsno == 0:
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

    def collect_source_model_data(self, branch_id, fname):
        """
        Parse source model file and collect information about source ids,
        source types and tectonic region types available in it. That
        information is used then for :meth:`validate_filters` and
        :meth:`validate_uncertainty_value`.

        :param branch_id: source model logic tree branch ID
        :param fname: relative filename for the current source model portion
        :returns: the number of sources in the source model portion
        """
        with self._get_source_model(fname) as sm:
            src = self.source_id.split('!')[0].split('@')[0]
            trt_by_src = get_trt_by_src(sm, src)
        if self.basepath:
            path = sm.name[len(self.basepath) + 1:]
        else:
            path = sm.name
        for src_id, trt in trt_by_src.items():
            try:
                valid.source_id(src_id)
            except ValueError:
                raise InvalidFile(
                    '%s: contain invalid ID %s' % (sm.name, src_id))
            self.source_data.append((branch_id, trt, path, src_id))
            self.tectonic_region_types.add(trt)
        return len(trt_by_src)

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

    def to_node(self):
        """
        :returns: a logicTree Node convertible into NRML format
        """
        bsnodes = []
        for bset in self.branchsets:
            dic = dict(branchSetID='bs%02d' % bset.ordinal,
                       uncertaintyType=bset.uncertainty_type)
            brnodes = []
            for br in bset.branches:
                um = Node('uncertaintyModel', {}, br.value)
                uw = Node('uncertaintyWeight', {}, br.weight)
                brnode = Node('logicTreeBranch', {'branchID': br.branch_id},
                              nodes=[um, uw])
                brnodes.append(brnode)
            bsnodes.append(Node('logicTreeBranchSet', dic, nodes=brnodes))
        return Node('logicTree', {'logicTreeID': 'lt'}, nodes=bsnodes)

    def get_duplicated_sources(self):
        """
        :returns: {src_id: affected branches}
        """
        sd = group_array(self.source_data, 'source')
        u, c = numpy.unique(self.source_data['source'], return_counts=1)
        # AUS event based was hanging with a slower implementation
        return {src: sd[src]['branch'] for src in u[c > 1]}

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
        attrs['source_id'] = self.source_id
        attrs['branchID'] = self.branchID
        return numpy.array(tbl, branch_dt), attrs

    # SourceModelLogicTree
    def __fromh5__(self, array, attrs):
        # this is rather tricky; to understand it, run the test
        # SerializeSmltTestCase which has a logic tree with 3 branchsets
        # with the form b11[b21[b31, b32], b22[b31, b32]] and 1 x 2 x 2 rlzs
        vars(self).update(attrs)
        self.test_mode = False
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
            bset = BranchSet(utype, filters, ordinal)
            bset.id = bsid
            for no, row in enumerate(rows):
                try:
                    uvalue = ast.literal_eval(row['uvalue'])
                except (SyntaxError, ValueError):
                    uvalue = row['uvalue']  # not really deserializable :-(
                br = Branch(row['branch'], uvalue, float(row['weight']), bsid)
                self.branches[br.branch_id] = br
                self.shortener[br.branch_id] = keyno(
                    br.branch_id, ordinal, no, BASE183)
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
    # NB: for EUR, with 302_990_625 realizations, the usage of __slots__
    # saves little memory, from 95.3 GB down to 81.0 GB
    __slots__ = ['ordinal', 'sm_lt_path', 'gsim_rlz', 'weight']

    def __init__(self, ordinal, sm_lt_path, gsim_rlz, weight):
        self.ordinal = ordinal
        self.sm_lt_path = sm_lt_path
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


def _get_smr(source_id):
    # 'src1;0.0' => 0
    suffix = source_id.split(';')[1]
    smr = suffix.split('.')[0]
    return int(smr)


def _ddic(trtis, smrs, get_rlzs):
    # returns a double dictionary trt_smr -> gsim -> rlzs
    acc = AccumDict(accum=AccumDict(accum=[]))
    for smr in smrs:
        rlzs_sm = get_rlzs(smr)
        for trti in trtis:
            rbg = acc[smr + TWO24 * trti]
            for rlz in rlzs_sm:
                rbg[rlz.gsim_rlz.value[trti]].append(rlz.ordinal)
            acc[smr + TWO24 * trti] = {gsim: U32(rbg[gsim])
                                       for gsim in sorted(rbg)}
    return acc


class FullLogicTree(object):
    """
    The full logic tree as composition of

    :param source_model_lt: :class:`SourceModelLogicTree` object
    :param gsim_lt: :class:`GsimLogicTree` object
    """
    oversampling = 'tolerate'

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

    def __init__(self, source_model_lt, gsim_lt, oversampling='tolerate'):
        self.source_model_lt = source_model_lt
        self.gsim_lt = gsim_lt
        self.oversampling = oversampling
        self.init()  # set .sm_rlzs and .trts

    def __getstate__(self):
        # .sd will not be available in the workers
        return {'source_model_lt': self.source_model_lt,
                'gsim_lt': self.gsim_lt,
                'oversampling': self.oversampling}

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
        self.Re = len(self.sm_rlzs)
        assert self.Re <= TWO24, len(self.sm_rlzs)
        self.trti = {trt: i for i, trt in enumerate(self.gsim_lt.values)}
        self.trts = list(self.gsim_lt.values)
        R = self.get_num_paths()
        logging.info('Building {:_d} realizations'.format(R))
        self.weights = numpy.array(  # shape (R, 1) or (R, M+1)
            [rlz.weight for rlz in self.get_realizations()])
        return self

    def wget(self, weights, imt):
        """
        Dispatch to the underlying gsim_lt.wget except for sampling
        """
        if self.num_samples:
            return weights[:, -1]
        return self.gsim_lt.wget(weights, imt)

    def gfull(self, all_trt_smrs):
        """
        :returns: the total Gt = Σ_i G_i
        """
        Gt = 0
        for trt_smrs in all_trt_smrs:
            trt = self.trts[trt_smrs[0] // TWO24]
            Gt += len(self.gsim_lt.values[trt])
        return Gt

    def get_gids(self, all_trt_smrs):
        """
        :returns: list of of arrays of gids, one for each source group
        """
        gids = []
        g = 0
        for trt_smrs in all_trt_smrs:
            rbg = self.get_rlzs_by_gsim(trt_smrs)
            gids.append(numpy.arange(g, g + len(rbg)))
            g += len(rbg)
        return gids

    def get_trt_rlzs(self, all_trt_smrs):
        """
        :returns: a list with Gt arrays of dtype uint32
        """
        data = []
        for trt_smrs in all_trt_smrs:
            for rlzs in self.get_rlzs_by_gsim(trt_smrs).values():
                data.append(U32(rlzs) + TWO24 * (trt_smrs[0] // TWO24))
        return data

    def g_weights(self, all_trt_smrs):
        """
        :returns: an array of weights of shape (Gt, 1) or (Gt, M+1)
        """
        data = []
        for trt_smrs in all_trt_smrs:
            for rlzs in self.get_rlzs_by_gsim(trt_smrs).values():
                data.append(self.weights[rlzs].sum(axis=0))
        return numpy.array(data)

    def trt_by(self, trt_smr):
        """
        :returns: the TRT associated to trt_smr
        """
        if len(self.trts) == 1:
            return self.trts[0]
        return self.trts[trt_smr // TWO24]

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

    @cached_property
    def sd(self):
        return group_array(self.source_model_lt.source_data, 'source')

    def get_trt_smrs(self, src_id=None):
        """
        :returns: a tuple of indices trt_smr for the given source
        """
        try:
            sd = self.source_model_lt.source_data
        except AttributeError:  # fake logic tree
            return 0,
        if src_id is None:
            return tuple(trti * TWO24 + sm_rlz.ordinal
                         for sm_rlz in self.sm_rlzs
                         for trti in self.trti)
        sd = self.sd[src_id]
        trt = sd['trt'][0]  # all same trt
        trti = 0 if trt == '*' else self.trti[trt]
        brids = set(sd['branch'])
        return tuple(trti * TWO24 + sm_rlz.ordinal
                     for sm_rlz in self.sm_rlzs
                     if set(sm_rlz.lt_path) & brids)

    # NB: called by the source_reader with smr and by
    # .reduce_groups with source_id
    def set_trt_smr(self, srcs, source_id=None, smr=None):
        """
        :param srcs: source objects
        :param source_id: base source ID
        :param srm: source model realization index
        :returns: list of sources with the same base source ID
        """
        if not self.trti:  # empty gsim_lt
            return srcs
        sd = self.sd
        out = []
        for src in srcs:
            srcid = valid.corename(src)
            if source_id and srcid != source_id:
                continue  # filter
            if self.trti == {'*': 0}:  # passed gsim=XXX in the job.ini
                trti = 0
            else:
                trti = self.trti[src.tectonic_region_type]
            if smr is None and ';' in src.source_id:
                # assume <base_id>;<smr>
                smr = _get_smr(src.source_id)
            if smr is None:  # called by .reduce_groups
                srcid = srcid.split('@')[0]
                try:
                    # check if ambiguous source ID
                    srcid, fname = srcid.rsplit('!')
                except ValueError:
                    # non-ambiguous source ID
                    fname = ''
                    ok = slice(None)
                else:
                    ok = [fname in string for string in sd[srcid]['fname']]
                brids = set(sd[srcid]['branch'][ok])
                tup = tuple(trti * TWO24 + sm_rlz.ordinal
                            for sm_rlz in self.sm_rlzs
                            if set(sm_rlz.lt_path) & brids)
            else:
                tup = trti * TWO24 + smr
            # print('Setting %s on %s' % (tup, src))
            src.trt_smr = tup  # realizations impacted by the source
            out.append(src)
        return out

    def reduce_groups(self, src_groups):
        """
        Filter the sources and set the tuple .trt_smr
        """
        groups = []
        source_id = self.source_model_lt.source_id
        for sg in src_groups:
            ok = self.set_trt_smr(sg, source_id)
            if ok:
                grp = copy.copy(sg)
                grp.sources = ok
                groups.append(grp)
        return groups

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
        if hasattr(self, '_rlzs'):
            return self._rlzs

        num_samples = self.source_model_lt.num_samples
        if num_samples:  # sampling
            rlzs = numpy.empty(num_samples, object)
            sm_rlzs = []
            for sm_rlz in self.sm_rlzs:
                sm_rlzs.extend([sm_rlz] * sm_rlz.samples)
            gsim_rlzs = self.gsim_lt.sample(
                num_samples, self.seed + 1, self.sampling_method)
            for i, gsim_rlz in enumerate(gsim_rlzs):
                rlzs[i] = LtRealization(i, sm_rlzs[i].lt_path, gsim_rlz,
                                        sm_rlzs[i].weight * gsim_rlz.weight)
            if self.sampling_method.startswith('early_'):
                for rlz in rlzs:
                    rlz.weight[:] = 1. / num_samples
        else:  # full enumeration
            gsim_rlzs = list(self.gsim_lt)
            ws = numpy.array([gsim_rlz.weight for gsim_rlz in gsim_rlzs])
            rlzs = numpy.empty(len(ws) * len(self.sm_rlzs), object)
            i = 0
            for sm_rlz in self.sm_rlzs:
                smpath = sm_rlz.lt_path
                for gsim_rlz, weight in zip(gsim_rlzs, sm_rlz.weight * ws):
                    rlzs[i] = LtRealization(i, smpath, gsim_rlz, weight)
                    i += 1
        # rescale the weights if not one, see case_52
        tot_weight = sum(rlz.weight for rlz in rlzs)[-1]
        if tot_weight != 1.:
            for rlz in rlzs:
                rlz.weight = rlz.weight / tot_weight
        self._rlzs = rlzs
        return self._rlzs

    def _rlzs_by_gsim(self, trt_smr):
        # return dictionary gsim->rlzs
        return self.get_rlzs_by_gsim_dic()[trt_smr]

    def get_rlzs_by_gsim_dic(self):
        """
        :returns: a dictionary trt_smr -> gsim -> rlz ordinals
        """
        if hasattr(self, '_rlzs_by'):
            return self._rlzs_by
        rlzs = self.get_realizations()
        trtis = range(len(self.gsim_lt.values))
        smrs = numpy.array([sm.ordinal for sm in self.sm_rlzs])
        if self.source_model_lt.filename == '_fake.xml':  # scenario
            smr_by_ltp = {'~'.join(sm_rlz.lt_path): i
                          for i, sm_rlz in enumerate(self.sm_rlzs)}
            smidx = numpy.zeros(self.get_num_paths(), int)
            for rlz in rlzs:
                smidx[rlz.ordinal] = smr_by_ltp['~'.join(rlz.sm_lt_path)]
            self._rlzs_by = _ddic(trtis, smrs,
                                  lambda smr: rlzs[smidx == smr])
        else:  # classical and event based
            start = 0
            slices = []
            for sm in self.sm_rlzs:
                slices.append(slice(start, start + sm.samples))
                start += sm.samples
            self._rlzs_by = _ddic(trtis, smrs, lambda smr: rlzs[slices[smr]])
        return self._rlzs_by

    def get_rlzs_by_gsim(self, trt_smr):
        """
        :param trt_smr: index or array of indices
        :returns: a dictionary gsim -> array of rlz indices
        """
        if isinstance(trt_smr, (numpy.ndarray, list, tuple)):  # classical
            dic = AccumDict(accum=[])
            for t in trt_smr:
                for gsim, rlzs in self._rlzs_by_gsim(t).items():
                    dic[gsim].append(rlzs)
            return {k: numpy.concatenate(ls, dtype=U32)
                    for k, ls in dic.items()}
        # event based
        return self._rlzs_by_gsim(trt_smr)

    # FullLogicTree
    def __toh5__(self):
        sm_data = []
        for sm in self.sm_rlzs:
            sm_data.append((str(sm.value), sm.weight,
                            '~'.join(sm.lt_path), sm.samples))
        return (dict(
            source_model_lt=self.source_model_lt,
            gsim_lt=self.gsim_lt,
            source_data=self.source_model_lt.source_data,
            sm_data=numpy.array(sm_data, source_model_dt)),
                dict(seed=self.seed, num_samples=self.num_samples,
                     trts=hdf5.array_of_vstr(self.gsim_lt.values),
                     oversampling=self.oversampling))

    # FullLogicTree
    def __fromh5__(self, dic, attrs):
        # TODO: this is called more times than needed, maybe we should cache it
        sm_data = dic['sm_data']
        sd = dic.pop('source_data', numpy.zeros(0))  # empty for engine <= 3.16
        vars(self).update(attrs)
        self.source_model_lt = dic['source_model_lt']
        self.source_model_lt.source_data = sd[:]
        self.gsim_lt = dic['gsim_lt']
        self.sm_rlzs = []
        for sm_id, rec in enumerate(sm_data):
            path = tuple(str(decode(rec['path'])).split('~'))
            sm = Realization(
                rec['name'], rec['weight'], sm_id, path, rec['samples'])
            self.sm_rlzs.append(sm)

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
            path = '%s~%s' % (shorten(r.sm_lt_path, sh1, 'smlt'),
                              shorten(r.gsim_rlz.lt_path, sh2, 'gslt'))
            tups.append((r.ordinal, path, r.weight[-1]))
        return numpy.array(tups, rlz_dt)

    def __repr__(self):
        info_by_model = {}
        for sm in self.sm_rlzs:
            info_by_model[sm.lt_path] = (
                '~'.join(map(decode, sm.lt_path)), decode(sm.value), sm.weight)
        summary = ['%s, %s, weight=%s' % ibm for ibm in info_by_model.values()]
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
        bset = BranchSet('gmpeModel', dict(applyToTectonicRegionType=trt))
        bset.branches = [Branch(bt.id, bt.gsim, bt.weight['weight'], bsid)
                         for bt in btuples]  # branch ID fixed later
        bsets.append(bset)
        bsno += 1
    clt = CompositeLogicTree(source_model_lt.branchsets + bsets)
    return clt
