# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import re
import sys
from setuptools import setup

def generate_data_files(source_dir):
    # Helper function for demos
    data_files_list = []
    for target_dir, _dirs, files in os.walk(source_dir):
        if files:
            source_files = [os.path.join(target_dir, f) for f in files]
            data_files_list.append((target_dir, source_files))
    return data_files_list

setup(
    data_files=generate_data_files('demos'),
    )
