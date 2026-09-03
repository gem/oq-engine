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

from openquake.baselib.general import BASE183
from openquake.hazardlib import InvalidFile, nrml


class AmplificationLogicTree(object):
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
        return '<AmplificationLogicTree %s, %d branches>' % (
            os.path.basename(self.filename), len(self.branches))


