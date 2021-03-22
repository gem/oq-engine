# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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

import copy
import collections
import numpy

from openquake.baselib.general import CallableDict
from openquake.hazardlib import geo, source as ohs
from openquake.hazardlib.sourceconverter import (
    split_coords_2d, split_coords_3d)


class LogicTreeError(Exception):
    """
    Logic tree file contains a logic error.

    :param node:
        XML node object that causes fail. Used to determine
        the affected line number.

    All other constructor parameters are passed to :class:`superclass'
    <LogicTreeError>` constructor.
    """
    def __init__(self, node, filename, message):
        self.filename = filename
        self.message = message
        self.lineno = node if isinstance(node, int) else getattr(
            node, 'lineno', '?')

    def __str__(self):
        return "filename '%s', line %s: %s" % (
            self.filename, self.lineno, self.message)


#                           parse_uncertainty                              #


def unknown(utype, node, filename):
    try:
        return float(node.text)
    except (TypeError, ValueError):
        raise LogicTreeError(node, filename, 'expected single float value')


parse_uncertainty = CallableDict(keymissing=unknown)


@parse_uncertainty.add('sourceModel', 'extendModel')
def smodel(utype, node, filename):
    return node.text.strip()


@parse_uncertainty.add('abGRAbsolute')
def abGR(utype, node, filename):
    try:
        [a, b] = node.text.split()
        return float(a), float(b)
    except ValueError:
        raise LogicTreeError(
            node, filename, 'expected a pair of floats separated by space')


@parse_uncertainty.add('incrementalMFDAbsolute')
def incMFD(utype, node, filename):
    min_mag, bin_width = (node.incrementalMFD["minMag"],
                          node.incrementalMFD["binWidth"])
    return min_mag,  bin_width, ~node.incrementalMFD.occurRates


@parse_uncertainty.add('truncatedGRFromSlipAbsolute')
def trucMFDFromSlip_absolute(utype, node, filename):
    slip_rate, rigidity = (node.faultActivityData["slipRate"],
                           node.faultActivityData["rigidity"])
    return slip_rate, rigidity


@parse_uncertainty.add('simpleFaultGeometryAbsolute')
def simpleGeom(utype, node, filename):
    if hasattr(node, 'simpleFaultGeometry'):
        node = node.simpleFaultGeometry
    _validate_simple_fault_geometry(utype, node, filename)
    spacing = node["spacing"]
    usd, lsd, dip = (~node.upperSeismoDepth, ~node.lowerSeismoDepth,
                     ~node.dip)
    coords = split_coords_2d(~node.LineString.posList)
    trace = geo.Line([geo.Point(*p) for p in coords])
    return trace, usd, lsd, dip, spacing


@parse_uncertainty.add('complexFaultGeometryAbsolute')
def complexGeom(utype, node, filename):
    if hasattr(node, 'complexFaultGeometry'):
        node = node.complexFaultGeometry
    _validate_complex_fault_geometry(utype, node, filename)
    spacing = node["spacing"]
    edges = []
    for edge_node in node.nodes:
        coords = split_coords_3d(~edge_node.LineString.posList)
        edges.append(geo.Line([geo.Point(*p) for p in coords]))
    return edges, spacing


@parse_uncertainty.add('characteristicFaultGeometryAbsolute')
def charGeom(utype, node, filename):
    surfaces = []
    for geom_node in node.surface:
        if "simpleFaultGeometry" in geom_node.tag:
            _validate_simple_fault_geometry(utype, geom_node, filename)
            trace, usd, lsd, dip, spacing = parse_uncertainty(
                'simpleFaultGeometryAbsolute', geom_node, filename)
            surfaces.append(geo.SimpleFaultSurface.from_fault_data(
                trace, usd, lsd, dip, spacing))
        elif "complexFaultGeometry" in geom_node.tag:
            _validate_complex_fault_geometry(utype, geom_node, filename)
            edges, spacing = parse_uncertainty(
                'complexFaultGeometryAbsolute', geom_node, filename)
            surfaces.append(geo.ComplexFaultSurface.from_fault_data(
                edges, spacing))
        elif "planarSurface" in geom_node.tag:
            _validate_planar_fault_geometry(utype, geom_node, filename)
            nodes = []
            for key in ["topLeft", "topRight", "bottomRight", "bottomLeft"]:
                nodes.append(geo.Point(getattr(geom_node, key)["lon"],
                                       getattr(geom_node, key)["lat"],
                                       getattr(geom_node, key)["depth"]))
            top_left, top_right, bottom_right, bottom_left = tuple(nodes)
            surface = geo.PlanarSurface.from_corner_points(
                top_left, top_right, bottom_right, bottom_left)
            surfaces.append(surface)
        else:
            raise LogicTreeError(
                geom_node, filename, "Surface geometry type not recognised")
    if len(surfaces) > 1:
        return geo.MultiSurface(surfaces)
    else:
        return surfaces[0]


# validations

def _validate_simple_fault_geometry(utype, node, filename):
    try:
        coords = split_coords_2d(~node.LineString.posList)
        trace = geo.Line([geo.Point(*p) for p in coords])
    except ValueError:
        # If the geometry cannot be created then use the LogicTreeError
        # to point the user to the incorrect node. Hence, if trace is
        # compiled successfully then len(trace) is True, otherwise it is
        # False
        trace = []
    if len(trace):
        return
    raise LogicTreeError(
        node, filename, "'simpleFaultGeometry' node is not valid")


def _validate_complex_fault_geometry(utype, node, filename):
    # NB: if the geometry does not conform to the Aki & Richards convention
    # this will not be verified here, but will raise an error when the surface
    # is created
    valid_edges = []
    for edge_node in node.nodes:
        try:
            coords = split_coords_3d(edge_node.LineString.posList.text)
            edge = geo.Line([geo.Point(*p) for p in coords])
        except ValueError:
            # See use of validation error in simple geometry case
            # The node is valid if all of the edges compile correctly
            edge = []
        if len(edge):
            valid_edges.append(True)
        else:
            valid_edges.append(False)
    if node["spacing"] and all(valid_edges):
        return
    raise LogicTreeError(
        node, filename, "'complexFaultGeometry' node is not valid")


def _validate_planar_fault_geometry(utype, node, filename):
    valid_spacing = node["spacing"]
    for key in ["topLeft", "topRight", "bottomLeft", "bottomRight"]:
        lon = getattr(node, key)["lon"]
        lat = getattr(node, key)["lat"]
        depth = getattr(node, key)["depth"]
        valid_lon = (lon >= -180.0) and (lon <= 180.0)
        valid_lat = (lat >= -90.0) and (lat <= 90.0)
        valid_depth = (depth >= 0.0)
        is_valid = valid_lon and valid_lat and valid_depth
        if not is_valid or not valid_spacing:
            raise LogicTreeError(
                node, filename, "'planarFaultGeometry' node is not valid")


#                         apply_uncertainty                                #

apply_uncertainty = CallableDict()


@apply_uncertainty.add('simpleFaultDipRelative')
def _simple_fault_dip_relative(utype, source, value):
    source.modify('adjust_dip', dict(increment=value))


@apply_uncertainty.add('simpleFaultDipAbsolute')
def _simple_fault_dip_absolute(bset, source, value):
    source.modify('set_dip', dict(dip=value))


@apply_uncertainty.add('simpleFaultGeometryAbsolute')
def _simple_fault_geom_absolute(utype, source, value):
    trace, usd, lsd, dip, spacing = value
    source.modify(
        'set_geometry',
        dict(fault_trace=trace, upper_seismogenic_depth=usd,
             lower_seismogenic_depth=lsd, dip=dip, spacing=spacing))


@apply_uncertainty.add('complexFaultGeometryAbsolute')
def _complex_fault_geom_absolute(utype, source, value):
    edges, spacing = value
    source.modify('set_geometry', dict(edges=edges, spacing=spacing))


@apply_uncertainty.add('characteristicFaultGeometryAbsolute')
def _char_fault_geom_absolute(utype, source, value):
    source.modify('set_geometry', dict(surface=value))


@apply_uncertainty.add('abGRAbsolute')
def _abGR_absolute(utype, source, value):
    a, b = value
    source.mfd.modify('set_ab', dict(a_val=a, b_val=b))


@apply_uncertainty.add('bGRRelative')
def _abGR_relative(utype, source, value):
    source.mfd.modify('increment_b', dict(value=value))


@apply_uncertainty.add('maxMagGRRelative')
def _maxmagGR_relative(utype, source, value):
    source.mfd.modify('increment_max_mag', dict(value=value))


@apply_uncertainty.add('maxMagGRAbsolute')
def _maxmagGR_absolute(utype, source, value):
    source.mfd.modify('set_max_mag', dict(value=value))


@apply_uncertainty.add('incrementalMFDAbsolute')
def _incMFD_absolute(utype, source, value):
    min_mag, bin_width, occur_rates = value
    source.mfd.modify('set_mfd', dict(min_mag=min_mag, bin_width=bin_width,
                                      occurrence_rates=occur_rates))


@apply_uncertainty.add('truncatedGRFromSlipAbsolute')
def _trucMFDFromSlip_absolute(utype, source, value):
    slip_rate, rigidity = value
    source.modify('adjust_mfd_from_slip', dict(slip_rate=slip_rate,
                                               rigidity=rigidity))


# ######################### apply_uncertainties ########################### #

def apply_uncertainties(bset_values, src_group):
    """
    :param bset_value: a list of pairs (branchset, value)
        List of branch IDs
    :param src_group:
        SourceGroup instance
    :returns:
        A copy of the original group with possibly modified sources
    """
    sg = copy.copy(src_group)
    sg.sources = []
    sg.changes = 0
    for source in src_group:
        oks = [bset.filter_source(source) for bset, value in bset_values]
        if sum(oks):  # source not filtered out
            src = copy.deepcopy(source)
            srcs = []
            for (bset, value), ok in zip(bset_values, oks):
                if ok and bset.collapsed:
                    if src.code == b'N':
                        raise NotImplementedError(
                            'Collapsing of the logic tree is not implemented '
                            'for %s' % src)
                    for br in bset.branches:
                        newsrc = copy.deepcopy(src)
                        newsrc.scaling_rate = br.weight
                        apply_uncertainty(
                            bset.uncertainty_type, newsrc, br.value)
                        srcs.append(newsrc)
                    sg.changes += len(srcs)
                elif ok:
                    if not srcs:  # only the first time
                        srcs.append(src)
                    apply_uncertainty(bset.uncertainty_type, src, value)
                    sg.changes += 1
        else:
            srcs = [copy.copy(source)]  # this is ultra-fast
        sg.sources.extend(srcs)
    return sg

# ######################### sampling ######################## #


def random(size, seed, sampling_method='early_weights'):
    """
    :param size: size of the returned array (integer or pair of integers)
    :param seed: random seed
    :param sampling_method: 'early_weights', 'early_latin', ...
    :returns: an array of floats in the range 0..1

    You can compare montecarlo sampling with latin square sampling with
    the following code:

    import matplotlib.pyplot as plt
    samples, seed = 10, 42
    x, y = random((samples, 2), seed, 'early_latin').T
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.scatter(x, y, color='green')  # points on a latin square
    x, y = random((samples, 2), seed, 'early_weights').T
    plt.scatter(x, y, color='red')  # points NOT on a latin square
    for x in numpy.arange(0, 1, 1/samples):
        for y in numpy.arange(0, 1, 1/samples):
            plt.axvline(x)
            plt.axhline(y)
    plt.show()
    """
    numpy.random.seed(seed)
    xs = numpy.random.uniform(size=size)
    if sampling_method.endswith('latin'):
        # https://zmurchok.github.io/2019/03/15/Latin-Hypercube-Sampling.html
        try:
            s, d = size
        except TypeError:  # cannot unpack non-iterable int object
            return (numpy.argsort(xs) + xs) / size
        for i in range(d):
            xs[:, i] = (numpy.argsort(xs[:, i]) + xs[:, i]) / s
    return xs


def _cdf(weighted_objects):
    weights = []
    for obj in weighted_objects:
        w = obj.weight
        if isinstance(obj.weight, float):
            weights.append(w)
        else:
            weights.append(w['weight'])
    return numpy.cumsum(weights)


def sample(weighted_objects, probabilities, sampling_method):
    """
    Take random samples of a sequence of weighted objects

    :param weighted_objects:
        A finite sequence of N objects with a `.weight` attribute.
        The weights must sum up to 1.
    :param probabilities:
        An array of S random numbers in the range 0..1
    :return:
        A list of S objects extracted randomly
    """
    if sampling_method.startswith('early'):  # consider the weights
        idxs = numpy.searchsorted(_cdf(weighted_objects), probabilities)
    elif sampling_method.startswith('late'):
        n = len(weighted_objects)  # consider all weights equal
        idxs = numpy.searchsorted(numpy.arange(1/n, 1, 1/n), probabilities)
    # NB: returning an array would break things
    return [weighted_objects[idx] for idx in idxs]


Weighted = collections.namedtuple('Weighted', 'object weight')


# used in notebooks for teaching, not in the engine
def random_sample(branchsets, num_samples, seed, sampling_method):
    """
    >>> bsets = [[('X', .4), ('Y', .6)], [('A', .2), ('B', .3), ('C', .5)]]
    >>> paths = random_sample(bsets, 100, 42, 'early_weights')
    >>> collections.Counter(paths)
    Counter({'YC': 26, 'XC': 24, 'YB': 17, 'XA': 13, 'YA': 10, 'XB': 10})

    >>> paths = random_sample(bsets, 100, 42, 'late_weights')
    >>> collections.Counter(paths)
    Counter({'XA': 20, 'YA': 18, 'XB': 17, 'XC': 15, 'YB': 15, 'YC': 15})

    >>> paths = random_sample(bsets, 100, 42, 'early_latin')
    >>> collections.Counter(paths)
    Counter({'YC': 31, 'XC': 19, 'YB': 17, 'XB': 13, 'YA': 12, 'XA': 8})

    >>> paths = random_sample(bsets, 100, 45, 'late_latin')
    >>> collections.Counter(paths)
    Counter({'YC': 18, 'XA': 18, 'XC': 16, 'YA': 16, 'XB': 16, 'YB': 16})
    """
    probs = random((num_samples, len(branchsets)), seed, sampling_method)
    arr = numpy.zeros((num_samples, len(branchsets)), object)
    for b, bset in enumerate(branchsets):
        arr[:, b] = sample([Weighted(*it) for it in bset], probs[:, b],
                           sampling_method)
    return [''.join(w.object for w in row) for row in arr]


# ######################### branches and branchsets ######################## #


class Branch(object):
    """
    Branch object, represents a ``<logicTreeBranch />`` element.

    :param bs_id:
        BranchSetID of the branchset to which the branch belongs
    :param branch_id:
        String identifier of the branch
    :param weight:
        float value of weight assigned to the branch. A text node contents
        of ``<uncertaintyWeight />`` child node.
    :param value:
        The actual uncertainty parameter value. A text node contents
        of ``<uncertaintyModel />`` child node. Type depends
        on the branchset's uncertainty type.
    """
    def __init__(self, bs_id, branch_id, weight, value):
        self.bs_id = bs_id
        self.branch_id = branch_id
        self.weight = weight
        self.value = value
        self.bset = None

    def __repr__(self):
        if self.bset:
            return '%s%s' % (self.branch_id, self.bset)
        else:
            return self.branch_id


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
        incrementalMFDAbsolute
            Replaces an evenly discretized MFD with the values provided
        simpleFaultDipRelative
            Increases or decreases the angle of fault dip from that given
            in the original source model
        simpleFaultDipAbsolute
            Replaces the fault dip in the specified source(s)
        simpleFaultGeometryAbsolute
            Replaces the simple fault geometry (trace, upper seismogenic depth
            lower seismogenic depth and dip) of a given source with the values
            provided
        complexFaultGeometryAbsolute
            Replaces the complex fault geometry edges of a given source with
            the values provided
        characteristicFaultGeometryAbsolute
            Replaces the complex fault geometry surface of a given source with
            the values provided
        truncatedGRFromSlipAbsolute
            Updates a TruncatedGR using a slip rate and a rigidity

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
    def __init__(self, uncertainty_type, ordinal=0, filters=None,
                 collapsed=False):
        self.uncertainty_type = uncertainty_type
        self.ordinal = ordinal
        self.filters = filters or {}
        self.collapsed = collapsed
        self.branches = []

    def sample(self, probabilities, sampling_method):
        """
        :param num_samples: the number of samples
        :param probabilities: (Ns, Nb) random numbers in the range 0..1
        :param sampling_method: the sampling method used
        :returns: a list of num_samples lists of branches
        """
        out = []
        for probs in probabilities:  # probs has a value for each branchset
            branchset = self
            branches = []
            while branchset is not None:
                if branchset.collapsed:
                    branch = branchset.branches[0]
                else:
                    x = probs[branchset.ordinal]
                    [branch] = sample(branchset.branches, [x], sampling_method)
                branches.append(branch)
                branchset = branch.bset
            out.append(branches)
        return out

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
            weight = 1.0
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
        if self.collapsed:
            b0 = copy.copy(self.branches[0])
            b0.weight = 1.0
            branches = [b0]
        else:
            branches = self.branches
        for branch in branches:
            path = [prefix_path, branch]
            if branch.bset is not None:
                yield from branch.bset._enumerate_paths(path)
            else:
                yield path

    def __getitem__(self, branch_id):
        """
        Return :class:`Branch` object belonging to this branch set with id
        equal to ``branch_id``.
        """
        for branch in self.branches:
            if branch.branch_id == branch_id:
                return branch
        raise KeyError(branch_id)

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
                    if not isinstance(source, ohs.AreaSource):
                        return False
                elif value == 'point':
                    # area source extends point source
                    if (not isinstance(source, ohs.PointSource)
                            or isinstance(source, ohs.AreaSource)):
                        return False
                elif value == 'simpleFault':
                    if not isinstance(source, ohs.SimpleFaultSource):
                        return False
                elif value == 'complexFault':
                    if not isinstance(source, ohs.ComplexFaultSource):
                        return False
                elif value == 'characteristicFault':
                    if not isinstance(source, ohs.CharacteristicFaultSource):
                        return False
                else:
                    raise AssertionError("unknown source type '%s'" % value)
            elif key == 'applyToSources':
                if source and source.source_id not in value:
                    return False
            else:
                raise AssertionError("unknown filter '%s'" % key)
        # All filters pass, return True.
        return True

    def get_bset_values(self, ltpath):
        """
        :param ltpath:
            List of branch IDs
        :returns:
            A list of pairs [(bset, value), ...]
        """
        pairs = []
        bset = self
        while ltpath:
            brid, ltpath = ltpath[0], ltpath[1:]
            pairs.append((bset, bset[brid].value))
            bset = bset[brid].bset
            if bset is None:
                break
        return pairs

    def __str__(self):
        return repr(self.branches)

    def __repr__(self):
        return '<%s>' % ' '.join(br.branch_id for br in self.branches)
