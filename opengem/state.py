#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Eventually this will manage shared system state via memcached,
for now it's just global variables :)
"""

import logging
import sys

STATE = {}
