#!/bin/bash
#
# bash_test.sh  Copyright (C) 2016-2018 GEM Foundation
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

# DESCRIPTION
#
# This script get list of scripts inside its basedir and
# run all (or one) of them, for each print exit status and
# run time and building optionally a cumulative xunit report.
#

# set -x
declare -a available_tests
NL='
'
tests_number=0
tests_errors=0
tests_failures=0
tests_skip=0
tests_results="" # content for tests items
some_test=0  # to check if some test is runned
xunit_output() {
    echo "<testsuite name=\"gem-suite\" tests=\"${tests_number}\" errors=\"${tests_errors}\" failures=\"${tests_failures}\" skip=\"${tests_skip}\">$tests_results"
    echo "</testsuite>"
}

xunit_ok() {
    local test_name="$1" test_time="$2" test_sysout="$3" test_sysout_s=""
    tests_number=$((tests_number + 1))
    if [ "$test_sysout" ]; then
        test_sysout_s="<system-out><![CDATA[${test_sysout}]]></system-out>"
    fi
    tests_results="$tests_results${NL}$(echo "  <testcase classname=\"openquake.risklib.tests.bash\" name=\"${test_name}\" time=\"${test_time}\">${test_sysout_s}</testcase>")"
}

xunit_failure() {
    tests_number=$((tests_number + 1))
    local test_name="$1" test_time="$2" failure_type="$3"
    local failure_mesg="$4" failure_cont="$5" system_err="$6"

    tests_failures=$((tests_failures + 1))
    tests_results="$tests_results${NL}$(echo "  <testcase classname=\"openquake.risklib.tests.bash\" name=\"${test_name}\" time=\"${test_time}\">
<failure type=\"${failure_type}\" message=\"${failure_mesg}\">${failure_cont}</failure>
<system-err>${system_err}</system-err>
</testcase>")"
}

console_begin () {
    local name="$1"

    echo "Test ${name} ... " | tr -d '\n'
}

console_end () {
    local result="$1" t_delta="$2"

    if [ $result -eq 0 ]; then
        echo "ok (${t_delta}s)."
    else
        echo "failed (${t_delta}s)."
    fi
}

usage () {
    cat <<EOF
USAGE:

# set PYTHONPATH properly
# cd git repository base directory
./openquake/risklib/tests/bin/bash_tests.sh <all|<name of the test>> [<xunit_fname>]
./openquake/risklib/tests/bin/bash_tests.sh <-h|--help>

EOF

    if [ ${#available_tests[@]} -gt 0 ]; then
        cat <<EOF
AVAILABLE TESTS:
  ${available_tests[@]}

EOF
    fi

    exit $1
}
whattest="$1"
outfile="$2"

if [ "$0" != "./openquake/risklib/tests/bin/bash_tests.sh" ]; then
    usage 1
fi

IFS='
'
for tst in $(ls $(dirname "$0") | grep -v "^$(basename "$0\$")"); do
    available_tests+=($(basename "$tst" .sh))
done

if [ $# -lt 1 -o "$1" = "-h" -o "$1" = "--help" ]; then
    usage 1
fi

for tst in ${available_tests[@]}; do
    if [ "$whattest" = "$tst" -o "$whattest" = "all" ]; then
        console_begin "$tst"
        t_pre="$(date +%s%3N)"
        # test_dump="$($(dirname "$0")/${tst}.sh)"
        test_dump="$($(dirname "$0")/${tst}.sh 2>&1)"
        ret=$?
        t_post="$(date +%s%3N)"
        t_delta="$((t_post - t_pre))"
        fraz="$(echo "$((1000 + t_delta % 1000))" | sed 's/^.//g')"
        t_delta="$((t_delta / 1000)).$fraz"
        some_test=1
        console_end $ret $t_delta
        if [ $ret -eq 0 ]; then
            xunit_ok "$tst" $t_delta "$test_dump"
        else
            xunit_failure "$tst" $t_delta "exit value not zero" "" "$test_dump" ""
        fi
    fi
done
if [ $some_test -eq 0 ]; then
    echo "No test started"
    usage 2
fi
if [ "$outfile" ]; then
    xunit_output >$outfile
fi
