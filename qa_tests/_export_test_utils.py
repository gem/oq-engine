# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""Helpers for test export CLI interaction."""


def check_list_calcs(testcase, cli_output, expected_calc_id):
    """Helper function for testing CLI output of
    `bin/openquake --list-calculations`.

    :param testcase:
        :class:`unittest.TestCase` instance.
    :param cli_output:
        List of strings as prepared by
        :function:`tests.utils.helpers.prepare_cli_output`.
    """
    for line in cli_output:
        # We get back:
        # calc_id <tab> status <tag> description
        # description is optional so we cannot always assume it will be
        # present.
        calc_id, status = line.split('\t')[:2]
        if int(calc_id) == expected_calc_id:
            testcase.assertEqual('succeeded', status)
            break
    else:
        # We didn't find the calculation we just ran in the
        # --list-calculations output.
        testcase.fail('`openquake --list-calculations` did not print the'
                      ' expected calculation with id %s' % expected_calc_id)


def check_list_outputs(testcase, cli_output, expected_output_id,
                       expected_output_type):
    """Helper function for testing CLI output of
    `bin/openquake --list-outputs CALC_ID`.

    :param testcase:
        :class:`unittest.TestCase` instance.
    :param cli_output:
        List of strings as prepared by
        :function:`tests.utils.helpers.prepare_cli_output`.
    """
    for line in cli_output:
        output_id, output_type = line.split('\t')
        if int(output_id) == expected_output_id:
            testcase.assertEqual(expected_output_type, output_type)
            break
    else:
        # We didn't find the output we expected with --list-outputs.
        testcase.fail('`openquake --list-outputs` CALCULATION_ID did not'
                      ' print the expected output with id %s' % output_id)
