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
import os
import re
import shlex
import subprocess

RE_REVIEWER = re.compile('\[r=(.*)\]')
RE_BUGS = re.compile('\[f=(.*)\]')


HOME_DIR = os.getenv('HOME')
CACHE_DIR = os.path.expanduser("~/.launchpadlib/cache/")


class CommitsOutput(object):
    """
        Helper class for git commit output
    """

    @staticmethod
    def since(time):
        """
            Reads from git
            extracts the output from a pipe
            returns read lines
        """
        git_cmd = shlex.split("git log --merges --since='%s'" % time)
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
        return out.splitlines()


# A serie of ArgumentParser action(s) that are triggered by parse_args()
class FixCommitted(argparse.Action):
    """ Changes the status of a bug to Fix Committed when it is in
        the repository
    """
    def __call__(self, parser, namespace, values, option_string=None):
        values = True
        print 'FixCommitted: %r %r %r' % (namespace, values, option_string)
        setattr(namespace, self.dest, values)


class FixReleased(argparse.Action):
    """
        Changes the status of a bug to Fix Released when it's triggered
        from the CI or other program
    """
    def __call__(self, parser, namespace, values, option_string=None):
        print 'FixReleased: %r %r %r' % (namespace, values, option_string)
        setattr(namespace, self.dest, values)


class ChangeLog(argparse.Action):
    """
        Prints on screen the ChangeLog since a time
    """
    def __call__(self, parser, namespace, values, option_string=None):
        print 'ChangeLog: %r %r %r' % (namespace, values, option_string)

        # hack to pass a parameter to the ArgumentParser Custom Action
        commits_output = CommitsOutput.since(namespace.time)

        launchpad = Launchpad.login_with('OpenQuake Bug Bot', 'staging',
                CACHE_DIR)
        for line in commits_output:
            commit_line = line.strip().split()
            reviewers = filter_reviewers(commit_line.pop(0))
            bugs = filter_bugs(launchpad, commit_line.pop(0))
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
        setattr(namespace, self.dest, values)


def arg_parse():
    """
        Prepares ArgumentParser for argument checking/triggering
    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('-t', '--time', dest="time",
            help="time: timeframe (i.e '1 month', '1 week', etc) \
                with quotes",
            metavar="TIME",
            required=True)
    parser.add_argument('-c', '--fix-committed', action=FixCommitted,
            help="Invoked from the CI gets from a git repository every \
                bug and changes status on launchpad to Fix Committed",
            default=False,
            nargs="?",
            required=False)

    parser.add_argument('-r', '--fix-released', action=FixReleased,
            help="Invoked from the ppa build fetches from a git repository \
                every with Fix Committed status and changes it to \
                Fix Released",
            default=False,
            nargs="?",
            required=False)

    parser.add_argument('-l', '--change-log', action=ChangeLog,
            help="Invoked from the CI gets from a git repository every \
                bug and changes status on launchpad to Fix Committed",
            nargs="?",
            required=False)

    args = parser.parse_args()
    return parser, args


def filter_reviewers(reviewers):
    """
        Little helper function to filter reviewers
    """
    filtered_reviewers = [reviewer for reviewer in
            RE_REVIEWER.findall(reviewers).pop(0).split(',')]
    return ','.join(filtered_reviewers)


def filter_bugs(lp, bugs):
    """
        Little helper function to filter bugs
    """
    return [lp.bugs[bug]
                for bug in RE_BUGS.findall(bugs).pop(0).split(',')
                if not bug.startswith('*')]

if __name__ == '__main__':
    (PARSER, ARGS) = arg_parse()
