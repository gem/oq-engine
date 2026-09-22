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
Epistemic uncertainty on the site-amplification function: a NRML logic
tree whose single uncertaintyType="amplificationModel" branchset lists
per-branch amplification CSV files with weights summing to 1
"""
import os
import numpy

from openquake.baselib import hdf5
from openquake.baselib.general import BASE183, decode
from openquake.hazardlib import InvalidFile, nrml
from openquake.hazardlib.lt import Realization, random, sample


F32 = numpy.float32

# amp-LT branch record: name, weight, per-branch CSV filename
amp_lt_dt = numpy.dtype([
    ('name', hdf5.vstr),
    ('weight', F32),
    ('filename', hdf5.vstr),
])


class AmplificationLogicTreeParser(object):
    """
    Parser for an amplification-function logic tree NRML XML
    """
    filename = ''

    @classmethod
    def is_amp_lt(cls, filename):
        """
        :returns: True if the given file is an amplification logic tree XML
        """
        if not filename.lower().endswith('.xml'):
            return False
        root = nrml.read(filename)
        if not hasattr(root, 'logicTree'):
            return False
        for child in root.logicTree:
            if (child.tag.endswith('logicTreeBranchSet') and
                    child.attrib.get('uncertaintyType') == 'amplificationModel'):
                return True
        return False

    def __init__(self, filename, base_path=None):
        self.filename = filename
        self.base_path = base_path or os.path.dirname(filename)
        self.branches = [] # List of (branchID, filename, weight)
        self.branchset_id = ''
        self._parse()

    def _parse(self):
        root = nrml.read(self.filename)
        if not hasattr(root, 'logicTree'):
            raise InvalidFile(
                '%s: missing <logicTree> element' % self.filename)
        ltree = root.logicTree
        bsets = [c for c in ltree if c.tag.endswith('logicTreeBranchSet')]
        if not bsets:
            raise InvalidFile(
                '%s: no amplificationModel branchset found' % self.filename)
        if len(bsets) > 1:
            raise InvalidFile(
                '%s: only one <logicTreeBranchSet> is supported'
                % self.filename)
        [bset] = bsets
        utype = bset.attrib.get('uncertaintyType')
        if utype != 'amplificationModel':
            raise InvalidFile(
                '%s: only uncertaintyType="amplificationModel" is supported '
                'in an amplification logic tree, got %r'
                % (self.filename, utype))
        self.branchset_id = bset.attrib.get('branchSetID', 'bs_ampl')
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
                '%s: duplicate branchID(s) in amplification logic tree: %s'
                % (self.filename, dups))
        # Keeps the amp leg of the composite path a single BASE183 char
        if len(self.branches) > len(BASE183):
            raise InvalidFile(
                '%s: too many branches (%d > %d)'
                % (self.filename, len(self.branches), len(BASE183)))
        wsum = sum(w for _, _, w in self.branches)
        if abs(wsum - 1.) > 1e-5:
            raise InvalidFile(
                '%s: amplificationModel branch weights sum to %s, expected 1.0'
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
        return '<AmplificationLogicTreeParser %s, %d branches>' % (
            os.path.basename(self.filename), len(self.branches))


class AmplificationLogicTree(object):
    """
    Site amplification for one or more branches (single CSV or amp-LT)
    """
    def __init__(self, names, weights, dframes=None, amplifiers=None,
                 filenames=None, tree_filename='', branchset_id='bs_ampl',
                 rlz_ampl_ord=None):
        assert names, 'At least one branch is required'
        self.names = list(names)
        self.weights = numpy.asarray(weights, F32)
        # dframes and amplifiers are None after a HDF5 restore; readinput
        # rebuilds them from the per-branch CSVs on demand
        self.dframes = list(dframes) if dframes is not None else None
        self.amplifiers = tuple(amplifiers) if amplifiers is not None else None
        self.filenames = list(filenames) if filenames else list(self.names)
        self.filename = tree_filename
        self.branchset_id = branchset_id
        # rlz_ampl_ord[r] gives the branch index used by realization r;
        # None for the single-branch case
        self.rlz_ampl_ord = rlz_ampl_ord

    def __bool__(self):
        return True

    @property
    def xR(self):
        """
        :returns: number of amplification branches
        """
        return len(self.names)

    def get_num_paths(self):
        """
        :returns: the number of paths in the logic tree
        """
        return self.xR

    @property
    def amplevels(self):
        return self.amplifiers[0].amplevels

    def check(self, vs30, vs30_tolerance, gsims_by_trt):
        self.amplifiers[0].check(vs30, vs30_tolerance, gsims_by_trt)

    def amplify(self, ampl_code, hcurve):
        """
        :param ampl_code: 2-letter code for the amplification function
        :param hcurve: an array of shape (L*M, R) on rock levels
        :returns: amplified array of shape (A*M, R) on soil levels
        """
        if self.rlz_ampl_ord is None:
            return self.amplifiers[0].amplify(ampl_code, hcurve)
        _, R = hcurve.shape
        return numpy.hstack([
            self.amplifiers[self.rlz_ampl_ord[r]].amplify(
                ampl_code, hcurve[:, r:r+1])
            for r in range(R)])

    def get_realizations(self):
        """
        :returns: a list of :class:`Realization` objects, one per branch
        """
        return [Realization(value=name, weight=float(w), ordinal=i,
                            lt_path=(name,), samples=1)
                for i, (name, w) in enumerate(zip(self.names, self.weights))]

    def sample(self, n, seed, sampling_method='early_weights'):
        """
        Monte-Carlo sample n branches with probability = branch weight;
        returns :class:`Realization` objects (branches may repeat or be absent)
        """
        probs = random(n, seed, sampling_method)
        return sample(self.get_realizations(), probs, sampling_method)

    @property
    def shortener(self):
        """
        :returns: dict of branchID -> two-char abbreviation, matching the SSC
            and GSIM shortener format
        """
        return {name: BASE183[i] + '0' for i, name in enumerate(self.names)}

    def __toh5__(self):
        arr = numpy.array(
            list(zip(self.names, self.weights, self.filenames)), amp_lt_dt)
        return arr, dict(tree_filename=self.filename,
                         branchset_id=self.branchset_id)

    def __fromh5__(self, array, attrs):
        self.names = [decode(r['name']) for r in array]
        self.weights = numpy.array([r['weight'] for r in array], F32)
        self.filenames = [decode(r['filename']) for r in array]
        self.dframes = None
        self.amplifiers = None
        self.rlz_ampl_ord = None
        self.filename = attrs.get('tree_filename', '')
        self.branchset_id = attrs.get('branchset_id', 'bs_ampl')

    def __repr__(self):
        return '<AmplificationLogicTree xR=%d weights=%s>' % (
            self.xR, self.weights.tolist())


