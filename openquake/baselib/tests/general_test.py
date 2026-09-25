# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Test related to code in openquake/utils/general.py
"""
import unittest.mock as mock
import unittest
import numpy
from operator import attrgetter
from collections import namedtuple
from openquake.baselib.general import (
    block_splitter, split_in_blocks, assert_close, rmsdiff,
    deprecated, DeprecationWarning, cached_property,
    compress, decompress, random_choice, get_duplicates,
    check_dependencies, get_bins, groupby_grid)


class BlockSplitterTestCase(unittest.TestCase):
    """Tests for :func:`openquake.baselib.general.block_splitter`."""

    DATA = range(10)

    def test_block_splitter(self):
        expected = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [9],
        ]
        actual = [x for x in block_splitter(self.DATA, 3)]
        self.assertEqual(expected, actual)

    def test_block_splitter_block_size_eq_data_len(self):
        expected = [self.DATA]
        actual = [x for x in block_splitter(self.DATA, 10)]
        self.assertEqual(expected, actual)

    def test_block_splitter_block_size_gt_data_len(self):
        expected = [self.DATA]
        actual = [x for x in block_splitter(self.DATA, 11)]
        self.assertEqual(expected, actual)

    def test_block_splitter_zero_block_size(self):
        gen = block_splitter(self.DATA, 0)
        with self.assertRaises(ValueError):
            next(gen)

    def test_block_splitter_block_size_lt_zero(self):
        gen = block_splitter(self.DATA, -1)
        with self.assertRaises(ValueError):
            next(gen)

    def test_block_splitter_with_generator(self):
        # Test the block with a data set of unknown length
        # (such as a generator)
        data = range(10)
        expected = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [9],
        ]
        actual = [x for x in block_splitter(data, 3)]
        self.assertEqual(expected, actual)

    def test_block_splitter_with_iter(self):
        # Test the block with a data set of unknown length
        data = range(10)
        expected = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [9],
        ]
        actual = [x for x in block_splitter(data, 3)]
        self.assertEqual(expected, actual)

    def test_split_with_weight(self):
        weights = dict([('a', 11), ('b', 10), ('c', 100), ('d', 15), ('e', 20),
                        ('f', 5), ('g', 30), ('h', 17), ('i', 25)])
        blocks = list(block_splitter('abcdefghi', 50, weights.get))
        self.assertEqual(repr(blocks), "[<WeightedSequence ['a', 'b'], weight=21>, <WeightedSequence ['c'], weight=100>, <WeightedSequence ['d', 'e', 'f'], weight=40>, <WeightedSequence ['g', 'h'], weight=47>, <WeightedSequence ['i'], weight=25>]")

    def test_split_in_blocks(self):
        weights = dict([('a', 11), ('b', 10), ('c', 100), ('d', 15), ('e', 20),
                        ('f', 5), ('g', 30), ('h', 17), ('i', 25)])
        blocks = list(split_in_blocks('abcdefghi', 1, weights.get))
        self.assertEqual(len(blocks), 1)
        blocks = list(split_in_blocks('abcdefghi', 2, weights.get))
        self.assertEqual(len(blocks), 3)
        self.assertEqual(repr(blocks),
                         "[['f', 'b', 'a', 'd', 'h', 'e', 'i'], ['g'], ['c']]")

    def test_split_with_kind(self):
        Source = namedtuple('Source', 'typology, weight')
        s1 = Source('point', 1)
        s2 = Source('point', 1)
        s3 = Source('area', 2)
        s4 = Source('area', 4)
        s5 = Source('area', 4)
        blocks = list(
            block_splitter([s1, s2, s3, s4, s5], max_weight=6,
                           weight=attrgetter('weight'),
                           key=attrgetter('typology')))
        self.assertEqual(list(map(len, blocks)), [2, 2, 1])
        self.assertEqual([b.weight for b in blocks], [2, 6, 4])

        blocks = list(
            split_in_blocks([s1, s2, s3, s4, s5], hint=6,
                            weight=attrgetter('weight'),
                            key=attrgetter('typology')))
        self.assertEqual(list(map(len, blocks)), [1, 1, 1, 2])


class AssertCloseTestCase(unittest.TestCase):
    def test_different(self):
        a = [1, 2]
        b = [1, 2, 3]
        with self.assertRaises(AssertionError):  # different lenghts
            assert_close(a, b)

        with self.assertRaises(AssertionError):  # different floats
            assert_close([1, 2, 3.1], b)

        with self.assertRaises(AssertionError):  # None and float
            assert_close([1, 2, None], b)

        with self.assertRaises(AssertionError):  # nested dicts
            gmf1 = {'a': {'PGA': [0.1, 0.2], 'SA(0.1)': [0.3, 0.4]}}
            gmf2 = {'a': {'PGA': [0.1, 0.2], 'SA(0.1)': [0.3, 0.41]}}
            assert_close(gmf1, gmf2)

        class C(object):
            pass

        c1 = C()
        c2 = C()
        c2.a = 1
        with self.assertRaises(AssertionError):  # different attributes
            assert_close(c1, c2)


class DeprecatedTestCase(unittest.TestCase):
    def test(self):
        @deprecated(msg='Use dummy_new instead.')
        def dummy():
            pass

        # check that a DeprecationWarning is printed
        with mock.patch('warnings.warn') as warn:
            dummy()
        warning_msg, warning_type = warn.call_args[0]
        self.assertIs(warning_type, DeprecationWarning)
        self.assertIn(
            'general_test.dummy has been deprecated. Use dummy_new instead.',
            warning_msg)

        # check that at the second call the warning is not printed
        with mock.patch('warnings.warn') as warn:
            dummy()
        self.assertIsNone(warn.call_args)


class CachedPropertyTestCase(unittest.TestCase):

    @cached_property
    def one(self):
        self.ncalls += 1
        return 1

    def test(self):
        self.ncalls = 0
        assert 'one' not in vars(self)
        self.assertEqual(self.one, 1)
        assert 'one' in vars(self)
        self.assertEqual(self.__dict__['one'], 1)
        self.assertEqual(self.ncalls, 1)
        self.__dict__['one'] = 2
        self.assertEqual(self.one, 2)
        self.assertEqual(self.ncalls, 1)


def double(calc_id, val):
    print((calc_id, val * 2))


class CompressTestCase(unittest.TestCase):
    def test(self):
        a = dict(a=numpy.array([9999.]))
        self.assertEqual(a, decompress(compress(a)))


class RmsDiffTestCase(unittest.TestCase):
    def test(self):
        a = numpy.array([[.1, .2, .3],
                         [1.1, 1.2, 1.3]])
        b = numpy.array([[.11, .21, .31],
                         [1.1, 1.21, 1.31]])
        rms, index = rmsdiff(a, b)
        print(rms, index)


class RandomChoiceTestCase(unittest.TestCase):
    def test_advance(self):
        chars = numpy.array(list('ABCDEFGHIJK'))
        ch1 = random_choice(chars, 1_000_000, 0)
        ch2 = random_choice(chars, 2_000_000, 1_000_000)
        ch3 = random_choice(chars, 3_000_000, 3_000_000)

        ch_tot = numpy.concatenate([ch1, ch2, ch3])
        ch6 = random_choice(chars, 6_000_000, 0)
        numpy.testing.assert_equal(ch_tot, ch6)


def test_get_duplicates():
    dtlist = [('lon', float), ('lat', float), (('id', numpy.bytes_, 3))]
    lst = [(2.1, 1.0, 's01'), (2.2, 1.0, 's02'), (2.1, 1.0, 's03')]
    arr = numpy.array(lst, dtlist)
    dic = get_duplicates(arr, 'lon', 'lat')
    assert dic == {(2.1, 1.0): 2}, dic


def test_check_dependencies():
    check_dependencies()


class GetBinsTestCase(unittest.TestCase):
    def test_regular(self):
        values = numpy.arange(10)
        idx, bins = get_bins(values, 3)
        self.assertEqual([int(i) for i in idx],
                         [0, 0, 0, 1, 1, 1, 2, 2, 2, 2])
        numpy.testing.assert_allclose(bins, [0., 3., 6.])

    def test_max_goes_in_last_bin(self):
        values = numpy.array([0., 0.9, 1.8])
        idx, bins = get_bins(values, 2)
        self.assertEqual([int(i) for i in idx], [0, 1, 1])
        numpy.testing.assert_allclose(bins, [0., 0.9])

    def test_degenerate(self):
        values = numpy.array([3., 3., 3.])
        idx, bins = get_bins(values, 5)
        self.assertEqual([int(i) for i in idx], [0, 0, 0])
        numpy.testing.assert_allclose(bins, [3.] * 5)


class GroupbyGridTestCase(unittest.TestCase):
    def test_two_cells(self):
        xs = numpy.array([0., 0.5, 0.9, 1.8])
        ys = numpy.array([0., 0.1, 0.2, 0.3])
        dic = groupby_grid(xs, ys, 1., 1.)
        keys = numpy.array(list(dic))
        numpy.testing.assert_allclose(keys, [[0.25, 0.05],
                                             [1.35, 0.25]])
        self.assertEqual([list(v) for v in dic.values()],
                         [[0, 1], [2, 3]])

    def test_first_occurrence_order(self):
        # point 0 is in the last cell and point 1 in the first
        # one, the dict must keep the first-occurrence order and
        # not the sorted order of the cells
        xs = numpy.array([1.8, 0.])
        ys = numpy.array([0.3, 0.])
        dic = groupby_grid(xs, ys, 1., 1.)
        keys = numpy.array(list(dic))
        numpy.testing.assert_allclose(keys, [[1.8, 0.3], [0., 0.]])
        self.assertEqual([list(v) for v in dic.values()], [[0], [1]])

    def test_degenerate_row(self):
        # all the points on the same row: used to raise an
        # assertion error, now the flat axis has a single bin
        xs = numpy.array([0., 2.])
        ys = numpy.zeros(2)
        dic = groupby_grid(xs, ys, 1., 1.)
        self.assertEqual(len(dic), 2)
        self.assertEqual([list(v) for v in dic.values()], [[0], [1]])

    def test_matches_reference(self):
        # the vectorized grouping must give the same cells as the
        # original implementation with numpy.arange bins
        rng = numpy.random.default_rng(7)
        for _ in range(20):
            N = int(rng.integers(2, 300))
            xs = rng.uniform(0, 20, N)
            ys = rng.uniform(30, 40, N)
            dic = groupby_grid(xs, ys, 1., 1.)

            def old_bins(values, nbins):
                vmin, vmax = values.min(), values.max()
                if vmin == vmax:
                    edges = [vmin] * nbins
                else:
                    edges = numpy.arange(vmin, vmax,
                                         (vmax - vmin) / nbins)
                return numpy.searchsorted(edges, values, side='right')

            nx = max(1, int(numpy.ceil(xs.max() - xs.min())))
            ny = max(1, int(numpy.ceil(ys.max() - ys.min())))
            xb = old_bins(xs, nx)
            yb = old_bins(ys, ny)
            ref = {}
            for k in range(N):
                ref.setdefault((int(xb[k]), int(yb[k])), []).append(k)
            got = {tuple(int(k) for k in v) for v in dic.values()}
            exp = {tuple(v) for v in ref.values()}
            self.assertEqual(got, exp)
