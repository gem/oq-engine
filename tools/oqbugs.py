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

# regexps
RE_BUGS = re.compile('\[f=(.*?)\]')
RE_REVIEWER = re.compile('\[r=(.*?)\]')

CACHE_DIR = os.path.expanduser("~/.launchpadlib/cache/")


def parse_and_login(time=None):
    """
        Convenience function to parse and login to launchpad
    """
    launchpad = None
    commits_output = []

    if time:
        commits_output = CommitsOutput.since(time)

        launchpad = Launchpad.login_with('OpenQuake Bug Bot', 'production',
                CACHE_DIR)

    return launchpad, commits_output


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

        return [line.strip() for line in out.splitlines()]


# A serie of ArgumentParser action(s) that are triggered by parse_args()
def fix_committed(launchpad, commit_lines):
    class FixCommitted(argparse.Action):
        """ Changes the status of a bug to Fix Committed when it is in
            the master repository (i.e. merged)
        """

        def __call__(self, parser, namespace, values, option_string=None):


            print 'FixCommitted: %s %r %r %r' % (parser, namespace, 
                    values, option_string)

            changed_bugs = [] 
            for commit_line in commit_lines:
                if namespace.time:
                    bugs = launchpad_lookup(launchpad, 
                            filter_bugs(commit_line))
                    
                    for bug in bugs:
                        if bug.bug_tasks[0].status != "Fix Committed":
                            bug.bug_tasks[0].status = 'Fix Committed'
                            changed_bugs.append(bug)
            return changed_bugs
    return FixCommitted


class FixReleased(argparse.Action):
    """
        Changes the status of a bug to Fix Released when the release packages
        are built
    """
    def __call__(self, parser, namespace, values, option_string=None):
        print 'FixReleased: %r %r %r' % (namespace, values, option_string)
        setattr(namespace, self.dest, values)


def changelog(launchpad, commit_lines):
    class ChangeLog(argparse.Action):
        """
            Prints on screen the ChangeLog since a time
        """
        def __call__(self, parser, namespace, values, option_string=None):
            print 'ChangeLog: %r %r %r' % (namespace, values, option_string)

            for commit_line in commit_lines:
                reviewers = filter_reviewers(commit_line)
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
            metavar="TIME"
            )

    # pre-parse time to provide it to the next parser with custom methods in
    # custom argparse actions
    args, remaining_argv = parser.parse_known_args()

    parser._actions[0].required = True

    if args.time:
        if len(remaining_argv):
            (launchpad, commits_output) = parse_and_login(args.time)
        remaining_argv.extend(['-t', args.time])

    # merges the two parsers and instantiate the second final parser
    action_parser = argparse.ArgumentParser(description=__doc__, 
            parents=[parser],
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=True)


    # hack
    action_group = action_parser.add_mutually_exclusive_group()
    action_group.add_argument('-c', '--fix-committed', 
            action=fix_committed(launchpad, commits_output),
            help="Invoked from the CI gets from a git repository every \
                bug and changes status on launchpad to Fix Committed",
            nargs=0,
            dest='fix_committed',
            required=False)

    action_group.add_argument('-r', '--fix-released', action=FixReleased,
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

    action_parser.parse_args(remaining_argv)

    return args


def filter_reviewers(reviewers):
    """
        Little helper function to filter reviewers
    """

    filtered_reviewers = [reviewer for reviewer in
            RE_REVIEWER.findall(reviewers).pop(0).split(',')]
    return ','.join(filtered_reviewers)

def launchpad_lookup(lp, bugs):
    try:
        return [lp.bugs[bug] for bug in bugs]
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
    """
    bugs = RE_BUGS.findall(commit)
    if len(bugs):
        return itertools.ifilterfalse(
            lambda bug: bug.startswith('*'),
            bugs.pop(0).split(','))
    return bugs
                    

if __name__ == '__main__':
    arg_parse()
