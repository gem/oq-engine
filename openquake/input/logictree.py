# -*- coding: utf-8 -*-

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""Logic tree parser, verifier and processor."""

import os
import sys
import re
from decimal import Decimal

from lxml import etree


class LogicTreeError(Exception):
    def __init__(self, filename, basepath, msg):
        super(LogicTreeError, self).__init__(msg)
        self.filename = filename
        self.basepath = basepath

    def get_filepath(self):
        return os.path.join(self.basepath, self.filename)

    def __str__(self):
        return 'file %r: %s' % (self.get_filepath(), self.message)


class ParsingError(LogicTreeError):
    pass


class ValidationError(LogicTreeError):
    def __init__(self, node, *args, **kwargs):
        super(ValidationError, self).__init__(*args, **kwargs)
        self.lineno = node.sourceline

    def __str__(self):
        return 'file %r line %r: %s' % (self.get_filepath(), self.lineno,
                                        self.message)


class Branch(object):
    def __init__(self, branch_id, weight, value):
        self.branch_id = branch_id
        self.weight = weight
        self.value = value
        self.child_branchset = None


class BranchSet(object):
    def __init__(self, branches, uncertainty_type, filters):
        self.branches = branches
        self.uncertainty_type = uncertainty_type
        self.filters = filters


class LogicTree(object):
    SCHEMA_PATH = os.path.join(os.path.dirname(__file__),
                               '..', 'nrml', 'schema', 'nrml.xsd')
    NRML = 'http://openquake.org/xmlns/nrml/0.2'

    SOURCE_TYPES = ('pointSource', 'areaSource', 'complexFault', 'simpleFault')

    FILTERS = ('applyToTectonicRegionType',
               'applyToSources',
               'applyToSourceType')

    _xmlschema = None

    @classmethod
    def get_xmlschema(cls):
        if not cls._xmlschema:
            cls._xmlschema = etree.XMLSchema(file=cls.SCHEMA_PATH)
        return cls._xmlschema

    def __init__(self, basepath, sourcemodel_logictree, gmpe_logictree):
        self.basepath = basepath
        parser = etree.XMLParser(schema=self.get_xmlschema())
        sm_filestream = self._open_file(sourcemodel_logictree)
        try:
            tree = etree.parse(sm_filestream, parser=parser)
        except etree.XMLSyntaxError as exc:
            raise ParsingError(sourcemodel_logictree, self.basepath, str(exc))
        self.branches = {}
        self.open_ends = set()
        self.source_ids = set()
        self.source_types = set()
        self.tectonic_region_types = set()
        [sm_tree] = tree.getroot()
        self.parse_sourcemodel_tree(sm_tree, sourcemodel_logictree)

    def _open_file(self, filename):
        try:
            return open(os.path.join(self.basepath, filename))
        except IOError as exc:
            raise ParsingError(filename, self.basepath, str(exc))

    def parse_sourcemodel_tree(self, tree, filename):
        branchinglevels = iter(tree)
        first_branchinglevel = list(next(branchinglevels))
        if len(first_branchinglevel) > 1:
            raise ValidationError(
                first_branchinglevel[1], filename, self.basepath,
                'there must be only one branch set on first branching level'
            )
        [root_branchset] = first_branchinglevel
        self.root = self.parse_branchset(root_branchset, filename)
        if self.root.uncertainty_type != 'sourceModel':
            raise ValidationError(
                root_branchset, filename, self.basepath,
                'first branchset must define an uncertainty ' \
                'of type "sourceModel"'
            )
        self.open_ends.update(branch for branch in self.root.branches)
        for source_model_branch in self.root.branches:
            self.collect_source_model_data(source_model_branch.value)
        for branchinglevel in branchinglevels:
            new_open_ends = set()
            for branchset_node in branchinglevel:
                branchset = self.parse_branchset(branchset_node, filename)
                if branchset.uncertainty_type == 'sourceModel':
                    raise ValidationError(
                        branchset_node, filename, self.basepath,
                        'uncertainty of type "sourceModel" can be defined ' \
                        'on first branchset only'
                    )
                if branchset.uncertainty_type == 'gmpeModel':
                    raise ValidationError(
                        branchset_node, filename, self.basepath,
                        'uncertainty of type "gmpeModel" is not allowed ' \
                        'in source model logic tree'
                    )
                for branch in branchset.branches:
                    new_open_ends.add(branch)
            self.open_ends.clear()
            self.open_ends.update(new_open_ends)

    def parse_branchset(self, branchset_node, filename):
        branches = []
        weight_sum = 0
        uncertainty_type = branchset_node.get('uncertaintyType')
        for branchnode in branchset_node:
            weight = branchnode.find('{%s}uncertaintyWeight' % self.NRML).text
            weight = Decimal(weight)
            weight_sum += weight
            value_node = branchnode.find('{%s}uncertaintyModel' % self.NRML)
            value = self.validate_uncertainty_value(
                filename, value_node, uncertainty_type, value_node.text
            )
            branch_id = branchnode.get('branchID')
            branch = Branch(branch_id, weight, value)
            if branch_id in self.branches:
                raise ValidationError(
                    branchnode, filename, self.basepath,
                    "branchID %r is not unique" % branch_id
                )
            self.branches[branch_id] = branch
            branches.append(branch)
        if weight_sum != 1.0:
            raise ValidationError(
                branchset_node, filename, self.basepath,
                "branchset weights don't sum up to 1.0"
            )
        filters = self.validate_branchset_filters(filename, branchset_node,
                                                  uncertainty_type)
        branchset = BranchSet(branches, uncertainty_type, filters)
        apply_to_branches = branchset_node.get('applyToBranches')
        if apply_to_branches:
            apply_to_branches = apply_to_branches.split()
            for branch_id in apply_to_branches:
                if not branch_id in self.branches:
                    raise ValidationError(
                        branchset_node, filename, self.basepath,
                        'branch %r is not yet defined' % branch_id
                    )
                branch = self.branches[branch_id]
                if branch.child_branchset is not None:
                    raise ValidationError(
                        branchset_node, filename, self.basepath,
                        'branch %r already has child branchset' % branch_id
                    )
                if not branch in self.open_ends:
                    raise ValidationError(
                        branchset_node, filename, self.basepath,
                        'applyToBranches must reference only branches ' \
                        'from previous branching level'
                    )
                branch.child_branchset = branchset
        else:
            for branch in self.open_ends:
                branch.child_branchset = branchset
        return branchset

    def validate_uncertainty_value(self, filename, node,
                                   uncertainty_type, value):
        _float_re = r'(\+|\-)?(\d+|\d*\.\d+)'
        if uncertainty_type == 'sourceModel' or uncertainty_type == 'gmpeModel':
            # file should exist and be readable
            self._open_file(value).close()
            return value
        elif uncertainty_type == 'abGRAbsolute':
            if not re.match('^%s\s+%s$' % (_float_re, _float_re), value):
                raise ValidationError(
                    node, filename, self.basepath,
                    'expected two float values separated by space'
                )
            return tuple(float(val) for val in value.split())
        else:
            if not re.match('^%s$' % _float_re, value):
                raise ValidationError(
                    node, filename, self.basepath,
                    'expected single float value'
                )
            return float(value)

    def validate_branchset_filters(self, filename, branchset_node,
                                   uncertainty_type):
        filters = dict((filtername, branchset_node.get(filtername))
                       for filtername in self.FILTERS
                       if filtername in branchset_node.attrib)
        if uncertainty_type == 'sourceModel' and filters:
            raise ValidationError(
                branchset_node, filename, self.basepath,
                'filters are not allowed on source model uncertainty'
            )
        if 'applyToSources' in filters:
            source_ids = filters['applyToSources'].split()
            nonexistent_source_ids = set(source_ids) - self.source_ids
            if nonexistent_source_ids:
                raise ValidationError(
                    branchset_node, filename, self.basepath,
                    'source ids %s are not defined in source models' % \
                    list(nonexistent_source_ids)
                )
            filters['applyToSources'] = source_ids
        if 'applyToTectonicRegionType' in filters:
            if not filters['applyToTectonicRegionType'] \
                    in self.tectonic_region_types:
                raise ValidationError(
                    branchset_node, filename, self.basepath,
                    "source models don't define sources of tectonic region " \
                    "type %r" % filters['applyToTectonicRegionType']
                )
        if 'applyToSourceType' in filters:
            if not filters['applyToSourceType'] in self.source_types:
                raise ValidationError(
                    branchset_node, filename, self.basepath,
                    "source models don't define sources of type %r" % \
                    filters['applyToSourceType']
                )
        if len(filters) > 1:
            raise ValidationError(
                branchset_node, filename, self.basepath,
                "only one filter is allowed per branchset"
            )
        elif not filters:
            filter_ = filter_value = None
        else:
            [[filter_, filter_value]] = filters.items()
        if uncertainty_type in ('abGRAbsolute', 'maxMagGRAbsolute'):
            if not filter_ or not filter_ == 'applyToSources' \
                    or not len(filter_value) == 1:
                raise ValidationError(
                    branchset_node, filename, self.basepath,
                    "uncertainty of type %r must define 'applyToSources' " \
                    "with only one source id" % uncertainty_type
                )

        return filters

    def collect_source_model_data(self, filename):
        all_source_types = set('{%s}%sSource' % (self.NRML, tagname)
                               for tagname in self.SOURCE_TYPES)
        tectonic_region_type_tag = '{%s}tectonicRegion' % LogicTree.NRML
        sourcetype_slice = slice(len('{%s}' % self.NRML), - len('Source'))
        eventstream = etree.iterparse(self._open_file(filename),
                                      tag='{%s}*' % self.NRML,
                                      schema=self.get_xmlschema())
        while True:
            try:
                event, node = next(eventstream)
            except StopIteration:
                break
            except etree.XMLSyntaxError as exc:
                raise ParsingError(filename, self.basepath, str(exc))
            if not node.tag in all_source_types:
                if node.tag == tectonic_region_type_tag:
                    self.tectonic_region_types.add(node.text)
            else:
                self.source_ids.add(
                    node.attrib['{http://www.opengis.net/gml}id']
                )
                self.source_types.add(node.tag[sourcetype_slice])

                # saving memory by removing already processed nodes.
                # see http://lxml.de/parsing.html#modifying-the-tree
                node.clear()
                parent = node.getparent()
                prev = node.getprevious()
                while prev is not None:
                    parent.remove(prev)
                    prev = node.getprevious()
