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

"""Saves source model data (parsed from a NRML file) to the
'hzrdi.parsed_source' table.
"""

import pickle

from django.db import router
from django.db import transaction
from nrml import models as nrml_models

from openquake.db import models


def _source_type(src_model):
    """Given of the source types defined in :mod:`nrml.models`, get the
    `source_type` for a :class:`~openquake.db.models.ParsedSource`.
    """
    if isinstance(nrml_models.PointSource):
        return 'point'
    elif isinstance(nrml_models.AreaSource):
        return 'area'
    elif isinstance(nrml_models.SimpleFaultSource):
        return 'simple'
    elif isinstance(nrml_models.ComplexFaultSource):
        return 'complex'


class SourceDBWriter(object):
    """
    :param inp:
        :class:`~openquake.db.models.Input` object, the top-level container for
        the sources written to the database. Should have an input_type of
        'source'.
    :param source_model:
        :class:`nrml.models.SourceModel` object, which is an Iterable of NRML
        source model objects (parsed from NRML XML). This also includes the
        name of the source model.
    """

    def __init__(self, inp, source_model):
        self.inp = inp
        self.source_model = source_model

    @transaction.commit_on_success(router.db_for_writer(models.ParsedSource))
    def serialize(self):

        # First, set the input name to the source model name
        self.inp.name = self.source_model.name
        self.inp.save()

        for source in self.source_model:
            blob = pickle.dumps(source, pickle.HIGHEST_PROTOCOL)
            ps = models.ParsedSource(
                input=self.inp, source_type=_source_type(source), blob=blob,
            )

