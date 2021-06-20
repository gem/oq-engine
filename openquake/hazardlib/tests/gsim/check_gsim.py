#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
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
Check GSIM class versus data file in CSV format by calculating standard
deviation and/or mean value and comparing the result to the expected value.
"""
import csv
import math
import sys
import time
import numpy

from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import GroundShakingIntensityModel
from openquake.hazardlib.contexts import (
    RuptureContext, DistancesContext, ContextMaker)
from openquake.hazardlib.imt import registry
from openquake.hazardlib.imt import from_string


def set_read_only(ctx):
    for slot in vars(ctx):
        arr = getattr(ctx, slot)
        if isinstance(arr, numpy.ndarray):
            arr.flags.writeable = False


def check_gsim(gsim, datafile, max_discrep_percentage, debug=False):
    """
    Test GSIM against the data file and return test result.

    :param gsim:
        An instance of :class:`~openquake.hazardlib.gsim.base.GMPE` to test.
    :param datafile:
        A file object containing test data in csv format.
    :param max_discrep_percentage:
        The maximum discrepancy in percentage points. The check fails
        if expected value diverges from actual by more than that.
    :param debug:
        If ``True`` the execution will stop immediately if there is an error
        and a message pointing to a line with a test that failed will show up.
        If ``False`` the GSIM is executed in a vectorized way (if possible)
        and all the tests are executed even if there are errors.

    :returns:
        A tuple of two elements: a number of errors and a string representing
        statistics about the test run.
    """
    cmaker = ContextMaker('*', [gsim])
    errors = 0
    linenum = 1
    discrepancies = []
    started = time.time()
    for testcase in _parse_csv(
            datafile, debug, gsim.REQUIRES_SITES_PARAMETERS):
        linenum += 1
        ctx, stddev_types, expected_results, result_type = testcase
        set_read_only(ctx)
        for imt, expected_result in expected_results.items():
            mean, stddevs = gsim.get_mean_and_stddevs(ctx, ctx, ctx,
                                                      imt, stddev_types)
            if result_type == 'MEAN':
                if str(imt) == 'MMI':
                    # For IPEs it is the values, not the logarithms returned
                    result = mean
                else:
                    result = numpy.exp(mean)
            else:
                [result] = stddevs

            discrep_percent = numpy.abs(result / expected_result * 100 - 100)
            discrepancies.extend(discrep_percent)
            errors += (discrep_percent > max_discrep_percentage).sum()

            if errors and debug:
                msg = 'file %r line %r imt %r: expected %s %f != %f ' \
                      '(delta %.4f%%)' % (
                          datafile.name, linenum, imt, result_type.lower(),
                          expected_result[0], result[0], discrep_percent[0])
                print(msg, file=sys.stderr)
                break

        if debug and errors:
            break
    return (errors,
            _format_stats(time.time() - started, discrepancies, errors))


def _format_stats(time_spent, discrepancies, errors):
    """
    Format a GMPE test statistics.

    :param time_spent:
        The amount of time spent doing checks, in seconds
    :param discrepancies:
        A list of discrepancy percentage values, one for each check.
    :param errors:
        Number of tests that failed.
    :returns:
        A string with human-readable statistics.
    """
    max_discrep = max(discrepancies)
    total_checks = len(discrepancies)
    successes = total_checks - errors
    avg_discrep = sum(discrepancies) / float(total_checks)
    success_rate = successes / float(total_checks) * 100
    stddev = math.sqrt(1.0 / total_checks * sum((avg_discrep - discrep) ** 2
                                                for discrep in discrepancies))
    # NB: on a windows virtual machine the clock can be buggy and
    # the time spent can be zero: Daniele has seen that
    checks_per_sec = (total_checks / time_spent) if time_spent else '?'
    stats = '''\
total of %d checks done, %d were successful and %d failed.
%.1f seconds spent, avg rate is %s checks per seconds.
success rate = %.1f%%
average discrepancy = %.4f%%
maximum discrepancy = %.4f%%
standard deviation = %.4f%%'''
    successes = total_checks - errors
    stats %= (total_checks, successes, errors,
              time_spent, checks_per_sec,
              success_rate,
              avg_discrep,
              max_discrep,
              stddev)
    return stats


def _parse_csv(datafile, debug, req_site_params):
    """
    Parse a data file in csv format and generate everything needed to exercise
    GSIM and check the result.

    :param datafile:
        File-like object to read csv from.
    :param debug:
        If ``False``, parser will try to combine several subsequent rows from
        the data file into one vectorized call.
    :returns:
        A generator of tuples of :func:`_parse_csv_line` result format.
    """
    reader = iter(csv.reader(datafile))
    headers = [param_name.lower() for param_name in next(reader)]
    ctx, stddev_types, expected_results, result_type \
        = _parse_csv_line(headers, next(reader), req_site_params)
    slots = set(vars(ctx))
    attrs = list(req_site_params) + [s for s in DistancesContext._slots_
                                     if s in slots]
    for line in reader:
        (ctx2, stddev_types2, expected_results2, result_type2) \
            = _parse_csv_line(headers, line, req_site_params)
        rp_equal = [
            numpy.all(getattr(ctx, slot, None) == getattr(ctx2, slot, None))
            for slot in RuptureContext._slots_]
        all(rp_equal)
        if not debug and stddev_types2 == stddev_types \
           and result_type2 == result_type and all(rp_equal):
            for slot in attrs:
                setattr(ctx, slot, numpy.hstack((getattr(ctx, slot),
                                                 getattr(ctx2, slot))))
            for imt in expected_results:
                expected_results[imt] = numpy.hstack((expected_results[imt],
                                                      expected_results2[imt]))
        else:
            yield ctx, stddev_types, expected_results, result_type
            (ctx, stddev_types, expected_results,
             result_type) = (ctx2, stddev_types2,
                             expected_results2, result_type2)
    yield ctx, stddev_types, expected_results, result_type


def _parse_csv_line(headers, values, req_site_params):
    """
    Parse a single line from data file.

    :param headers:
        A list of header names, the strings from the first line of csv file.
    :param values:
        A list of values of a single row to parse.
    :returns:
        A tuple of the following values (in specified order):
        ctx
            An instance of
            :class:`openquake.hazardlib.gsim.base.RuptureContext`.
        stddev_types
            An empty list, if the ``result_type`` column says "MEAN"
            for that row, otherwise it is a list with one item --
            a requested standard deviation type.
        expected_results
            A dictionary mapping IMT-objects to one-element arrays of expected
            result values. Those results represent either standard deviation
            or mean value of corresponding IMT depending on ``result_type``.
        result_type
            A string literal, one of ``'STDDEV'`` or ``'MEAN'``. Value
            is taken from column ``result_type``.
    """
    ctx = RuptureContext()
    expected_results = {}
    stddev_types = result_type = damping = None

    for param, value in zip(headers, values):

        if param == 'result_type':
            value = value.upper()
            if value.endswith('_STDDEV'):
                # the row defines expected stddev results
                result_type = 'STDDEV'
                stddev_types = [getattr(const.StdDev,
                                        value[:-len('_STDDEV')])]
            else:
                # the row defines expected exponents of mean values
                assert value == 'MEAN'
                stddev_types = []
                result_type = 'MEAN'
        elif param == 'damping':
            damping = float(value)
        elif param.startswith('site_'):
            # value is sites context object attribute
            if param == 'site_vs30measured' or param == 'site_backarc':
                value = float(value) != 0
            elif param in ('site_siteclass', 'site_ec8', 'site_ec8_p18',
                           'site_geology'):
                value = numpy.string_(value)
            else:
                value = float(value)
            # site_lons, site_lats, site_depths -> lon, lat, depth
            if param.endswith(('lons', 'lats', 'depths')):
                attr = param[len('site_'):-1]
            else:  # vs30s etc
                attr = param[len('site_'):]
            setattr(ctx, attr, numpy.array([value]))
        elif param.startswith('dist_'):
            # value is a distance measure
            value = float(value)
            setattr(ctx, param[len('dist_'):], numpy.array([value]))
        elif param.startswith('rup_'):
            # value is a rupture context attribute
            try:
                value = float(value)
            except ValueError:
                if value != 'undefined':
                    raise
            setattr(ctx, param[len('rup_'):], value)
        elif param == 'component_type':
            pass
        else:
            # value is the expected result (of result_type type)
            value = float(value)

            if param == 'arias':  # ugly legacy corner case
                param = 'ia'
            if param == 'avgsa':
                imt = from_string('AvgSA')
            else:
                try:    # The title of the column should be IMT(args)
                    imt = from_string(param.upper())
                except KeyError:  # Then it is just a period for SA
                    imt = registry['SA'](float(param), damping)

            expected_results[imt] = numpy.array([value])

    assert result_type is not None
    return ctx, stddev_types, expected_results, result_type


if __name__ == '__main__':
    import argparse

    def gsim_by_import_path(import_path):
        if '.' not in import_path:
            raise argparse.ArgumentTypeError(
                '%r is not well-formed import path' % import_path)
        module_name, class_name = import_path.rsplit('.', 1)
        try:
            module = __import__(module_name, fromlist=[class_name])
        except ImportError:
            raise argparse.ArgumentTypeError(
                'can not import module %r, make sure '
                'it is in your $PYTHONPATH' % module_name)
        if not hasattr(module, class_name):
            raise argparse.ArgumentTypeError(
                "module %r doesn't export name %r" % (module_name, class_name))
        gsim_class = getattr(module, class_name)
        if not isinstance(gsim_class, type) \
                or not issubclass(gsim_class, GroundShakingIntensityModel):
            raise argparse.ArgumentTypeError(
                "%r is not subclass of "
                "openquake.hazardlib.gsim.base.GroundShakingIntensityModel"
                % import_path)
        return gsim_class

    parser = argparse.ArgumentParser(description=' '.join(__doc__.split()))
    parser.add_argument('gsim', type=gsim_by_import_path,
                        help='an import path of the ground shaking '
                        'intensity model class in a form '
                        '"package.module.ClassName".')
    parser.add_argument('datafile', type=argparse.FileType('r'),
                        help='test data file in a csv format. use "-" for '
                             'reading from standard input')
    parser.add_argument('-p', '--max-discrepancy', type=float, metavar='prcnt',
                        help='the maximum discrepancy allowed for result '
                        'value to be considered matching, expressed '
                             'in percentage points. default value is 0.5.',
                        nargs='?', default=0.5, dest='max_discrep_percentage')
    dbg_group = parser.add_mutually_exclusive_group()
    dbg_group.add_argument('-d', '--debug', required=False,
                           action='store_true',
                           help='run unvectorized, stop on first error '
                                'and print information about line containing '
                                'failing test')
    dbg_group.add_argument('-q', '--quiet', action='store_true',
                           help="don't print stats at the end. use exit "
                           "code to determine if test succeeded.")

    args = parser.parse_args()
    errors, stats, _, _, _, = check_gsim(
        gsim=args.gsim(), datafile=args.datafile,
        max_discrep_percentage=args.max_discrep_percentage,
        debug=args.debug)
    if not args.quiet:
        print(stats, file=sys.stderr)
    if errors:
        exit(127)
