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


import StringIO

from openquake.calculators import base
from openquake.calculators.hazard import general


class ClassicalHazardCalculator(base.CalculatorNext):

    def pre_execute(self):
        site_model = general.get_site_model(self.job.hazard_calculation.id)

        if site_model is not None:
            # Explicit cast to `str` here because the XML parser doesn't like
            # unicode. (More specifically, lxml doesn't like unicode.)
            site_model_content = str(site_model.model_content.raw_content)
            site_model_data = general.store_site_model(
                site_model, StringIO.StringIO(site_model_content))

            general.validate_site_model(
                site_model_data,
                self.job.hazard_calculation.points_to_compute())
