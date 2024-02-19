# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2023 GEM Foundation
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

from django.apps import AppConfig


class ServerConfig(AppConfig):
    name = 'openquake.server'

    def ready(self):
        # From Django manual:
        #     Subclasses can override this method to perform initialization
        #     tasks such as registering signals. It is called as soon as the
        #     registry is fully populated.
        #     Although you can’t import models at the module-level where
        #     AppConfig classes are defined, you can import them in ready()
        import openquake.server.signals  # NOQA
