# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2026 GEM Foundation
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
Epistemic uncertainty on the site model.

A site-model logic tree is a NRML XML file with a single branchset of
``uncertaintyType="siteModel"``; each branch points at a site-model CSV
(or XML) file and carries a weight. All branches must reference the same
sites (identical lon/lat, in the same order); only per-site parameters
(vs30, z1pt0, z2pt5, ...) may differ across branches.
"""
import os
import numpy
from openquake.baselib import hdf5
from openquake.baselib.general import BASE183
from openquake.hazardlib import InvalidFile, nrml
from openquake.hazardlib.lt import Realization

F32 = numpy.float32


class SiteRealization(Realization):
    """
    Realization for a single site-model branch. Behaves like the generic
    Realization but carries a short_id used to build the third leg of
    the composite path (SSC~GMM~SITE).
    """


class SiteModelLogicTree(object):
    """
    Parser and container for a site-model logic tree.

    :param filename:
        path to the NRML XML file
    :param base_path:
        directory used to resolve relative CSV/XML filenames referenced
        in the XML (defaults to the directory holding the XML itself)
    """
    filename = ''

    @classmethod
    def _iter_branchsets(cls, lt_node):
        # yield every <logicTreeBranchSet> under a <logicTree>, tolerating
        # both flat and <logicTreeBranchingLevel>-wrapped layouts
        for child in lt_node:
            if child.tag.endswith('logicTreeBranchSet'):
                yield child
            elif child.tag.endswith('logicTreeBranchingLevel'):
                for bset in child:
                    if bset.tag.endswith('logicTreeBranchSet'):
                        yield bset

    @classmethod
    def is_site_model_lt(cls, filename):
        """
        :returns: True if the given XML file is a site-model logic tree
        """
        try:
            root = nrml.read(filename)
        except Exception:
            return False
        try:
            lt = root.logicTree
        except AttributeError:
            return False
        try:
            for bset in cls._iter_branchsets(lt):
                if bset.attrib.get('uncertaintyType') == 'siteModel':
                    return True
        except Exception:
            return False
        return False

    def __init__(self, filename, base_path=None):
        self.filename = filename
        self.base_path = base_path or os.path.dirname(filename)
        self.branches = []  # list of (branchID, filename, weight)
        self._parse()

    def _parse(self):
        root = nrml.read(self.filename)
        try:
            lt = root.logicTree
        except AttributeError:
            raise InvalidFile(
                '%s: missing <logicTree> element' % self.filename)
        found_bset = False
        for bset in self._iter_branchsets(lt):
            utype = bset.attrib.get('uncertaintyType')
            if utype != 'siteModel':
                raise InvalidFile(
                    '%s: only uncertaintyType="siteModel" is supported '
                    'in a site-model logic tree, got %r'
                    % (self.filename, utype))
            if found_bset:
                raise InvalidFile(
                    '%s: only one <logicTreeBranchSet> is supported'
                    % self.filename)
            found_bset = True
            for br in bset:
                brid = br.attrib.get('branchID', '')
                csv_rel = br.uncertaintyModel.text.strip()
                weight = float(br.uncertaintyWeight.text)
                csv_abs = os.path.normpath(
                    os.path.join(self.base_path, csv_rel))
                self.branches.append((brid, csv_abs, weight))
        if not found_bset:
            raise InvalidFile(
                '%s: no siteModel branchset found' % self.filename)
        if len(self.branches) < 2:
            raise InvalidFile(
                '%s: a site-model logic tree needs at least 2 branches'
                % self.filename)
        # weights must sum to 1
        wsum = sum(w for _, _, w in self.branches)
        if abs(wsum - 1.) > 1e-5:
            raise InvalidFile(
                '%s: siteModel branch weights sum to %s, expected 1.0'
                % (self.filename, wsum))

    @property
    def filenames(self):
        return [f for _, f, _ in self.branches]

    @property
    def weights(self):
        return numpy.array([w for _, _, w in self.branches])

    @property
    def branch_ids(self):
        return [b for b, _, _ in self.branches]

    def get_num_paths(self):
        return len(self.branches)

    def __repr__(self):
        return '<SiteModelLogicTree %s, %d branches>' % (
            os.path.basename(self.filename), len(self.branches))


class SiteModelsEpistemic(object):
    """
    In-memory container of the site-model realizations for a calculation.

    :param names:
        list of short names, one per branch (usually the branchIDs)
    :param weights:
        1D numpy array of branch weights, summing to 1
    :param arrays:
        list of structured site-model arrays (one per branch); all arrays
        must have identical length, identical lon/lat (in the same order)
        and identical field sets
    :param filenames:
        list of the CSV/XML source filenames (informational)

    Validation of lon/lat consistency happens at construction time; any
    mismatch raises :class:`openquake.hazardlib.InvalidFile`.
    """

    def __init__(self, names, weights, arrays, filenames=None):
        assert len(names) == len(weights) == len(arrays), (
            len(names), len(weights), len(arrays))
        self.names = list(names)
        self.weights = numpy.asarray(weights, F32)
        self.arrays = list(arrays)
        self.filenames = list(filenames) if filenames else list(names)
        self._validate()

    def _validate(self):
        ref = self.arrays[0]
        ref_name = self.filenames[0]
        n = len(ref)
        for other, oname in zip(self.arrays[1:], self.filenames[1:]):
            if len(other) != n:
                raise InvalidFile(
                    'Site models %s (%d sites) and %s (%d sites) have '
                    'different numbers of sites'
                    % (ref_name, n, oname, len(other)))
            if not numpy.allclose(ref['lon'], other['lon']) or \
                    not numpy.allclose(ref['lat'], other['lat']):
                raise InvalidFile(
                    'Site models %s and %s must have identical (lon, lat) '
                    'coordinates in the same order' % (ref_name, oname))
            if set(other.dtype.names) != set(ref.dtype.names):
                diff = (set(ref.dtype.names) ^ set(other.dtype.names))
                raise InvalidFile(
                    'Site models %s and %s have different field sets '
                    '(differing fields: %s)'
                    % (ref_name, oname, sorted(diff)))

    def __len__(self):
        return len(self.arrays)

    @property
    def R(self):
        """
        :returns: number of site-model realizations
        """
        return len(self.arrays)

    def get_realizations(self):
        """
        :returns: a list of :class:`SiteRealization` objects
        """
        rlzs = []
        for i, (name, w) in enumerate(zip(self.names, self.weights)):
            rlzs.append(SiteRealization(
                value=name, weight=float(w), ordinal=i,
                lt_path=(name,), samples=1))
        return rlzs

    @property
    def shortener(self):
        """
        :returns: dict branchID -> short character (a, b, c, ...) used to
            build the third leg of the composite realization path;
            lowercase is used so the site leg is visually distinct from
            the SSC (uppercase) and GSIM (digits) legs
        """
        chars = 'abcdefghijklmnopqrstuvwxyz'
        if self.R > len(chars):
            # fall back to BASE183 for large trees
            return {name: BASE183[i] for i, name in enumerate(self.names)}
        return {name: chars[i] for i, name in enumerate(self.names)}

    def __repr__(self):
        return '<SiteModelsEpistemic R=%d weights=%s>' % (
            self.R, self.weights.tolist())


site_model_lt_dt = numpy.dtype([
    ('name', hdf5.vstr),
    ('weight', F32),
    ('filename', hdf5.vstr),
])
