# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Quick tests to demonstrate that we can serialize into
memcached in Python and deserialize in Java and viceversa.

To run these tests you need to:

* Install Pylibmc
* Install Jpype
* A memcached server running somewhere

"""

import os
import jpype
import pylibmc
import unittest

MEMCACHED_PORT = 11211
MEMCACHED_HOST = "localhost"

# starting the jvm...
jarpath = os.path.join(os.path.abspath(".."), "lib")
jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.ext.dirs=%s" % jarpath)

class MemcachedTestCase(unittest.TestCase):
    
    def setUp(self):
        java_class = jpype.JClass("org.gem.engine.hazard.memcached.Cache")
        self.java_client = java_class(MEMCACHED_HOST, MEMCACHED_PORT)
        
        # clean server side cache
        self.java_client.flush()
        
        self.python_client = pylibmc.Client([
                MEMCACHED_HOST + ":%d" % MEMCACHED_PORT], binary=False)
    
    def test_can_wrap_the_java_client(self):
        self.java_client.set("KEY", "VALUE")
        self.assertEqual("VALUE", self.java_client.get("KEY"))

    def test_can_write_in_java_and_read_in_python(self):
        self.java_client.set("ANOTHER_KEY", "ANOTHER_VALUE")
        self.assertEqual("ANOTHER_VALUE", self.python_client.get("ANOTHER_KEY"))
    
    def test_can_write_in_python_and_read_in_java(self):
        self.python_client.set("SOME_KEY", "SOME_VALUE")
        self.assertEqual("SOME_VALUE", self.java_client.get("SOME_KEY"))
    
if __name__ == "__main__":
    unittest.main()