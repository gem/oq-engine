#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2016, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import sys
from openquake.baselib import sap
from openquake.commonlib import config
from openquake.engine.utils import celerystatus


@sap.Script
def celery(cmd):
    """
    start the webui server in foreground or perform other operation on the
    django application
    """

    oq_distribute = config.get('distribution', 'oq_distribute')
    if oq_distribute != 'celery':
        sys.exit('This command requires celery as task distribution method: '
                 'see the documentation for details')

    celerystatus.report()

celery.arg('cmd', 'celery command', choices=['status'])
