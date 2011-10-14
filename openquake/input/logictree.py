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

"""
Logic tree parser, verifier and processor. See specs
at https://blueprints.launchpad.net/openquake/+spec/openquake-logic-tree-module
"""

import os
import sys
import re
import random
import itertools
from decimal import Decimal
try:
    import simplejson as json
except ImportError:
    import json

from lxml import etree

from openquake.nrml import nrml_schema_file
from openquake.java import jvm


class LogicTreeError(Exception):
    """
    Base class for errors of loading, parsing and validation of logic trees.

    :param filename:
        The name of the file which contains an error. Supposed
        to be relative to ``basepath``.
    :param basepath:
        Base path as given to :class:`LogicTree` constructor.
    """
    def __init__(self, filename, basepath, msg):
        super(LogicTreeError, self).__init__(msg)
        self.filename = filename
        self.basepath = basepath

    def get_filepath(self):
        """
        Reconstruct and return absolute path to affected file.
        """
        return os.path.join(self.basepath, self.filename)

    def __str__(self):
        return 'file %r: %s' % (self.get_filepath(), self.message)


class ParsingError(LogicTreeError):
    """
    XML file failed to load: it is not readable or contains invalid xml.
    """


class ValidationError(LogicTreeError):
    """
    Logic tree file contains a logic error.

    :param node:
        XML node object that causes fail. Used to determine
        the affected line number.

    All other constructor parameters are passed to :class:`superclass'
    <LogicTreeError>` constructor.
    """
    def __init__(self, node, *args, **kwargs):
        super(ValidationError, self).__init__(*args, **kwargs)
        self.lineno = node.sourceline

    def __str__(self):
        return 'file %r line %r: %s' % (self.get_filepath(), self.lineno,
                                        self.message)


class Branch(object):
    """
    Branch object, represents a ``<logicTreeBranch />`` element.

    :param branch_id:
        Value of ``@branchID`` attribute.
    :param weight:
        Decimal value of weight assigned to the branch. A text node contents
        of ``<uncertaintyWeight />`` child node.
    :param value:
        The actual uncertainty parameter value. A text node contents
        of ``<uncertaintyModel />`` child node. Type depends
        on the branchset's uncertainty type.
    """
    def __init__(self, branch_id, weight, value):
        self.branch_id = branch_id
        self.weight = weight
        self.value = value
        self.child_branchset = None


class BranchSet(object):
    """
    Branchset object, represents a ``<logicTreeBranchSet />`` element.

    :param uncertainty_type:
        String value. According to specs can be one of:

        gmpeModel
            Branches contain references to different GMPEs. Values are parsed
            as strings and are supposed to be one of supported GMPEs. See list
            at :class:`GMPELogicTree`.
        sourceModel
            Branches contain references to different PSHA source models. Values
            are treated as file names, relatively to base path.
        maxMagGRRelative
            Different values to add to Gutenberg-Richter ("GR") maximum
            magnitude. Value should be interpretable as float.
        bGRRelative
            Values to add to GR "b" value. Parsed as float.
        maxMagGRAbsolute
            Values to replace GR maximum magnitude. Values expected to be
            lists of floats separated by space, one float for each GR MFD
            in a target source in order of appearance.
        abGRAbsolute
            Values to replace "a" and "b" values of GR MFD. Lists of pairs
            of floats, one pair for one GR MFD in a target source.

    :param filters:
        Dictionary, a set of filters to specify which sources should
        the uncertainty be applied to. Represented as branchset element's
        attributes in xml:

        applyToSources
            The uncertainty should be applied only to specific sources.
            This filter is required for absolute uncertainties (also
            only one source can be used for those). Value should be the list
            of source ids. Can be used only in source model logic tree.
        applyToSourceType
            Can be used in the source model logic tree definition. Allows
            to specify to which source type (area, point, simple fault,
            complex fault) the uncertainty applies to.
        applyToTectonicRegionType
            Can be used in both the source model and GMPE logic trees. Allows
            to specify to which tectonic region type (Active Shallow Crust,
            Stable Shallow Crust, etc.) the uncertainty applies to. This
            filter is required for all branchsets in GMPE logic tree.
    """
    def __init__(self, uncertainty_type, filters):
        self.branches = []
        self.uncertainty_type = uncertainty_type
        self.filters = filters

    def sample(self, rnd=random):
        """
        Take a random branch (with respect to their weights) and return it.

        :param rnd:
            Random object. Should have method ``random()`` -- return uniformly
            distributed random float number >= 0 and < 1.
        :return:
            :class:`Branch` object, one of branches in the branchet's list.
        """
        # Take a random number once, then loop through branches,
        # accumulating their weights. When accumulated value exceeds
        # sampled random value, return that branch.
        diceroll = rnd.random()
        acc = 0
        for branch in self.branches:
            acc += branch.weight
            if acc >= diceroll:
                return branch
        raise AssertionError('do weights really sum up to 1.0?')

    @classmethod
    def _is_gr_mfd(cls, mfd):
        """
        Return ``True`` if ``mfd`` is opensha GR MFD object
        (and in particular not evenly discretized function).
        """
        if not hasattr(cls, '_GRMFD'):
            cls._GRMFD = jvm().JClass(
                'org.opensha.sha.magdist.GutenbergRichterMagFreqDist'
            )
        return isinstance(mfd, cls._GRMFD)

    @classmethod
    def _is_point(cls, source):
        """
        Return ``True`` if ``source`` is opensha source of point type.
        """
        if not hasattr(cls, '_PointSource'):
            cls._PointSource = jvm().JClass(
                'org.opensha.sha.earthquake.' \
                'rupForecastImpl.GEM1.SourceData.GEMPointSourceData'
            )
        return isinstance(source, cls._PointSource)

    @classmethod
    def _is_simplefault(cls, source):
        """
        Return ``True`` if ``source`` is opensha source of simple fault type.
        """
        if not hasattr(cls, '_SimpleFaultSource'):
            cls._SimpleFaultSource = jvm().JClass(
                'org.opensha.sha.earthquake.' \
                'rupForecastImpl.GEM1.SourceData.GEMFaultSourceData'
            )
        return isinstance(source, cls._SimpleFaultSource)

    @classmethod
    def _is_complexfault(cls, source):
        """
        Return ``True`` if ``source`` is opensha source of complex fault type.
        """
        if not hasattr(cls, '_ComplexFaultSource'):
            cls._ComplexFaultSource = jvm().JClass(
                'org.opensha.sha.earthquake.' \
                'rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData'
            )
        return isinstance(source, cls._ComplexFaultSource)

    @classmethod
    def _is_area(cls, source):
        """
        Return ``True`` if ``source`` is opensha source of area type.
        """
        if not hasattr(cls, '_AreaSource'):
            cls._AreaSource = jvm().JClass(
                'org.opensha.sha.earthquake.' \
                'rupForecastImpl.GEM1.SourceData.GEMAreaSourceData'
            )
        return isinstance(source, cls._AreaSource)

    def filter_source(self, source):
        """
        Apply filters to ``source`` and return ``True`` if uncertainty should
        be applied to it.
        """
        for key, value in self.filters.items():
            if key == 'applyToTectonicRegionType':
                if value != source.tectReg.name:
                    return False
            elif key == 'applyToSourceType':
                if value == 'area':
                    if not self._is_area(source):
                        return False
                elif value == 'point':
                    if not self._is_point(source):
                        return False
                elif value == 'simpleFault':
                    if not self._is_simplefault(source):
                        return False
                elif value == 'complexFault':
                    if not self._is_complexfault(source):
                        return False
                else:
                    raise AssertionError('unknown source type %r' % value)
            elif key == 'applyToSources':
                if source.id not in value:
                    return False
            else:
                raise AssertionError('unknown filter %r' % key)
        # All filters pass, return True.
        return True

    def apply_uncertainty(self, value, source):
        """
        Apply this branchset's uncertainty with value ``value`` to source
        ``source``, if it passes :meth:`filters <filter_source>`.

        This method is not called for uncertainties of types "gmpeModel"
        and "sourceModel".

        :param value:
            The actual uncertainty value of :meth:`sampled <sample>` branch.
            Type depends on uncertainty type.
        :param source:
            The opensha source data object.
        :return:
            ``None``, all changes are applied to MFD in place. Therefore
            all sources have to be reinstantiated after processing is done
            in order to sample the tree once again.
        """
        if not self.filter_source(source):
            return

        # TODO: handle exceptions in java methods and rethrow LogicTreeError
        if self._is_complexfault(source) or self._is_simplefault(source):
            # simple fault or complex fault - only one mfd always
            mfdlist = [source.getMfd()]
        elif self._is_point(source):
            # point
            mfdlist = source.getHypoMagFreqDistAtLoc().getMagFreqDistList()
        elif self._is_area(source):
            # area
            mfdlist = source.getMagfreqDistFocMech().getMagFreqDistList()
        else:
            raise AssertionError('type of source %r is unknown' % source)

        if self.uncertainty_type in ('abGRAbsolute', 'maxMagGRAbsolute'):
            # Absolute uncertainties have lists of values -- one for each
            # GR MFD in order of appearance.
            valuelist = iter(value)
        else:
            # All other uncertainties always have one value which applies
            # to all mfds, no matter how many are there.
            valuelist = itertools.repeat(value)

        for mfd in mfdlist:
            # ignore all non-GR mfds
            if self._is_gr_mfd(mfd):
                mfd_value = next(valuelist)
                self._apply_uncertainty_to_mfd(mfd, mfd_value)

    def _apply_uncertainty_to_mfd(self, mfd, value):
        """
        Modify ``mfd`` object with uncertainty value ``value``.
        """
        # Need to cast to floats explicitly to make calls match java
        # methods signatures in case when value is an integer.
        if self.uncertainty_type == 'abGRAbsolute':
            a, b = value
            mfd.setAB(float(a), float(b))
        elif self.uncertainty_type == 'bGRRelative':
            mfd.incrementB(float(value))
        elif self.uncertainty_type == 'maxMagGRRelative':
            mfd.incrementMagUpper(float(value))
        elif self.uncertainty_type == 'maxMagGRAbsolute':
            mfd.setMagUpper(float(value))
        else:
            raise AssertionError('what is %s btw?' % self.uncertainty_type)


class BaseLogicTree(object):
    """
    Common code for logic tree readers, parsers and verifiers --
    :class:`GMPELogicTree` and :class:`SourceModelLogicTree`.

    :param basepath:
        Base path for logic tree itself and all files that it references.
    :param filename:
        Name of logic tree file, supposed to be relative to ``basepath``.
    :raises ParsingError:
        If logic tree file or any of the referenced files is unable to read
        or parse.
    :raises ValidationError:
        If logic tree file has a logic error, which can not be prevented
        by xml schema rules (like referencing sources with missing id).
    """
    NRML = 'http://openquake.org/xmlns/nrml/0.2'
    FILTERS = ('applyToTectonicRegionType',
               'applyToSources',
               'applyToSourceType')

    _xmlschema = None

    @classmethod
    def get_xmlschema(cls):
        """
        Create (if needed) and return ``etree.XMLSchema`` object
        for verifying nrml-files correctness.

        Once created schema object is cached in ``_xmlschema``
        class attribute.
        """
        if not cls._xmlschema:
            cls._xmlschema = etree.XMLSchema(file=nrml_schema_file())
        return cls._xmlschema

    def __init__(self, basepath, filename):
        self.basepath = basepath
        self.filename = filename
        parser = etree.XMLParser(schema=self.get_xmlschema())
        self.branches = {}
        self.open_ends = set()
        filestream = self._open_file(self.filename)
        try:
            tree = etree.parse(filestream, parser=parser)
        except etree.XMLSyntaxError as exc:
            # Wrap etree parsing exception to :exc:`ParsingError`.
            raise ParsingError(self.filename, self.basepath, str(exc))
        [tree] = tree.getroot()
        self.root_branchset = None
        self.parse_tree(tree)

    def parse_tree(self, tree_node):
        """
        Parse the whole tree and point ``root_branchset`` attribute
        to the tree's root. Calls :meth:`validate_tree` when done.
        """
        for depth, branchinglevel_node in enumerate(tree_node):
            self.parse_branchinglevel(branchinglevel_node, depth)
        self.root_branchset = self.validate_tree(tree_node,
                                                 self.root_branchset)

    def _open_file(self, filename):
        """
        Open file named ``filename`` and return the file object.

        :param fileame:
            String, should be relative to tree's base path.
        :raises ParsingError:
            If file can not be opened.
        """
        # This was extracted to method mainly to simplify unittesting.
        try:
            return open(os.path.join(self.basepath, filename))
        except IOError as exc:
            raise ParsingError(filename, self.basepath, str(exc))

    def parse_branchinglevel(self, branchinglevel_node, depth):
        """
        Parse one branching level.

        :param branchinglevel_node:
            ``etree.Element`` object with tag "logicTreeBranchingLevel".
        :param depth:
            The sequential number of this branching level, based on 0.

        Enumerates children branchsets and call :meth:`parse_branchset`,
        :meth:`validate_branchset`, :meth:`parse_branches` and finally
        :meth:`apply_branchset` for each.

        Keeps track of "open ends" -- the set of branches that don't have
        any child branchset on this step of execution. After processing
        of every branching level only those branches that are listed in it
        can have child branchsets (if there is one on the next level).
        """
        new_open_ends = set()
        for number, branchset_node in enumerate(branchinglevel_node):
            branchset = self.parse_branchset(branchset_node)
            branchset = self.validate_branchset(branchset_node, depth, number,
                                                branchset)
            self.parse_branches(branchset_node, branchset)
            if depth == 0 and number == 0:
                self.root_branchset = branchset
            else:
                self.apply_branchset(branchset_node, branchset)
            for branch in branchset.branches:
                new_open_ends.add(branch)
        self.open_ends.clear()
        self.open_ends.update(new_open_ends)

    def parse_branchset(self, branchset_node):
        """
        Create :class:`BranchSet` object using data in ``branchset_node``.

        :param branchset_node:
            ``etree.Element`` object with tag "logicTreeBranchSet".
        :returns:
            An instance of :class:`BranchSet` with filters applied but with
            no branches (they're attached in :meth:`parse_branches`).
        """
        uncertainty_type = branchset_node.get('uncertaintyType')
        filters = dict((filtername, branchset_node.get(filtername))
                       for filtername in self.FILTERS
                       if filtername in branchset_node.attrib)
        filters = self.validate_filters(branchset_node, uncertainty_type,
                                        filters)
        branchset = BranchSet(uncertainty_type, filters)
        return branchset

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
        weight_sum = 0
        for branchnode in branchset_node:
            weight = branchnode.find('{%s}uncertaintyWeight' % self.NRML).text
            weight = Decimal(weight.strip())
            weight_sum += weight
            value_node = branchnode.find('{%s}uncertaintyModel' % self.NRML)
            value = self.validate_uncertainty_value(
                value_node, branchset, value_node.text.strip()
            )
            branch_id = branchnode.get('branchID')
            branch = Branch(branch_id, weight, value)
            if branch_id in self.branches:
                raise ValidationError(
                    branchnode, self.filename, self.basepath,
                    "branchID %r is not unique" % branch_id
                )
            self.branches[branch_id] = branch
            branchset.branches.append(branch)
        if weight_sum != 1.0:
            raise ValidationError(
                branchset_node, self.filename, self.basepath,
                "branchset weights don't sum up to 1.0"
            )

    def apply_branchset(self, branchset_node, branchset):
        """
        Apply ``branchset`` to all "open end" branches.
        See :meth:`parse_branchinglevel`.

        :param branchset_node:
            Same as for :meth:`parse_branchset`.
        :param branchset:
            An instance of :class:`BranchSet` to make it child
            for "open-end" branches.

        Can be overridden by subclasses if they want to apply branchests
        to branches selectively.
        """
        for branch in self.open_ends:
            branch.child_branchset = branchset

    def validate_tree(self, tree_node, root_branchset):
        """
        Check the whole parsed tree for consistency and sanity.

        Abstract method, must be overriden by subclasses.

        :param tree_node:
            ``etree.Element`` object with tag "logicTree".
        :param root_branchset:
            An instance of :class:`BranchSet` which is about to become
            the root branchset for this tree.
        :return:
            An object to make it root branchset.
        """
        raise NotImplementedError()

    def validate_uncertainty_value(self, node, branchset, value):
        """
        Check the value ``value`` for correctness to be set for one
        of branchet's branches.

        Abstract method, must be overriden by subclasses.

        :param node:
            ``etree.Element`` object with tag "uncertaintyModel" (the one
            that contains the subject value).
        :param branchset:
            An instance of :class:`BranchSet` which will have the branch
            with provided value attached once it's validated.
        :param value:
            The actual value to be checked. Type depends on branchset's
            uncertainty type.
        :return:
            The value to replace an original (for example, with type casted).
        """
        raise NotImplementedError()

    def validate_filters(self, node, uncertainty_type, filters):
        """
        Check that filters ``filters`` are valid for given uncertainty type.

        Abstract method, must be overriden by subclasses.

        :param node:
            ``etree.Element`` object with tag "logicTreeBranchSet".
        :param uncertainty_type:
            String specifying the uncertainty type.
            See the list in :class:`BranchSet`.
        :param filters:
            Filters dictionary.
        :return:
            The filters dictionary to replace an original.
        """
        raise NotImplementedError()

    def validate_branchset(self, branchset_node, depth, number, branchset):
        """
        Check that branchset is valid.

        Abstract method, must be overriden by subclasses.

        :param branchset_node:
            ``etree.Element`` object with tag "logicTreeBranchSet".
        :param depth:
            The number of branching level that contains the branchset,
            based on 0.
        :param number:
            The number of branchset inside the branching level,
            based on 0.
        :param branchset:
            An instance of :class:`BranchSet`.
        """
        raise NotImplementedError()


class SourceModelLogicTree(BaseLogicTree):
    """
    Source model logic tree parser.
    """
    SOURCE_TYPES = ('point', 'area', 'complexFault', 'simpleFault')

    def __init__(self, *args, **kwargs):
        self.source_ids_to_num_gr_mfds = {}
        self.tectonic_region_types = set()
        self.source_types = set()
        super(SourceModelLogicTree, self).__init__(*args, **kwargs)

    def validate_tree(self, tree_node, root_branchset):
        """
        See superclass' method for description and signature specification.

        Does not check anything, returns ``root_branchset`` intact.
        """
        return root_branchset

    def validate_uncertainty_value(self, node, branchset, value):
        """
        See superclass' method for description and signature specification.

        Checks that the following conditions are met:

        * For uncertainty of type "sourceModel": referenced file must exist
          and be readable. This is checked in :meth:`collect_source_model_data`
          along with saving the source model information.
        * For absolute uncertainties: the number of values must match
          the number of GR MFDs in source. The source (only one) itself
          must be referenced in branchset's filter "applyToSources".
        * For all other cases: value should be a single float value.
        """
        _float_re = re.compile(r'^(\+|\-)?(\d+|\d*\.\d+)$')
        if branchset.uncertainty_type == 'sourceModel':
            self.collect_source_model_data(value)
            return os.path.join(self.basepath, value)
        elif branchset.uncertainty_type == 'abGRAbsolute' \
                or branchset.uncertainty_type == 'maxMagGRAbsolute':
            [source_id] = branchset.filters['applyToSources']
            num_numbers_expected = self.source_ids_to_num_gr_mfds[source_id]
            assert num_numbers_expected != 0
            if branchset.uncertainty_type == 'abGRAbsolute':
                num_numbers_expected *= 2
            values = []
            for single_number in value.split():
                if not _float_re.match(single_number):
                    break
                values.append(float(single_number))
                if len(values) > num_numbers_expected:
                    break
            else:
                if len(values) == num_numbers_expected:
                    if branchset.uncertainty_type == 'abGRAbsolute':
                        return zip(*((iter(values), ) * 2))
                    else:
                        return values
            raise ValidationError(
                node, self.filename, self.basepath,
                'expected list of %d float(s) separated by space, ' \
                'as source %r has %d GR MFD(s)' % (num_numbers_expected,
                source_id, self.source_ids_to_num_gr_mfds[source_id])
            )
        else:
            if not _float_re.match(value):
                raise ValidationError(
                    node, self.filename, self.basepath,
                    'expected single float value'
                )
            return float(value)

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
            raise ValidationError(
                branchset_node, self.filename, self.basepath,
                'filters are not allowed on source model uncertainty'
            )
        if len(filters) > 1:
            raise ValidationError(
                branchset_node, self.filename, self.basepath,
                "only one filter is allowed per branchset"
            )
        if 'applyToSources' in filters:
            source_ids = filters['applyToSources'].split()
            nonexistent_source_ids = set(source_ids)
            nonexistent_source_ids.difference_update(
                self.source_ids_to_num_gr_mfds
            )
            if nonexistent_source_ids:
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    'source ids %s are not defined in source models' % \
                    list(nonexistent_source_ids)
                )
            filters['applyToSources'] = source_ids
        if 'applyToTectonicRegionType' in filters:
            if not filters['applyToTectonicRegionType'] \
                    in self.tectonic_region_types:
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    "source models don't define sources of tectonic region " \
                    "type %r" % filters['applyToTectonicRegionType']
                )
        if 'applyToSourceType' in filters:
            if not filters['applyToSourceType'] in self.source_types:
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    "source models don't define sources of type %r" % \
                    filters['applyToSourceType']
                )

        if not filters:
            filter_ = filter_value = None
        else:
            [[filter_, filter_value]] = filters.items()
        if uncertainty_type in ('abGRAbsolute', 'maxMagGRAbsolute'):
            if not filter_ or not filter_ == 'applyToSources' \
                    or not len(filter_value) == 1:
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    "uncertainty of type %r must define 'applyToSources' " \
                    "with only one source id" % uncertainty_type
                )
        return filters

    def validate_branchset(self, branchset_node, depth, number, branchset):
        """
        See superclass' method for description and signature specification.

        Checks that the following conditions are met:

        * First branching level must contain exactly one branchset, which
          must be of type "sourceModel".
        * All other branchsets must not be of type "sourceModel" or "gmpeModel".
        """
        if depth == 0:
            if number > 0:
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    'there must be only one branch set ' \
                    'on first branching level'
                )
            elif branchset.uncertainty_type != 'sourceModel':
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    'first branchset must define an uncertainty ' \
                    'of type "sourceModel"'
                )
        else:
            if branchset.uncertainty_type == 'sourceModel':
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    'uncertainty of type "sourceModel" can be defined ' \
                    'on first branchset only'
                )
            elif branchset.uncertainty_type == 'gmpeModel':
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    'uncertainty of type "gmpeModel" is not allowed ' \
                    'in source model logic tree'
                )
        return branchset

    def apply_branchset(self, branchset_node, branchset):
        """
        See superclass' method for description and signature specification.

        Parses branchset node's attribute ``@applyToBranches`` to apply
        following branchests to preceding branches selectively. Branching
        level can have more than one branchset exactly for this: different
        branchsets can apply to different open ends.

        Checks that branchset tries to be applied only to branches on previous
        branching level which do not have a child branchset yet.
        """
        apply_to_branches = branchset_node.get('applyToBranches')
        if apply_to_branches:
            apply_to_branches = apply_to_branches.split()
            for branch_id in apply_to_branches:
                if not branch_id in self.branches:
                    raise ValidationError(
                        branchset_node, self.filename, self.basepath,
                        'branch %r is not yet defined' % branch_id
                    )
                branch = self.branches[branch_id]
                if branch.child_branchset is not None:
                    raise ValidationError(
                        branchset_node, self.filename, self.basepath,
                        'branch %r already has child branchset' % branch_id
                    )
                if not branch in self.open_ends:
                    raise ValidationError(
                        branchset_node, self.filename, self.basepath,
                        'applyToBranches must reference only branches ' \
                        'from previous branching level'
                    )
                branch.child_branchset = branchset
        else:
            super(SourceModelLogicTree, self).apply_branchset(branchset_node,
                                                              branchset)

    def collect_source_model_data(self, filename):
        """
        Parse source model file and collect information about source ids,
        source types and tectonic region types available in it and also
        the number of GR MFDs for each source. That information is used then
        for :meth:`validate_filters` and :meth:`validate_uncertainty_value`.
        """
        all_source_types = set('{%s}%sSource' % (self.NRML, tagname)
                               for tagname in self.SOURCE_TYPES)
        tectonic_region_type_tag = '{%s}tectonicRegion' % self.NRML
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
                source_id = node.attrib['{http://www.opengis.net/gml}id']
                source_type = node.tag[sourcetype_slice]
                if source_type == 'point' or source_type == 'area':
                    mfds = len(node.findall(
                        '{%s}ruptureRateModel/{%s}truncatedGutenbergRichter' %
                        (self.NRML, self.NRML)
                    ))
                else:
                    mfds = 1
                self.source_ids_to_num_gr_mfds[source_id] = mfds

                self.source_types.add(source_type)

                # saving memory by removing already processed nodes.
                # see http://lxml.de/parsing.html#modifying-the-tree
                node.clear()
                parent = node.getparent()
                prev = node.getprevious()
                while prev is not None:
                    parent.remove(prev)
                    prev = node.getprevious()


class GMPELogicTree(BaseLogicTree):
    # TODO: document
    GMPEs = frozenset("""\
        Abrahamson_2000_AttenRel
        AS_1997_AttenRel
        AS_2008_AttenRel
        AW_2010_AttenRel
        BA_2008_AttenRel
        BC_2004_AttenRel
        BJF_1997_AttenRel
        BS_2003_AttenRel
        BW_1997_AttenRel
        Campbell_1997_AttenRel
        CB_2003_AttenRel
        CB_2008_AttenRel
        CL_2002_AttenRel
        CS_2005_AttenRel
        CY_2008_AttenRel
        DahleEtAl_1995_AttenRel
        Field_2000_AttenRel
        GouletEtAl_2006_AttenRel
        McVerryetal_2000_AttenRel
        SadighEtAl_1997_AttenRel
        SEA_1999_AttenRel
        WC94_DisplMagRel""".split()
    )

    def __init__(self, tectonic_region_types, *args, **kwargs):
        self.tectonic_region_types = frozenset(tectonic_region_types)
        self.defined_tectonic_region_types = set()
        super(GMPELogicTree, self).__init__(*args, **kwargs)

    def validate_uncertainty_value(self, node, branchset, value):
        if not value in self.GMPEs:
            raise ValidationError(
                node, self.filename, self.basepath,
                'gmpe %r is not available' % value
            )
        return value

    def validate_filters(self, node, uncertainty_type, filters):
        if not filters \
                or len(filters) > 1 \
                or filters.keys() != ['applyToTectonicRegionType']:
            raise ValidationError(
                node, self.filename, self.basepath,
                'branch sets in gmpe logic tree must define only ' \
                '"applyToTectonicRegionType" filter'
            )
        trt = filters['applyToTectonicRegionType']
        if not trt in self.tectonic_region_types:
            raise ValidationError(
                node, self.filename, self.basepath,
                "source models don't define sources of tectonic region " \
                "type %r" % trt
            )
        if trt in self.defined_tectonic_region_types:
            raise ValidationError(
                node, self.filename, self.basepath,
                'gmpe uncertainty for tectonic region type %r has already ' \
                'been defined' % trt
            )
        self.defined_tectonic_region_types.add(trt)
        return filters

    def validate_tree(self, tree_node, root_branchset):
        missing_trts = self.tectonic_region_types \
                       - self.defined_tectonic_region_types
        if missing_trts:
            raise ValidationError(
                tree_node, self.filename, self.basepath,
                'the following tectonic region types are defined ' \
                'in source model logic tree but not in gmpe logic tree: %s' % \
                list(sorted(missing_trts))
            )
        return root_branchset

    def validate_branchset(self, branchset_node, depth, number, branchset):
        if not branchset.uncertainty_type == 'gmpeModel':
            raise ValidationError(
                branchset_node, self.filename, self.basepath,
                'only uncertainties of type "gmpeModel" are allowed ' \
                'in gmpe logic tree'
            )
        if number != 0:
            raise ValidationError(
                branchset_node, self.filename, self.basepath,
                'only one branchset on each branching level is allowed ' \
                'in gmpe logic tree'
            )
        return branchset


class LogicTreeProcessor(object):
    # TODO: document
    def __init__(self, basepath, source_model_logictree_path,
                 gmpe_logictree_path):
        self.source_model_lt = SourceModelLogicTree(
            basepath, source_model_logictree_path
        )
        trts = self.source_model_lt.tectonic_region_types
        self.gmpe_lt = GMPELogicTree(trts, basepath, gmpe_logictree_path)

    def sample_and_save_source_model_logictree(self, cache, key, random_seed,
                                               mfd_bin_width):
        json_result = self.sample_source_model_logictree(random_seed,
                                                         mfd_bin_width)
        cache.set(key, json_result)

    def sample_source_model_logictree(self, random_seed, mfd_bin_width):
        rnd = random.Random(random_seed)
        SourceModelReader = jvm().JClass('org.gem.engine.hazard.' \
                                         'parsers.SourceModelReader')
        branch = self.source_model_lt.root_branchset.sample(rnd)
        sources = SourceModelReader(branch.value, float(mfd_bin_width)).read()
        while True:
            branchset = branch.child_branchset
            if branchset is None:
                break
            branch = branchset.sample(rnd)
            for source in sources:
                branchset.apply_uncertainty(branch.value, source)

        serializer = jvm().JClass('org.gem.JsonSerializer')
        return serializer.getJsonSourceList(sources)

    def sample_and_save_gmpe_logictree(self, cache, key, random_seed):
        cache.set(key, self.sample_gmpe_logictree(random_seed))

    def sample_gmpe_logictree(self, random_seed):
        rnd = random.Random(random_seed)
        value_prefix = 'org.opensha.sha.imr.attenRelImpl.'
        result = {}
        branchset = self.gmpe_lt.root_branchset
        while branchset:
            branch = branchset.sample(rnd)
            trt = branchset.filters['applyToTectonicRegionType']
            assert trt not in result
            result[trt] = value_prefix + branch.value
            branchset = branch.child_branchset
        return json.dumps(result)
