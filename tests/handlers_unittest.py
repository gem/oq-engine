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



import os
import unittest
import urlparse

from tests.utils import helpers
from openquake.job import handlers

class StubbedGetter(object):
    def __init__(self, host, port):
        pass


class FileHandlerTestCase(unittest.TestCase):
    def test_file_handler_writes_a_file(self):
        expected_path = "/tmp/fake_file"
        remote_path = helpers.get_data_path("config.gem")
        url = urlparse.urlparse(remote_path)

        file_handler = handlers.FileHandler(url, expected_path)
        guaranteed_file = file_handler.handle()
        self.assertTrue(os.path.isfile(guaranteed_file))
        os.unlink(guaranteed_file)


class SFTPHandlerTestCase(unittest.TestCase):
    def test_ssh_handler_raises_on_bad_credentials(self):
        url = urlparse.urlparse("sftp://baduser:badpass@localhost:22/path/to/file")
        sftp_handler = handlers.SFTPHandler(url, '') 
        self.assertRaises(handlers.HandlerError, sftp_handler.handle)

    def test_ssh_handler_raises_on_bad_netloc(self):
        url = urlparse.urlparse("sftp://doesntexist/path/to/file")
        sftp_handler = handlers.SFTPHandler(url, '')
        self.assertRaises(handlers.HandlerError, sftp_handler.handle)

    def test_ssh_handler_writes_a_file(self):
        class StubbedSFTPClient(StubbedGetter):
            def get(self, remote_path, local_path):
                with open(local_path, "w") as writer:
                    with open(remote_path, "r") as reader:
                        writer.write(reader.read())

        expected_path = "/tmp/fake_file"
        remote_path = "sftp://localhost/%s" % helpers.get_data_path("config.gem")
        url = urlparse.urlparse(remote_path)

        sftp_handler = handlers.SFTPHandler(url, expected_path)
        guaranteed_file = sftp_handler.handle(getter=StubbedSFTPClient)
        self.assertTrue(os.path.isfile(guaranteed_file))
        os.unlink(guaranteed_file)

class HTTPHandlerTestCase(unittest.TestCase):
    def test_http_handler_raises_on_bad_schema(self):
        url = urlparse.urlparse("bloop://host.domain/path/to/file")
        http_handler = handlers.HTTPHandler(url, '')
        self.assertRaises(handlers.HandlerError, http_handler.handle)

    def test_http_handler_writes_a_file(self):
        class StubbedHTTPConnection(StubbedGetter):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def request(self, req_type, path):
                self.remote_path = path 
                return self

            def getresponse(self):
                return self

            def read(self):
                with open(self.remote_path, "r") as reader:
                    return reader.read()

        expected_path = "/tmp/fake_file"
        remote_path = "http://localhost/%s" % helpers.get_data_path("config.gem")
        url = urlparse.urlparse(remote_path)

        http_handler = handlers.HTTPHandler(url, expected_path)
        guaranteed_file = http_handler.handle(getter=StubbedHTTPConnection)
        self.assertTrue(os.path.isfile(guaranteed_file))
        os.unlink(guaranteed_file)
