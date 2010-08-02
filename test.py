# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Base classes for our unit tests.
"""

import os
import unittest

class BaseTestCase(unittest.TestCase):
    """Base class for our test cases 
    (supports fetching resources for test validation)"""
    resources_folder = "tests/resources"
    
    def __init__(self, args, **kwargs):
        super(BaseTestCase, self).__init__(args, **kwargs)
    
    def setUp(self):
        super(BaseTestCase, self).setUp()
        
    def resource_path(self, file_name):
        """Resolve the path of the resources for test cases"""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), self.resources_folder, file_name))
