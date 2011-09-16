# -*- coding: utf-8 -*-
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


from bulk_insert_unittest import *
from cache_gc_unittest import *
from db_loader_unittest import *
from db_loader_unittest import *
from db_routers_unittest import *
from deterministic_hazard_unittest import *
from deterministic_risk_unittest import *
from geo_unittest import *
from handlers_unittest import *
from hazard_classical_unittest import *
from hazard_nrml_unittest import *
from hazard_unittest import *
from input_risk_unittest import *
from java_unittest import *
from job_unittest import *
from kvs_unittest import *
from logs_unittest import *
from loss_map_output_unittest import *
from loss_output_unittest import *
from output_hazard_unittest import *
from output_risk_unittest import *
from output_unittest import *
from output_writers_unittest import *
from parser_exposure_portfolio_unittest import *
from parser_hazard_curve_unittest import *
from parser_hazard_map_unittest import *
from parser_vulnerability_model_unittest import *
from probabilistic_unittest import *
from producer_unittest import *
from risk_job_unittest import *
from risk_parser_unittest import *
from risk_unittest import *
from schema_unittest import *
from shapes_unittest import *
from signalling_unittest import *
from supervisor_unittest import *
from tools_dbmaint_unittest import *
from tools_oqbugs_unittest import *
from utils_config_unittest import *
from utils_general_unittest import *
from utils_tasks_unittest import *
from utils_version_unittest import *
from validator_unittest import *

import glob
import os
import sys

for path in glob.glob(os.path.join(os.path.dirname(__file__), '*test*.py')):
    test = os.path.splitext(os.path.basename(path))[0]
    module = 'tests.' + test

    if module not in sys.modules:
        print >> sys.stderr, "Potential missing import of " + module

import logging
# this is needed to avoid "no handlers" warning during test run
logging.getLogger('amqplib').addHandler(logging.NullHandler())
