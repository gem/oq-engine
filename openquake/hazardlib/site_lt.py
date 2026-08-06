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
Epistemic uncertainty on the site model: a NRML logic tree whose single
``uncertaintyType="siteModel"`` branchset lists per-branch site-model
files with weights summing to 1
"""
import os
import numpy

from openquake.baselib import hdf5
from openquake.baselib.general import BASE183
from openquake.hazardlib import InvalidFile, nrml
from openquake.hazardlib import lt
from openquake.hazardlib.lt import Realization


F32 = numpy.float32


def _iter_branchsets(lt_node):
    # Tolerate both flat and <logicTreeBranchingLevel>-wrapped layouts
    for child in lt_node:
        if child.tag.endswith('logicTreeBranchSet'):
            yield child
        elif child.tag.endswith('logicTreeBranchingLevel'):
            for bset in child:
                if bset.tag.endswith('logicTreeBranchSet'):
                    yield bset


class SiteModelLogicTree(object):
    """
    Parser for a site-model logic tree NRML XML
    """
    filename = ''

    @classmethod
    def is_site_model_lt(cls, filename):
        """
        :returns: ``True`` if the given XML file is a site-model logic tree
        """
        try:
            root = nrml.read(filename)
            for bset in _iter_branchsets(root.logicTree):
                if bset.attrib.get('uncertaintyType') == 'siteModel':
                    return True
        except Exception:
            pass
        return False

    def __init__(self, filename, base_path=None):
        self.filename = filename
        self.base_path = base_path or os.path.dirname(filename)
        self.branches = []  # list of (branchID, filename, weight)
        self.branchset_id = ''
        self._parse()

    def _parse(self):
        root = nrml.read(self.filename)
        try:
            ltree = root.logicTree
        except AttributeError:
            raise InvalidFile(
                '%s: missing <logicTree> element' % self.filename)
        bsets = list(_iter_branchsets(ltree))
        if not bsets:
            raise InvalidFile(
                '%s: no siteModel branchset found' % self.filename)
        if len(bsets) > 1:
            raise InvalidFile(
                '%s: only one <logicTreeBranchSet> is supported'
                % self.filename)
        [bset] = bsets
        utype = bset.attrib.get('uncertaintyType')
        if utype != 'siteModel':
            raise InvalidFile(
                '%s: only uncertaintyType="siteModel" is supported '
                'in a site-model logic tree, got %r'
                % (self.filename, utype))
        self.branchset_id = bset.attrib.get('branchSetID', 'bs_site')
        for br in bset:
            brid = br.attrib.get('branchID', '')
            rel = br.uncertaintyModel.text.strip()
            weight = float(br.uncertaintyWeight.text)
            fname = os.path.normpath(os.path.join(self.base_path, rel))
            self.branches.append((brid, fname, weight))
        brids = [b for b, _, _ in self.branches]
        if len(set(brids)) != len(brids):
            dups = sorted({b for b in brids if brids.count(b) > 1})
            raise InvalidFile(
                '%s: duplicate branchID(s) in site-model logic tree: %s'
                % (self.filename, dups))
        # Keeps the site leg of the composite path a single BASE183 char
        if len(self.branches) > len(BASE183):
            raise InvalidFile(
                '%s: too many branches (%d > %d)'
                % (self.filename, len(self.branches), len(BASE183)))
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
    Container holding one structured site-model array per branch; branches
    share identical geometry (``lon``, ``lat``, and ``depth`` if present)
    and field sets
    """
    def __init__(self, names, weights, arrays, filenames=None,
                 tree_filename='', branchset_id='bs_site'):
        self.names = list(names)
        self.weights = numpy.asarray(weights, F32)
        self.arrays = list(arrays)
        self.filenames = list(filenames) if filenames else list(names)
        self.filename = tree_filename
        self.branchset_id = branchset_id
        self._validate()

    def _validate(self):
        # NOTE: custom_site_id is intentionally not checked - users might
        # use it to denote per-branch differences at the same location
        ref = self.arrays[0]
        ref_name = self.filenames[0]
        n = len(ref)
        for other, oname in zip(self.arrays[1:], self.filenames[1:]):
            if len(other) != n:
                raise InvalidFile(
                    'Site models %s (%d sites) and %s (%d sites) have '
                    'different numbers of sites'
                    % (ref_name, n, oname, len(other)))
            if set(other.dtype.names) != set(ref.dtype.names):
                diff = set(ref.dtype.names) ^ set(other.dtype.names)
                raise InvalidFile(
                    'Site models %s and %s have different field sets '
                    '(differing fields: %s)'
                    % (ref_name, oname, sorted(diff)))
            for name in ('lon', 'lat', 'depth'):
                if name in ref.dtype.names and not numpy.allclose(
                        ref[name], other[name]):
                    raise InvalidFile(
                        'Site models %s and %s must have identical %s '
                        'values in the same order'
                        % (ref_name, oname, name))

    def __len__(self):
        return len(self.arrays)

    @property
    def Rsite(self):
        """
        :returns: number of site-model realizations
        """
        return len(self.arrays)

    def get_realizations(self):
        """
        :returns: a list of :class:`Realization` objects, one per branch
        """
        return [Realization(value=name, weight=float(w), ordinal=i,
                            lt_path=(name,), samples=1)
                for i, (name, w) in enumerate(zip(self.names, self.weights))]

    def sample(self, n, seed, sampling_method='early_weights'):
        """
        Monte-Carlo sample ``n`` site branches with prob = branch weight;
        returns :class:`Realization` objects (branches may repeat or be absent)
        """
        probs = lt.random(n, seed, sampling_method)
        return lt.sample(self.get_realizations(), probs, sampling_method)

    @property
    def shortener(self):
        """
        :returns: dict ``branchID -> single BASE183 character`` (consistent
            with the SSC and GSIM shorteners)
        """
        return {name: BASE183[i] for i, name in enumerate(self.names)}

    def __repr__(self):
        return '<SiteModelsEpistemic Rsite=%d weights=%s>' % (
            self.Rsite, self.weights.tolist())


site_model_lt_dt = numpy.dtype([
    ('name', hdf5.vstr),
    ('weight', F32),
    ('filename', hdf5.vstr),
])
