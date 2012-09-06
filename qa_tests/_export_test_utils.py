# Copyright (c) 2010-2012, GEM Foundation.
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


"""Helpers for test export CLI interaction."""


def check_list_calcs(testcase, cli_output, expected_calc_id):
    """Helper function for testing CLI output of
    `bin/oqscript.py --list-calculations`.

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
    `bin/oqscript.py --list-outputs CALC_ID`.

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
