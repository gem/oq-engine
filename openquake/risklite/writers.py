#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2010-2013, GEM foundation

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


class ScenarioDamageWriter(object):
    """
    Write a tab-separated csv file with the format

    id damage_state mean stddev
    """
    def __init__(self, path, damage_states):
        self.outfile = open(path, 'w')
        self.damage_states = damage_states

    def write(self, id_, mean, std):
        for d, m, s in zip(self.damage_states, mean, std):
            self.outfile.write('%s\t%s\t%s\t%s\n' % (id_, d, m, s))

    def serialize(self, data):
        with self.outfile:
            for id_, mean, std in data:
                self.write(id_, mean, std)

    def close(self):
        self.outfile.close()


class ScenarioWriter(object):
    """
    Write a tab-separated csv file with the format

    id damage_state mean stddev
    """
    def __init__(self, path):
        self.outfile = open(path, 'w')

    def write(self, asset, mean, std):
        self.outfile.write('%s\t%s\t%s\n' % (asset, mean, std))

    def serialize(self, data):
        with self.outfile:
            for asset, mean, std in data:
                self.write(asset, mean, std)

    def close(self):
        self.outfile.close()
