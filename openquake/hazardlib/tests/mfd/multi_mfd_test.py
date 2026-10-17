# The Hazard Library
# Copyright (C) 2026 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from openquake.hazardlib.mfd.multi_mfd import MultiMFD


class MultiMFDModifyTestCase(unittest.TestCase):

    def _mfd(self):
        return MultiMFD('truncGutenbergRichterMFD', size=2,
                        min_mag=[4.0], max_mag=[6.0], bin_width=[0.1],
                        a_val=[1.0, 2.0], b_val=[1.0])

    def test_single_modification(self):
        mfd = self._mfd()
        mfd.modify('increment_max_mag', dict(value=0.2))
        mfds = list(mfd)
        self.assertAlmostEqual(mfds[0].max_mag, 6.2)
        self.assertAlmostEqual(mfds[1].max_mag, 6.2)

    def test_stacked_modifications(self):
        # maxMag and b-value uncertainties act on the same MFD: both
        # must be applied, not only the last one
        mfd = self._mfd()
        mfd.modify('increment_max_mag', dict(value=0.2))
        mfd.modify('increment_b', dict(value=0.05))
        for single in mfd:
            self.assertAlmostEqual(single.max_mag, 6.2)
            self.assertAlmostEqual(single.b_val, 1.05)

    def test_slice_has_no_modification(self):
        # slicing is done before the uncertainties are applied, so the
        # slice must still produce the same MFDs as the full object
        mfd = self._mfd()
        sliced = mfd[slice(1, 2)]
        self.assertEqual(len(sliced), 1)
        self.assertEqual(list(sliced.kwargs), list(mfd.kwargs))
        self.assertEqual(sliced.modification, [])

    def test_slice_keeps_modifications(self):
        # splitting a source after the uncertainties are applied must
        # not lose them: the slice must yield the modified MFDs
        mfd = self._mfd()
        mfd.modify('increment_max_mag', dict(value=0.2))
        sliced = mfd[slice(1, 2)]
        self.assertEqual(len(sliced.modification), 1)
        for single in sliced:
            self.assertAlmostEqual(single.max_mag, 6.2)


if __name__ == '__main__':
    unittest.main()
