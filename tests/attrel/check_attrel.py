#!/usr/bin/env python
import csv
import math
import sys

from nhe import const
from nhe.attrel.base import AttRelContext, AttenuationRelationship
from nhe.imt import PGA, PGV, SA


def check_attrel(attrel_cls, filename, max_discrep_percentage,
                 max_errors=0, verbose=False):
    reader = csv.reader(open(filename))
    attrel = attrel_cls()
    context_params = set(AttRelContext.__slots__)

    linenum = 1
    errors = 0
    discrepancies = []
    headers = [param_name.lower() for param_name in reader.next()]
    for values in reader:
        linenum += 1
        expected_results = {}
        context = AttRelContext()
        stddev_type = result_type = damping = component_type = None

        for param, value in zip(headers, values):
            if param == 'result_type':
                value = value.upper()
                if value.endswith('_STDDEV'):
                    # the row defines expected stddev results
                    result_type = 'STDDEV'
                    stddev_type = getattr(const.StdDev,
                                          value[:-len('_STDDEV')])
                    assert stddev_type != const.StdDev.NONE
                else:
                    # the row defines expected exponents of mean values
                    assert value == 'MEAN'
                    stddev_type = const.StdDev.NONE
                    result_type = 'MEAN'
            elif param == 'damping':
                damping = float(value)
            elif param == 'component_type':
                component_type = getattr(const.IMC, value)
            elif param in context_params:
                # value is context object attribute
                if param == 'site_vs30type':
                    value = getattr(const.VS30T, value)
                else:
                    value = float(value)
                setattr(context, param, value)
            else:
                # value is the expected result (of result_type type)
                value = float(value)
                if param == 'pga':
                    imt = PGA()
                elif param == 'pgv':
                    imt = PGV()
                else:
                    period = float(param)
                    assert damping is not None
                    imt = SA(period, damping)

                expected_results[imt] = value

        assert component_type is not None and result_type is not None

        for imt, expected_result in expected_results.items():
            mean, [stddev] = attrel.get_mean_and_stddevs(
                context, imt, [stddev_type], component_type
            )
            if result_type == 'MEAN':
                result = math.exp(mean)
            else:
                result = stddev
            discrep_percentage = abs(
                result / float(expected_result) * 100 - 100
            )
            discrepancies.append(discrep_percentage)
            if discrep_percentage > max_discrep_percentage:
                # check failed
                errors += 1
                if verbose:
                    msg = 'file %r line %r imt %r: expected %s %f != %f ' \
                          '(delta %.4f%%)' % (
                              filename, linenum, imt, result_type.lower(),
                              expected_result, result, discrep_percentage
                          )
                    print >> sys.stderr, msg
                if max_errors is not None and errors > max_errors:
                    break

        if max_errors is not None and errors > max_errors:
            break

    max_discrep = max(discrepancies)
    total_checks = len(discrepancies)
    successes = total_checks - errors
    avg_discrep = sum(discrepancies) / float(total_checks)
    success_rate = successes / float(total_checks) * 100
    stddev = math.sqrt(1.0 / total_checks * sum((avg_discrep - discrep) ** 2
                                                for discrep in discrepancies))
    stats = '''\
total of %d checks done, %d of them were successful and %d failed.
success rate = %.1f%%
average discrepancy = %.4f%%
maximum discrepancy = %.4f%%
standard deviation = %.4f%%'''
    successes = total_checks - errors
    stats %= (total_checks, successes, errors, success_rate,
              avg_discrep, max_discrep, stddev)
    return errors, stats


if __name__ == '__main__':
    import argparse

    def attrel_by_import_path(import_path):
        if not '.' in import_path:
            raise argparse.ArgumentTypeError(
                '%r is not well-formed import path' % import_path
            )
        module_name, class_name = import_path.rsplit('.', 1)
        try:
            module = __import__(module_name, fromlist=[class_name])
        except ImportError:
            raise argparse.ArgumentTypeError(
                'can not import module %r, make sure ' \
                'it is in your $PYTHONPATH' % module_name
            )
        if not hasattr(module, class_name):
            raise argparse.ArgumentTypeError(
                "module %r doesn't export name %r" % (module_name, class_name)
            )
        attrel_class = getattr(module, class_name)
        if not isinstance(attrel_class, type) \
                or not issubclass(attrel_class, AttenuationRelationship):
            raise argparse.ArgumentTypeError(
                "%r is not subclass of " \
                "nhe.attrel.base.AttenuationRelationship" % import_path
            )
        return attrel_class

    parser = argparse.ArgumentParser(
        description='Check GMPE/IPE class versus data file in CSV format ' \
                    'by calculating standard deviation or mean value and ' \
                    'comparing the result to the expected value.'
    )
    parser.add_argument('attrel', type=attrel_by_import_path,
                        help='an import path of the attenuation relationship '\
                             'class in a form "package.module.ClassName".')
    parser.add_argument('datafile', type=argparse.FileType('r'),
                        help='test data file in a csv format')
    parser.add_argument('-p', '--max-discrepancy', type=float, metavar='prcnt',
                        help='the maximum discrepancy allowed for result ' \
                             'value to be considered matching, expressed ' \
                             'in percentage points. default value is 0.5.',
                        nargs='?', default=0.5, dest='max_discrep_percentage')
    parser.add_argument('-e', '--max-errors', type=int, nargs='?',
                        help='maximum number of tests to fail before ' \
                             'stopping execution. by default all tests ' \
                             'are executed.',
                        default=None, metavar='num')
    verb_group = parser.add_mutually_exclusive_group()
    verb_group.add_argument('-v', '--verbose', action='store_true',
                            help='print information about each error ' \
                                 'immediately.')
    verb_group.add_argument('-q', '--quiet', action='store_true',
                            help="don't print stats at the end. use exit " \
                                 "code to determine if test succeeded.")

    args = parser.parse_args()

    errors, stats = check_attrel(
        attrel_cls=args.attrel, filename=args.datafile.name,
        max_discrep_percentage=args.max_discrep_percentage,
        max_errors=args.max_errors, verbose=args.verbose
    )
    if not args.quiet:
        print >> sys.stderr, stats
    if errors:
        exit(127)
