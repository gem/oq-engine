# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
This module contains common stuff for parsing NRML instance files.
"""

from lxml import etree

from openquake import logs

from openquake import producer
from openquake import shapes
from openquake import xml


LOG = logs.LOG

# TODO(fab): collect common stuff for all parsers here
