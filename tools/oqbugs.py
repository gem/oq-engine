#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
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

"""
    A tool to automatically query/close bugs after a git merge
"""


from launchpadlib.launchpad import Launchpad
import argparse
import logging
import itertools
import os
import re
import shlex
import subprocess
from openquake import __version__

# regexps
RE_BUGS = re.compile('\[f=(.*?)\]')
RE_REVIEWER = re.compile('\[r=(.*?)\]')

CACHE_DIR = os.path.expanduser("~/.launchpadlib/cache/")

PROJECT_NAME = 'OpenQuake'


def launchpad_login():
    """ returns a Launchpad instance """
    return Launchpad.login_with('OpenQuake Bug Bot', 'production',
                CACHE_DIR)


def milestone_interval(launchpad):
    """
        * fetches current openquake's version
        * returns current milestone date_targeted attribute
        * returns the first inactive milestone
    """

    # WARNING: be sure to export PYTHONPATH=`pwd` on the git clone'd folder
    # otherwise if there's python-oq installed the version picked is the
    # 'system' version
    cur_milestone_ver = '.'.join(
            [str(datum) for datum in __version__[:3]])

    cur_milestone = launchpad.projects["openquake"].getMilestone(
        name=cur_milestone_ver)
    for  milestone in cur_milestone.series_target.all_milestones:
        if not milestone.is_active:
            prev_milestone_inactive = milestone
            break

    return (cur_milestone.date_targeted, prev_milestone_inactive.date_targeted)


class CommitsOutput(object):
    """
        Helper class for git commit output
    """

    @staticmethod
    def since(time, until=None):
        """
            Reads from git
            extracts the output from a pipe
            returns read lines
        """

        #git_cmd = shlex.split("git log --merges --since='%s'" % time)
        git_cmd = ["git", "log", "--merges",  "--since", time]

        if until:
            git_cmd.extend(shlex.split("--until='%s'" % until))

        git = subprocess.Popen(
            git_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        grep_cmd = shlex.split("grep '\[r='")
        grep = subprocess.Popen(grep_cmd, stdin=git.stdout,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        out, err = grep.communicate()

        if grep.returncode != 0 and len(out):
            error = ("%s terminated with exit code: %s\n%s"
                     % (' '.join(git_cmd) + '|' + ' '.join(grep_cmd),
                         grep.returncode, err))
            logging.error(error)
            raise Exception(error)

        return [line.strip() for line in out.splitlines()]


# A serie of ArgumentParser action(s) that are triggered by parse_args()
def fix_apply(launchpad, commit_lines, status_type):
    """
        convenience wrapper function to pass parameters to FixApply
        argparse action
    """
    class FixApply(argparse.Action):
        """
            Changes the status of a bug to status_type
            (Fix Committed/Fix Released)
        """

        def __call__(self, parser, namespace, values, option_string=None):

            changed_bugs = []
            for commit_line in commit_lines:
                if namespace.time:
                    bugs = launchpad_lookup(launchpad,
                            filter_bugs(commit_line))

                    for bug in bugs:
                        if bug.bug_tasks[0].status != status_type:
                            # this assignment triggers a call to the
                            # launchpadapi that changes the status of the
                            # bug into status_type
                            bug.bug_tasks[0].status = status_type
                            changed_bugs.append(bug)
            return changed_bugs
    return FixApply


def changelog(launchpad, commit_lines):
    """
        convenience wrapper function to pass parameters to ChangeLog
        argparse action
    """
    class ChangeLog(argparse.Action):
        """
            Prints on screen the ChangeLog since a time or between milestones
            releases
        """
        def __call__(self, parser, namespace, values, option_string=None):

            for commit_line in commit_lines:
                reviewers = extract_reviewers(commit_line)
                # TODO: generalize filter_bugs to match multiple lines and
                # speed up the launchpad_lookup process
                bugs = launchpad_lookup(launchpad,
                        filter_bugs(commit_line))
                for bug in bugs:
                    entry = """Fix-committed:  %s
Summary:        %s
Url:            %s
Reviewed-by:    %s
Closed-by:      %s
""" % (
                        str(bug.bug_tasks[0].date_fix_committed),
                        str(bug.title),
                        str(bug.bug_tasks[0].web_link),
                        str(reviewers),
                        str(bug.bug_tasks[0].assignee.name))

                    print entry
    return ChangeLog


def arg_parse():
    """
        Prepares ArgumentParser for argument checking/triggering
    """

    launchpad = None
    commits_output = []
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)

    parser.add_argument('-t', '--time', dest="time",
            help="time: timeframe (i.e '1 month', '1 week', etc) \
                with quotes",
            metavar="TIME")

    # pre-parse time to provide it to the next parser with custom methods in
    # custom argparse actions
    args, remaining_argv = parser.parse_known_args()

    if remaining_argv:
        if args.time:
            launchpad = launchpad_login()
            commits_output = CommitsOutput.since(args.time)
            remaining_argv.extend(['-t', args.time])
        else:
            launchpad = launchpad_login()
            cur_milestone_date, prev_milestone_date = milestone_interval(
                launchpad)

            commits_output = CommitsOutput.since(
                prev_milestone_date.isoformat(),
                until=cur_milestone_date.isoformat())

    # "merges" the two parsers and instantiate the second final parser
    action_parser = argparse.ArgumentParser(description=__doc__,
            parents=[parser],
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=True)

    action_group = action_parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('-c', '--fix-committed',
            action=fix_apply(launchpad, commits_output, 'Fix Committed'),
            help="Invoked from the CI gets from a git repository every \
                bug and changes status on launchpad to Fix Committed",
            nargs=0,
            dest='fix_committed',
            required=False)

    action_group.add_argument('-r', '--fix-released',
            action=fix_apply(launchpad, commits_output, 'Fix Released'),
            help="Invoked from the ppa build fetches from a git repository \
                every with Fix Committed status and changes it to \
                Fix Released",
            nargs=0,
            required=False)

    action_group.add_argument('-l', '--changelog',
            action=changelog(launchpad, commits_output),
            help="Invoked from the CI gets from a git repository every \
                bug and changes status on launchpad to Fix Committed",
            nargs=0,
            required=False)

    args = action_parser.parse_args(remaining_argv)

    return args


def extract_reviewers(reviewers):
    """
        Little helper function to filter reviewers
    """

    filtered_reviewers = [reviewer for reviewer in
            RE_REVIEWER.findall(reviewers).pop(0).split(',')]
    return ','.join(filtered_reviewers)


def launchpad_lookup(lp, bugs):
    """ looks up a list of bugs in launchpad """
    try:
        bug_instances = [lp.bugs[bug] for bug in bugs if bug]

        # returns bug_instances if they are belonging to PROJECT_NAME
        return [bug_instance for bug_instance in bug_instances
                if bug_instance.bug_tasks[0].milestone
                and (
                PROJECT_NAME in bug_instance.bug_tasks[0].milestone.title)]
    # Sometimes launchpad does not fetch the correct bug, we have to handle
    # this situation
    except KeyError, e:
        error_message = 'Bug not found, maybe a launchpad api error or ' \
                'staging area? bug: %s' % e
        logging.error(error_message)
        raise Exception(error_message)


def filter_bugs(commit):
    """
        Little helper function to filter bugs

        Discards also bugs that are starting with '*' which are marked to be
        skipped
    """
    bugs = RE_BUGS.findall(commit)
    if len(bugs):
        return itertools.ifilterfalse(
            lambda bug: bug.startswith('*'),
            bugs.pop(0).split(','))
    return bugs


if __name__ == '__main__':
    arg_parse()
