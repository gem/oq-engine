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

from nhlib import correlation

from openquake.calculators.hazard import general as haz_general

#: Ground motion correlation model map
GM_CORRELATION_MODEL_MAP = {
    'JB2009': correlation.JB2009CorrelationModel,
}


class EventBasedHazardCalculator(haz_general.BaseHazardCalculatorNext):
    # TODO: Just a skeleton of the new calculator to get the engine bits and
    # param validation wired up

    def pre_execute(self):
        # TODO: implement me
        print "pre_execute"

    def execute(self):
        # TODO: implement me
        print "execute"

    def post_execute(self):
        # TODO: implement me
        print "post_execute"

    def post_process(self):
        # TODO: implement me
        print "post_process"
