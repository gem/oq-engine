#!/bin/bash
# set -x
cd demos/hazard
python -m openquake.commands run LogicTreeCase3ClassicalPSHA/job.ini --exports xml &
lite_pid=$!
sleep 5
kill -SEGV $lite_pid
sleep 2
survived="$( ps ax | grep oq-lite | grep python | grep -v grep | sed 's/^ *//g;s/ .*//g' )"
survived_number="$(echo "$survived" | grep -v '^$' | wc -l | tr -d ' ' )"

wait $!

# # cleanup
if [ $survived_number -ne 0 ]; then
    IFS='
'
    for i in $(echo "$survived" | grep -v '^$'); do
        kill -KILL $i
    done
fi

exit $survived_number
