# -*- coding: utf-8 -*-

# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Logic tree parser, verifier and processor. See specs
at https://blueprints.launchpad.net/openquake/+spec/openquake-logic-tree-module
"""

import abc
import os
import random
import re

from decimal import Decimal
from lxml import etree

import openquake.nrmllib
import openquake.hazardlib
from openquake.hazardlib.gsim.base import GroundShakingIntensityModel


GSIM = openquake.hazardlib.gsim.get_available_gsims()


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

    def __str__(self):
        return 'basepath %r, filename %r: %s' % (self.basepath, self.filename,
                                                 self.message)


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
        return 'basepath %r, filename %r, line %r: %s' % (
            self.basepath, self.filename, self.lineno, self.message)


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
        String value. According to the spec one of:

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
        # Draw a random number and iterate through the branches in the set
        # (adding up their weights) until the random value falls into
        # the interval occupied by a branch. Return the latter.
        diceroll = rnd.random()
        acc = 0
        for branch in self.branches:
            acc += branch.weight
            if acc >= diceroll:
                return branch
        raise AssertionError('do weights really sum up to 1.0?')

    def enumerate_paths(self):
        """
        Generate all possible paths starting from this branch set.

        :returns:
            Generator of two-item tuples. Each tuple contains weight
            of the path (calculated as a product of the weights of all path's
            branches) and list of path's :class:`Branch` objects. Total sum
            of all paths' weights is 1.0
        """
        for path in self._enumerate_paths([]):
            flat_path = []
            weight = Decimal('1.0')
            while path:
                path, branch = path
                weight *= branch.weight
                flat_path.append(branch)
            yield weight, flat_path[::-1]

    def _enumerate_paths(self, prefix_path):
        """
        Recursive (private) part of :func:`enumerate_paths`. Returns generator
        of recursive lists of two items, where second item is the branch object
        and first one is itself list of two items.
        """
        for branch in self.branches:
            path = [prefix_path, branch]
            if branch.child_branchset is not None:
                for subpath in branch.child_branchset._enumerate_paths(path):
                    yield subpath
            else:
                yield path

    def get_branch_by_id(self, branch_id):
        """
        Return :class:`Branch` object belonging to this branch set with id
        equal to ``branch_id``.
        """
        for branch in self.branches:
            if branch.branch_id == branch_id:
                return branch
        raise AssertionError("couldn't find branch %r" % branch_id)

    def filter_source(self, source):
        # pylint: disable=R0911,R0912
        """
        Apply filters to ``source`` and return ``True`` if uncertainty should
        be applied to it.
        """
        for key, value in self.filters.items():
            if key == 'applyToTectonicRegionType':
                if value != source.tectonic_region_type:
                    return False
            elif key == 'applyToSourceType':
                if value == 'area':
                    if not isinstance(source,
                                      openquake.hazardlib.source.AreaSource):
                        return False
                elif value == 'point':
                    # area source extends point source
                    if (not isinstance(
                            source, openquake.hazardlib.source.PointSource)
                        or isinstance(
                            source, openquake.hazardlib.source.AreaSource)):
                        return False
                elif value == 'simpleFault':
                    if not isinstance(
                        source, openquake.hazardlib.source.SimpleFaultSource):
                        return False
                elif value == 'complexFault':
                    if not isinstance(
                        source, openquake.hazardlib.source.ComplexFaultSource):
                        return False
                elif value == 'characteristicFault':
                    if not isinstance(
                        source,
                        openquake.hazardlib.source.CharacteristicFaultSource):
                        return False
                else:
                    raise AssertionError('unknown source type %r' % value)
            elif key == 'applyToSources':
                if source.source_id not in value:
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
            # source didn't pass the filter
            return

        if not isinstance(source.mfd, openquake.hazardlib.mfd.TruncatedGRMFD):
            # source's mfd is not gutenberg-richter
            return

        self._apply_uncertainty_to_mfd(source.mfd, value)

    def _apply_uncertainty_to_mfd(self, mfd, value):
        """
        Modify ``mfd`` object with uncertainty value ``value``.
        """
        if self.uncertainty_type == 'abGRAbsolute':
            a, b = value
            mfd.modify('set_ab', dict(a_val=a, b_val=b))

        elif self.uncertainty_type == 'bGRRelative':
            mfd.modify('increment_b', dict(value=value))

        elif self.uncertainty_type == 'maxMagGRRelative':
            mfd.modify('increment_max_mag', dict(value=value))

        elif self.uncertainty_type == 'maxMagGRAbsolute':
            mfd.modify('set_max_mag', dict(value=value))

        else:
            raise AssertionError('unknown uncertainty type %r'
                                 % self.uncertainty_type)


class BaseLogicTree(object):
    """
    Common code for logic tree readers, parsers and verifiers --
    :class:`GMPELogicTree` and :class:`SourceModelLogicTree`.

    :param content:
        Raw string containing the logic tree xml content.
    :param basepath:
        Base path for logic tree itself and all files that it references.
    :param filename:
        Name of logic tree file, supposed to be relative to ``basepath``.
        That filename together with ``basepath`` are only used for reporting
        errors, the actual data is read from ``content``.
    :param hc:
        a :class:`openquake.engine.db.models.HazardCalculation`.
    :param validate:
        Boolean indicating whether or not the tree should be validated
        while parsed. This should be set to ``True`` on initial load
        of the logic tree (before importing it to the database) and
        to ``False`` on workers side (when loaded from the database).
    :raises ParsingError:
        If logic tree file or any of the referenced files is unable to read
        or parse.
    :raises ValidationError:
        If logic tree file has a logic error, which can not be prevented
        by xml schema rules (like referencing sources with missing id).
    """
    NRML = openquake.nrmllib.NAMESPACE
    FILTERS = ('applyToTectonicRegionType',
               'applyToSources',
               'applyToSourceType')

    _xmlschema = None

    __metaclass__ = abc.ABCMeta

    @classmethod
    def get_xmlschema(cls):
        """
        Create (if needed) and return ``etree.XMLSchema`` object
        for verifying nrml-files correctness.

        Once created schema object is cached in ``_xmlschema``
        class attribute.
        """
        if not cls._xmlschema:
            cls._xmlschema = etree.XMLSchema(
                file=openquake.nrmllib.nrml_schema_file())
        return cls._xmlschema

    def __init__(self, content, basepath, filename, calc, validate=True):
        self.basepath = basepath
        self.filename = filename
        self.hc = calc
        parser = etree.XMLParser(schema=self.get_xmlschema())
        self.branches = {}
        self.open_ends = set()
        if isinstance(content, unicode):
            # etree.fromstring() refuses to parse unicode objects
            content = content.encode('latin1')
        try:
            tree = etree.fromstring(content, parser=parser)
        except etree.XMLSyntaxError as exc:
            # Wrap etree parsing exception to :exc:`ParsingError`.
            raise ParsingError(self.filename, self.basepath, str(exc))
        [tree] = tree.findall('{%s}logicTree' % self.NRML)
        self.root_branchset = None
        self.parse_tree(tree, validate)

    def parse_tree(self, tree_node, validate):
        """
        Parse the whole tree and point ``root_branchset`` attribute
        to the tree's root. If ``validate`` is set to ``True``, calls
        :meth:`validate_tree` when done. Also passes that value
        to :meth:`parse_branchinglevel`.
        """
        levels = tree_node.findall('{%s}logicTreeBranchingLevel' % self.NRML)
        for depth, branchinglevel_node in enumerate(levels):
            self.parse_branchinglevel(branchinglevel_node, depth, validate)
        if validate:
            self.validate_tree(tree_node, self.root_branchset)

    def parse_branchinglevel(self, branchinglevel_node, depth, validate):
        """
        Parse one branching level.

        :param branchinglevel_node:
            ``etree.Element`` object with tag "logicTreeBranchingLevel".
        :param depth:
            The sequential number of this branching level, based on 0.
        :param validate:
            Whether or not the branching level, its branchsets and their
            branches should be validated.

        Enumerates children branchsets and call :meth:`parse_branchset`,
        :meth:`validate_branchset`, :meth:`parse_branches` and finally
        :meth:`apply_branchset` for each.

        Keeps track of "open ends" -- the set of branches that don't have
        any child branchset on this step of execution. After processing
        of every branching level only those branches that are listed in it
        can have child branchsets (if there is one on the next level).
        """
        new_open_ends = set()
        branchsets = branchinglevel_node.findall('{%s}logicTreeBranchSet' %
                                                 self.NRML)
        for number, branchset_node in enumerate(branchsets):
            branchset = self.parse_branchset(branchset_node, depth, number,
                                             validate)
            self.parse_branches(branchset_node, branchset, validate)
            if depth == 0 and number == 0:
                self.root_branchset = branchset
            else:
                self.apply_branchset(branchset_node, branchset)
            for branch in branchset.branches:
                new_open_ends.add(branch)
        self.open_ends.clear()
        self.open_ends.update(new_open_ends)

    def parse_branchset(self, branchset_node, depth, number, validate):
        """
        Create :class:`BranchSet` object using data in ``branchset_node``.

        :param branchset_node:
            ``etree.Element`` object with tag "logicTreeBranchSet".
        :param depth:
            The sequential number of branchset's branching level, based on 0.
        :param number:
            Index number of this branchset inside branching level, based on 0.
        :param validate:
            Whether or not filters defined in branchset and the branchset
            itself should be validated.
        :returns:
            An instance of :class:`BranchSet` with filters applied but with
            no branches (they're attached in :meth:`parse_branches`).
        """
        uncertainty_type = branchset_node.get('uncertaintyType')
        filters = dict((filtername, branchset_node.get(filtername))
                       for filtername in self.FILTERS
                       if filtername in branchset_node.attrib)
        if validate:
            self.validate_filters(branchset_node, uncertainty_type, filters)
        filters = self.parse_filters(branchset_node, uncertainty_type, filters)
        branchset = BranchSet(uncertainty_type, filters)
        if validate:
            self.validate_branchset(branchset_node, depth, number, branchset)
        return branchset

    def parse_branches(self, branchset_node, branchset, validate):
        """
        Create and attach branches at ``branchset_node`` to ``branchset``.

        :param branchset_node:
            Same as for :meth:`parse_branchset`.
        :param branchset:
            An instance of :class:`BranchSet`.
        :param validate:
            Whether or not branches' uncertainty values should be validated.

        Checks that each branch has :meth:`valid <validate_uncertainty_value>`
        value, unique id and that all branches have total weight of 1.0.

        :return:
            ``None``, all branches are attached to provided branchset.
        """
        weight_sum = 0
        branches = branchset_node.findall('{%s}logicTreeBranch' % self.NRML)
        for branchnode in branches:
            weight = branchnode.find('{%s}uncertaintyWeight' % self.NRML).text
            weight = Decimal(weight.strip())
            weight_sum += weight
            value_node = branchnode.find('{%s}uncertaintyModel' % self.NRML)
            if validate:
                self.validate_uncertainty_value(value_node, branchset,
                                                value_node.text.strip())
            value = self.parse_uncertainty_value(value_node, branchset,
                                                 value_node.text.strip())
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
        # pylint: disable=W0613
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

        Can be overriden by subclasses. Base class implementation does nothing.

        :param tree_node:
            ``etree.Element`` object with tag "logicTree".
        :param root_branchset:
            An instance of :class:`BranchSet` which is about to become
            the root branchset for this tree.
        """

    @abc.abstractmethod
    def parse_uncertainty_value(self, node, branchset, value):
        """
        Do any kind of type conversion or adaptation on the uncertainty value.

        Abstract method, must be overridden by subclasses.

        Parameters are the same as for :meth:`validate_uncertainty_value`.

        :return:
            Something to replace ``value`` as the uncertainty value.
        """

    @abc.abstractmethod
    def validate_uncertainty_value(self, node, branchset, value):
        """
        Check the value ``value`` for correctness to be set for one
        of branchset's branches.

        Abstract method, must be overridden by subclasses.

        :param node:
            ``etree.Element`` object with tag "uncertaintyModel" (the one
            that contains the subject value).
        :param branchset:
            An instance of :class:`BranchSet` which will have the branch
            with provided value attached once it's validated.
        :param value:
            The actual value to be checked. Type depends on branchset's
            uncertainty type.
        """

    @abc.abstractmethod
    def parse_filters(self, branchset_node, uncertainty_type, filters):
        """
        Do any kind of type conversion or adaptation on the filters.

        Abstract method, must be overriden by subclasses.

        Parameters are the same as for :meth:`validate_filters`.

        :return:
            The filters dictionary to replace the original.
        """

    @abc.abstractmethod
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
        """

    @abc.abstractmethod
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


class SourceModelLogicTree(BaseLogicTree):
    """
    Source model logic tree parser.
    """
    SOURCE_TYPES = ('point', 'area', 'complexFault', 'simpleFault',
                    'characteristicFault')

    def __init__(self, *args, **kwargs):
        self.source_ids = set()
        self.tectonic_region_types = set()
        self.source_types = set()
        super(SourceModelLogicTree, self).__init__(*args, **kwargs)

    def parse_uncertainty_value(self, node, branchset, value):
        """
        See superclass' method for description and signature specification.

        Doesn't change source model file name, converts other values to either
        pair of floats or a single float depending on uncertainty type.
        """
        if branchset.uncertainty_type == 'sourceModel':
            return value
        elif branchset.uncertainty_type == 'abGRAbsolute':
            [a, b] = value.strip().split()
            return float(a), float(b)
        else:
            return float(value)

    def validate_uncertainty_value(self, node, branchset, value):
        """
        See superclass' method for description and signature specification.

        Checks that the following conditions are met:

        * For uncertainty of type "sourceModel": referenced file must exist
          and be readable. This is checked in :meth:`collect_source_model_data`
          along with saving the source model information.
        * For uncertainty of type "abGRAbsolute": value should be two float
          values.
        * For both absolute uncertainties: the source (only one) must
          be referenced in branchset's filter "applyToSources".
        * For all other cases: value should be a single float value.
        """
        _float_re = re.compile(r'^(\+|\-)?(\d+|\d*\.\d+)$')

        if branchset.uncertainty_type == 'sourceModel':
            self.collect_source_model_data(value)

        elif branchset.uncertainty_type == 'abGRAbsolute':
            ab = value.split()
            if len(ab) == 2:
                a, b = ab
                if _float_re.match(a) and _float_re.match(b):
                    return
            raise ValidationError(
                node, self.filename, self.basepath,
                'expected a pair of floats separated by space'
            )
        else:
            if not _float_re.match(value):
                raise ValidationError(
                    node, self.filename, self.basepath,
                    'expected single float value'
                )

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
            raise ValidationError(
                branchset_node, self.filename, self.basepath,
                'filters are not allowed on source model uncertainty'
            )

        if len(filters) > 1:
            raise ValidationError(
                branchset_node, self.filename, self.basepath,
                "only one filter is allowed per branchset"
            )

        if 'applyToTectonicRegionType' in filters:
            if not filters['applyToTectonicRegionType'] \
                    in self.tectonic_region_types:
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    "source models don't define sources of tectonic region "
                    "type %r" % filters['applyToTectonicRegionType']
                )
        if 'applyToSourceType' in filters:
            if not filters['applyToSourceType'] in self.source_types:
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    "source models don't define sources of type %r" %
                    filters['applyToSourceType']
                )

        if 'applyToSources' in filters:
            for source_id in filters['applyToSources'].split():
                if not source_id in self.source_ids:
                    raise ValidationError(
                        branchset_node, self.filename, self.basepath,
                        "source with id %r is not defined in source models"
                        % source_id
                    )

        if uncertainty_type in ('abGRAbsolute', 'maxMagGRAbsolute'):
            if not filters or not filters.keys() == ['applyToSources'] \
                    or not len(filters['applyToSources'].split()) == 1:
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    "uncertainty of type %r must define 'applyToSources' "
                    "with only one source id" % uncertainty_type
                )

    def validate_branchset(self, branchset_node, depth, number, branchset):
        """
        See superclass' method for description and signature specification.

        Checks that the following conditions are met:

        * First branching level must contain exactly one branchset, which
          must be of type "sourceModel".
        * All other branchsets must not be of type "sourceModel"
          or "gmpeModel".
        """
        if depth == 0:
            if number > 0:
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    'there must be only one branch set '
                    'on first branching level'
                )
            elif branchset.uncertainty_type != 'sourceModel':
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    'first branchset must define an uncertainty '
                    'of type "sourceModel"'
                )
        else:
            if branchset.uncertainty_type == 'sourceModel':
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    'uncertainty of type "sourceModel" can be defined '
                    'on first branchset only'
                )
            elif branchset.uncertainty_type == 'gmpeModel':
                raise ValidationError(
                    branchset_node, self.filename, self.basepath,
                    'uncertainty of type "gmpeModel" is not allowed '
                    'in source model logic tree'
                )

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
                        'applyToBranches must reference only branches '
                        'from previous branching level'
                    )
                branch.child_branchset = branchset
        else:
            super(SourceModelLogicTree, self).apply_branchset(branchset_node,
                                                              branchset)

    def collect_source_model_data(self, source_model):
        """
        Parse source model file and collect information about source ids,
        source types and tectonic region types available in it. That
        information is used then for :meth:`validate_filters` and
        :meth:`validate_uncertainty_value`.
        """
        all_source_types = set('{%s}%sSource' % (self.NRML, tagname)
                               for tagname in self.SOURCE_TYPES)
        sourcetype_slice = slice(len('{%s}' % self.NRML), - len('Source'))

        fh = file(os.path.join(self.basepath, source_model))
        eventstream = etree.iterparse(fh, tag='{%s}*' % self.NRML,
                                      schema=self.get_xmlschema())
        while True:
            try:
                _, node = next(eventstream)
            except StopIteration:
                break
            except etree.XMLSyntaxError as exc:
                raise ParsingError(source_model, self.basepath, str(exc))
            if not node.tag in all_source_types:
                continue
            self.tectonic_region_types.add(node.attrib['tectonicRegion'])
            source_id = node.attrib['id']
            source_type = node.tag[sourcetype_slice]
            self.source_ids.add(source_id)
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
    """
    GMPE logic tree parser.

    :param tectonic_region_types:
        Set of all tectonic region type names that are used in corresponding
        source models. Used to check that there are GMPEs for each, but
        no unattended ones. That check is only performed if ``validate``
        parameter is set to ``True`` (see :class:`BaseLogicTree`), otherwise
        it can be an empty sequence.
    """
    #: Base GMPE class (all valid GMPEs must extend it).
    BASE_GMPE = GroundShakingIntensityModel

    def __init__(self, tectonic_region_types, *args, **kwargs):
        self.tectonic_region_types = frozenset(tectonic_region_types)
        self.defined_tectonic_region_types = set()
        super(GMPELogicTree, self).__init__(*args, **kwargs)

    def parse_uncertainty_value(self, node, branchset, classname):
        """
        See superclass' method for description and signature specification.

        Convert gmpe import path to a gmpe object.
        """
        return GSIM[classname]()

    def validate_uncertainty_value(self, node, branchset, value):
        """
        See superclass' method for description and signature specification.

        Checks that the value is a class name in the dictionary reported
        by get_available_gsims, i.e. a GSIM class.
        """
        try:
            GSIM[value]
        except KeyError:
            raise ValidationError(
                node, self.filename, self.basepath,
                'unknown class %r; available classes are: %s' % (
                    value, list(GSIM)))

    def parse_filters(self, node, uncertainty_type, filters):
        """
        See superclass' method for description and signature specification.

        Does nothing, simply returns ``filters``.
        """
        return filters

    def validate_filters(self, node, uncertainty_type, filters):
        """
        See superclass' method for description and signature specification.

        Checks that there is only one filter -- "applyToTectonicRegionType",
        its value is used only once and appears in the set of types, provided
        to constructor.
        """
        if not filters \
                or len(filters) > 1 \
                or filters.keys() != ['applyToTectonicRegionType']:
            raise ValidationError(
                node, self.filename, self.basepath,
                'branch sets in gmpe logic tree must define only '
                '"applyToTectonicRegionType" filter'
            )
        trt = filters['applyToTectonicRegionType']
        if not trt in self.tectonic_region_types:
            raise ValidationError(
                node, self.filename, self.basepath,
                "source models don't define sources of tectonic region "
                "type %r" % trt
            )
        if trt in self.defined_tectonic_region_types:
            raise ValidationError(
                node, self.filename, self.basepath,
                'gmpe uncertainty for tectonic region type %r has already '
                'been defined' % trt
            )
        self.defined_tectonic_region_types.add(trt)

    def validate_tree(self, tree_node, root_branchset):
        """
        See superclass' method for description and signature specification.

        Checks that for all tectonic region types that are defined in source
        models there is a branchset defined.
        """
        missing_trts = self.tectonic_region_types \
            - self.defined_tectonic_region_types
        if missing_trts:
            raise ValidationError(
                tree_node, self.filename, self.basepath,
                'the following tectonic region types are defined '
                'in source model logic tree but not in gmpe logic tree: %s' %
                list(sorted(missing_trts))
            )

    def validate_branchset(self, branchset_node, depth, number, branchset):
        """
        See superclass' method for description and signature specification.

        Checks that uncertainty type is "gmpeModel" (only those are allowed)
        and that there is only one branchset in each branching level.
        """
        if not branchset.uncertainty_type == 'gmpeModel':
            raise ValidationError(
                branchset_node, self.filename, self.basepath,
                'only uncertainties of type "gmpeModel" are allowed '
                'in gmpe logic tree'
            )
        if number != 0:
            raise ValidationError(
                branchset_node, self.filename, self.basepath,
                'only one branchset on each branching level is allowed '
                'in gmpe logic tree'
            )


def read_logic_trees(hc, validate=True):
    """
    :param bool validate:
        Defaults to `True`. If `True`, do a full validation when reading the
        logic trees.
    :param calc:
        a :class:`openquake.engine.db.models.HazardCalculation`.
    """
    [smlt_file] = hc.inputs['source_model_logic_tree']
    [gsimlt_file] = hc.inputs['gsim_logic_tree']

    smlt = SourceModelLogicTree(
        file(smlt_file).read(), hc.base_path, smlt_file, hc,
        validate=validate
    )
    GMPELogicTree(
        smlt.tectonic_region_types, file(gsimlt_file).read(), hc.base_path,
        gsimlt_file, hc, validate=validate
    )
    return [branch.value for branch in smlt.root_branchset.branches]


class LogicTreeProcessor(object):
    """
    Logic tree processor. High-level interface to dealing with logic trees
    that are already in the database.

    :param calc:
        a :class:`openquake.engine.db.models.HazardCalculation`.
    """
    def __init__(self, calc):
        [smlt_input] = calc.inputs['source_model_logic_tree']
        smlt_content = file(smlt_input).read()

        [gmpelt_input] = calc.inputs['gsim_logic_tree']
        gmpelt_content = file(gmpelt_input).read()

        self.source_model_lt = SourceModelLogicTree(
            smlt_content, basepath=None, filename=None, calc=calc,
            validate=False
        )
        self.gmpe_lt = GMPELogicTree(
            tectonic_region_types=[], content=gmpelt_content,
            basepath=None, filename=None, calc=calc, validate=False
        )

    def sample_source_model_logictree(self, random_seed):
        """
        Perform a Monte-Carlo sampling of source model logic tree.

        :param random_seed:
            An integer random seed value to initialize random generator
            before doing random sampling.
        :return:
            Tuple of two items: first is the name of the source model
            to load (as it appears in the source model logic tree)
            and second is a list of the branchIDs (strings) which indicate
            the complete path taken through the logic tree for this sample.
        """
        path = self._sample_path(random_seed, self.source_model_lt)
        sm_b = self.source_model_lt.root_branchset.get_branch_by_id(path[0])
        return sm_b.value, path

    def sample_gmpe_logictree(self, random_seed):
        """
        Same as :meth:`sample_source_model_logictree`, but for GMPE logic tree
        and returns only path (list of branch ids).
        """
        return self._sample_path(random_seed, self.gmpe_lt)

    def _sample_path(self, random_seed, tree):
        """
        Common part of :func:`sample_source_model_logictree` and
        :func:`sample_gmpe_logictree`.
        """
        branch_ids = []
        rnd = random.Random(random_seed)
        branchset = tree.root_branchset
        while branchset is not None:
            branch = branchset.sample(rnd)
            branch_ids.append(branch.branch_id)
            branchset = branch.child_branchset
        return branch_ids

    def enumerate_paths(self):
        """
        Generate all the possible paths through both logic trees.

        :returns:
            Generator of four items:

            #. Source model file name, as a string.
            #. Path's weight (decimal between 0 and 1). Sum of all paths'
               weights is equal to 1.
            #. List of source-model logic tree branch ids.
            #. List of GMPE logic tree branch ids.
        """
        smlt_paths_gen = self.source_model_lt.root_branchset.enumerate_paths
        gmpelt_paths_gen = self.gmpe_lt.root_branchset.enumerate_paths

        for smlt_path_weight, smlt_path in smlt_paths_gen():
            for gmpelt_path_weight, gmpelt_path in gmpelt_paths_gen():
                weight = smlt_path_weight * gmpelt_path_weight
                sm_name = smlt_path[0].value

                smlt_branch_ids = [branch.branch_id for branch in smlt_path]
                gmpelt_branch_ids = [
                    branch.branch_id for branch in gmpelt_path]

                yield sm_name, weight, smlt_branch_ids, gmpelt_branch_ids

    def parse_source_model_logictree_path(self, branch_ids):
        """
        Parse the path through the source model logic tree and return
        "apply uncertainties" function.

        :param branch_ids:
            List of string identifiers of branches, representing the path
            through source model logic tree.
        :return:
            Function to be applied to all the sources as they get read from
            the database and converted to hazardlib representation. Function
            takes one argument, that is the hazardlib source object, and
            applies uncertainties to it in-place.
        """
        branchset = self.source_model_lt.root_branchset
        branchsets_and_uncertainties = []
        branch_ids = branch_ids[::-1]

        while branchset is not None:
            branch = branchset.get_branch_by_id(branch_ids.pop(-1))
            if not branchset.uncertainty_type == 'sourceModel':
                branchsets_and_uncertainties.append((branchset, branch.value))
            branchset = branch.child_branchset

        def apply_uncertainties(source):
            for branchset, value in branchsets_and_uncertainties:
                branchset.apply_uncertainty(value, source)

        return apply_uncertainties

    def parse_gmpe_logictree_path(self, branch_ids):
        """
        Same as :meth:`parse_source_model_logictree_path`, but for GMPE logic
        tree.

        :return:
            Dictionary mapping tectonic region type names to instances
            of hazardlib GSIM objects.
        """
        branchset = self.gmpe_lt.root_branchset
        trt_to_gsim = {}
        branch_ids = branch_ids[::-1]

        while branchset is not None:
            branch = branchset.get_branch_by_id(branch_ids.pop(-1))
            trt = branchset.filters['applyToTectonicRegionType']

            assert trt not in trt_to_gsim
            trt_to_gsim[trt] = branch.value
            branchset = branch.child_branchset

        return trt_to_gsim
