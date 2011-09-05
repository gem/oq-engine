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
Unit tests for the tools/oqbugs.py tool.
"""

import unittest
from tools.oqbugs import (CommitsOutput, extract_reviewers, filter_bugs,
        launchpad_lookup, fix_apply)
import mock
import os
from argparse import Namespace
import datetime

CACHE_DIR = os.path.expanduser("~/.launchpadlib-test/cache/")


def prepare_mock(bugs):
    """
        prepares mock objects for tests
    """

    mock_name = mock.Mock()
    mock_name.name = 'Funky Monk'
    mock_name.title = 'OpenQuake'
    attributes = {
     'date_fix_committed': str(datetime.datetime.now()),
     'assignee': mock_name,
     'milestone': mock_name,
     'status': 'In Progress',
     'web_link': 'http://openquake.org'}

    bugs_list = {}
    # prepares instances of mocked launchpad's bug objects
    for bug in bugs:
        # MagicMock supports most of python's "magical" methods
        magic_mock = mock.MagicMock()

        for prop, val in attributes.iteritems():
            magic_mock.title = 'a bug title'
            setattr(magic_mock.bug_tasks[0], prop, val)

            # prepares a dictionary for mocking launchpad_instance.bugs
            # lookup. key is bug number, value is a prepared MagicMock object
            bugs_list.update({bug: magic_mock})
    return bugs_list


class OqBugsTestCase(unittest.TestCase):
    """Tests the mechanics of oqbugs ."""

    def setUp(self):
        self.bugs = {}

        def getitem(name):
            """ utility methods for returning dict data from a mock """
            return self.bugs[name]

        self.correct_commits = ['[r=favalex][f=827908]',
                '[r=mbarbon][f=*827366]',
                '[r=favalex][f=819689]', '[r=mbarbon] [f=827256]',
                '[r=larsbutler][f=807360]', '[r=al-maisan] [f=812698]',
                '[r=al-maisan][f=802396]', '[r=favalex][f=817081]',
                '[r=larsbutler][f=809217]', '[r=larsbutler] [f=82464]']

        self.skip_commits = ['[r=mbarbon][f=*827366]']
        self.multiple_bugs_commit = ['[r=mbarbon][f=827366,812698,809217]']
        self.wrong_lines = ['lorem', 'loren', 'sofia']

        self.launchpad = mock.MagicMock()
        self.launchpad.bugs.__getitem__ = mock.Mock(side_effect=getitem)

    def test_commits_output_is_empty(self):
        self.assertEquals(CommitsOutput.since('0 week'), [])

    # one month to be sure to have commit lines
    def test_commits_output_for_one_month(self):
        self.assertTrue(len(CommitsOutput.since('1 month')))

    # interval between two openquake milestones
    def test_commits_output_interval(self):
        self.assertTrue(len(CommitsOutput.since("2011-07-20T00:00:00",
            until="2011-08-09T00:00:00")))

    def test_commits_output_reviewers(self):
        for commit in self.correct_commits:
            self.assertTrue(len(extract_reviewers(commit)))

    def test_filter_bugs_multiple(self):
        self.assertEquals(
                len(list(filter_bugs(self.multiple_bugs_commit[0]))), 3)

    def test_filter_bugs_skip(self):
        for commit in self.skip_commits:
            self.assertEquals(len(list(filter_bugs(commit))), 0)

    def test_filter_bugs_wrong_format(self):
        for bug in self.wrong_lines:
            self.assertEquals(filter_bugs(bug), [])

    def test_launchpad_instances(self):
        bugs_list = filter_bugs(self.multiple_bugs_commit[0])
        self.bugs = prepare_mock(bugs_list)
        self.assertEquals(len(launchpad_lookup(self.launchpad,
                self.bugs.keys())), 3)

    def test_launchpad_attributes(self):
        bugs_list = filter_bugs(self.correct_commits[0])
        self.bugs = prepare_mock(bugs_list)
        for bug_instance in launchpad_lookup(self.launchpad, self.bugs.keys()):
            self.assertTrue(isinstance(bug_instance.title, str))
            self.assertTrue(isinstance(
                bug_instance.bug_tasks[0].date_fix_committed, str))
            self.assertTrue(isinstance(
                bug_instance.bug_tasks[0].assignee.name, str))
            self.assertTrue(isinstance(
                bug_instance.bug_tasks[0].web_link, str))

    def test_commits_output_bugs(self):
        for commit in self.correct_commits:
            # preparing bugs for mocker
            self.bugs = prepare_mock(commit)
            for bug in launchpad_lookup(self.launchpad, self.bugs):
                self.assertTrue(isinstance(bug, mock.Mock))

    def test_fix_committed_and_fix_released(self):
        for commit in self.correct_commits:
            # preparing bugs for mocker
            self.bugs.update(prepare_mock(filter_bugs(commit)))

        # gets the FixApply instances reference by calling the fix_apply
        # method with specific args
        lp_fixes = {
            'Fix Committed': fix_apply(self.launchpad,
                self.correct_commits, 'Fix Committed'),
            'Fix Released': fix_apply(self.launchpad,
                self.correct_commits, 'Fix Released')}

        namespace = Namespace(time='1 week')

        for status, lp_fix in lp_fixes.iteritems():
            # creates an argparse action instance and __call__[s] it passing
            # the namespace object
            bugs = lp_fix(None, None)(None, namespace,
                    None)

            # there should be bugs (mocked objects) returned
            self.assertTrue(len(bugs))
            for bug in bugs:
                self.assertEqual(status, bug.bug_tasks[0].status)
