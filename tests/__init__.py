# -*- coding: utf-8 -*-
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


from bulk_insert_unittest import *
from cache_gc_unittest import *
from calculators.hazard.disagg.subsets_unittest import *
from db_fields_unittest import *
from db_loader_unittest import *
from db_loader_unittest import *
from db.models_unittest import *
from db_routers_unittest import *
from disaggregation_unittest import *
from engine_unittest import *
from hazard_classical_unittest import *
from hazard_nrml_unittest import *
from hazard_unittest import *
from input_logictree_unittest import *
from input_risk_unittest import *
from java_unittest import *
from job_unittest import *
from kvs_unittest import *
from logs_unittest import *
from loss_map_output_unittest import *
from loss_output_unittest import *
from output_hazard_unittest import *
from output_risk_unittest import *
from output.risk_unittest import *
from output_unittest import *
from output_writers_unittest import *
from parser_exposure_model_unittest import *
from parser_fragility_model_unittest import *
from parser_hazard_curve_unittest import *
from parser_hazard_map_unittest import *
from parser_vulnerability_model_unittest import *
from probabilistic_unittest import *
from producer_unittest import *
from risk_job_unittest import *
from risk_parser_unittest import *
from risk_unittest import *
from scenario_hazard_unittest import *
from scenario_risk_unittest import *
from schema_unittest import *
from shapes_unittest import *
from signalling_unittest import *
from supervisor_unittest import *
from tools_dbmaint_unittest import *
from tools_oqbugs_unittest import *
from utils_config_unittest import *
from utils_general_unittest import *
from utils_stats_unittest import *
from utils_tasks_unittest import *
from utils_version_unittest import *
from validator_unittest import *
from writer_unittest import *

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
