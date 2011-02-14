import os
import unittest
import urlparse

from utils import test
from openquake.job import handlers

class StubbedGetter(object):
    def __init__(self, host, port):
        pass


class FileHandlerTestCase(unittest.TestCase):
    def test_file_handler_writes_a_file(self):
        expected_path = "/tmp/fake_file"
        remote_path = test.test_file("config.gem")
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
        remote_path = "sftp://localhost/%s" % test.test_file("config.gem")
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
        remote_path = "http://localhost/%s" % test.test_file("config.gem")
        url = urlparse.urlparse(remote_path)

        http_handler = handlers.HTTPHandler(url, expected_path)
        guaranteed_file = http_handler.handle(getter=StubbedHTTPConnection)
        self.assertTrue(os.path.isfile(guaranteed_file))
        os.unlink(guaranteed_file)
