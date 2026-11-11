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
from openquake.hazardlib.lt import Branch, BranchSet, ExtraLogicTree
from openquake.hazardlib.logictree import check_branchset_weights

UTYPE = 'amplificationModel'


class AmplificationLogicTree(ExtraLogicTree):
    """
    Site amplification for one or more branches: a logic tree with a
    single branchset of type amplificationModel, whose branches are the
    amplification CSV files (a single branch for a plain CSV file)
    """
    def __init__(self, names, weights, dframes=None, amplifiers=None,
                 filenames=None, tree_filename='', branchset_id='bs_ampl',
                 rlz_ampl_ord=None):
        assert names, 'At least one branch is required'
        filenames = list(filenames) if filenames else list(names)
        bset = BranchSet(UTYPE)
        bset.id = branchset_id
        bset.branches = [
            Branch(name, fname, float(weight), branchset_id)
            for name, fname, weight in zip(names, filenames, weights)]
        self.branchsets = [bset]
        self.bsetdict = {branchset_id: {'uncertaintyType': UTYPE}}
        self.filename = tree_filename
        self.set_num_paths()
        # dframes and amplifiers are None after a HDF5 restore; readinput
        # rebuilds them from the per-branch CSVs on demand
        self.dframes = list(dframes) if dframes is not None else None
        self.amplifiers = tuple(amplifiers) if amplifiers is not None else None
        # rlz_ampl_ord[r] gives the branch index used by realization r;
        # None for the single-branch case
        self.rlz_ampl_ord = rlz_ampl_ord

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
                    child.attrib.get('uncertaintyType') == UTYPE):
                return True
        return False

    @classmethod
    def from_xml(cls, filename):
        """
        :param filename: an XML file with a single amplificationModel
            branchset, whose branches refer to CSV files relative to it
        :returns: an AmplificationLogicTree without amplifiers
        """
        root = nrml.read(filename)
        if not hasattr(root, 'logicTree'):
            raise InvalidFile('%s: missing <logicTree> element' % filename)
        bsets = [c for c in root.logicTree
                 if c.tag.endswith('logicTreeBranchSet')]
        if not bsets:
            raise InvalidFile(
                '%s: no amplificationModel branchset found' % filename)
        if len(bsets) > 1:
            raise InvalidFile(
                '%s: only one <logicTreeBranchSet> is supported' % filename)
        [bset] = bsets
        utype = bset.attrib.get('uncertaintyType')
        if utype != UTYPE:
            raise InvalidFile(
                '%s: only uncertaintyType="amplificationModel" is supported '
                'in an amplification logic tree, got %r' % (filename, utype))
        bsid = bset.attrib.get('branchSetID', 'bs_ampl')
        dirname = os.path.dirname(filename)
        names, fnames, weights = [], [], []
        for br in bset:
            names.append(br.attrib.get('branchID', ''))
            fnames.append(os.path.normpath(os.path.join(
                dirname, br.uncertaintyModel.text.strip())))
            weights.append(float(br.uncertaintyWeight.text))
        dups = sorted({name for name in names if names.count(name) > 1})
        if dups:
            raise InvalidFile(
                '%s: duplicate branchID(s) in amplification logic tree: %s'
                % (filename, dups))
        # keeps the amp leg of the composite path a single BASE183 char
        if len(names) > len(BASE183):
            raise InvalidFile('%s: too many branches (%d > %d)' % (
                filename, len(names), len(BASE183)))
        check_branchset_weights(bset, filename, bsid, weights)
        return cls(names, weights, filenames=fnames, tree_filename=filename,
                   branchset_id=bsid)

    @property
    def branchset_id(self):
        return self.root_branchset.id

    @property
    def names(self):
        return [br.branch_id for br in self.root_branchset.branches]

    @property
    def weights(self):
        return numpy.array([br.weight for br in self.root_branchset.branches])

    @property
    def filenames(self):
        return [br.value for br in self.root_branchset.branches]

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

    def __fromh5__(self, array, attrs):
        super().__fromh5__(array, attrs)
        # the amplifiers are rebuilt from the CSV files by readinput
        self.dframes = self.amplifiers = self.rlz_ampl_ord = None

    def __repr__(self):
        return '<AmplificationLogicTree %d branches weights=%s>' % (
            self.get_num_paths(), self.weights.tolist())
