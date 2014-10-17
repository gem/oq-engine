#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import operator
from openquake.commonlib.general import import_all, MultiFunction

calculate = MultiFunction(operator.attrgetter('calculation_mode'))


class BaseCalculator(object):
    """
    To be subclassed. Instantiating a calculator performs some initialization,
    run the execute method, post process the results and populate a list
    of exported files.
    """
    def __init__(self, oqparam):
        self.oqparam = oqparam
        self.pre_execute()
        result = self.execute()
        self.exported = self.post_execute(result)

    def __iter__(self):
        """
        You can iterate on the set of the exported files
        """
        return iter(self.exported)

    @staticmethod
    def core(*args):
        """
        Core staticmethod running on the workers.
        Usually returns a collections.Counter instance.
        """
        raise NotImplemented

    def pre_execute(self):
        """
        Initialization phase. Doing nothing by default.
        """

    def execute(self):
        """
        Execution phase. Usually will run in parallel the core
        staticmethod and result a Counter with the results.
        """
        raise NotImplemented

    def post_execute(self, result):
        """
        Post-processing phase of the aggregated output. It must be
        overridden with the export code.
        """
        raise NotImplemented

import_all('openquake.lite.calculators')
