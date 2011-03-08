# This file is part of OpenQuake.
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

""" Handlers for guarantee_file """

import paramiko
import re
import socket

from httplib import HTTPConnection, HTTPSConnection
from paramiko import (
    AuthenticationException, BadAuthenticationType, SSHException)

CREDENTIALS_RE = re.compile("(?P<username>.*?):(?P<password>.*)@")
HOST_PORT_RE = re.compile("(?:(?:.*@)?)(?P<host>.*?)(?::(?P<port>\d+)|$)")

DEFAULT_SSH_PORT = 22


def resolve_handler(parsed_url, base_path):
    """ Resolve to a File Handler """
    handlers = {
        '': FileHandler,
        'file': FileHandler,
        'sftp': SFTPHandler,
        'http': HTTPHandler,
        'https': HTTPHandler,
    }

    return handlers[parsed_url.scheme](parsed_url, base_path)


class HandlerError(Exception):
    """ Raised from Handler descendents """
    pass


class Handler(object):
    """ A generic handler that doesn't do anything. """

    def __init__(self, parsed_url, base_path):
        self.parsed_url = parsed_url
        self.base_path = base_path

    @property
    def credentials(self):
        """ Extract the credentials from the parsed URL """
        credentials = (None, None)
        cred_match = CREDENTIALS_RE.match(self.parsed_url.netloc)
        if cred_match:
            credentials = cred_match.group('username', 'password')
        return credentials

    @property
    def host_and_port(self):
        """ Extract the host and port from the parsed URL """
        return HOST_PORT_RE.match(self.parsed_url.netloc).group('host', 'port')

    @property
    def filename(self):
        """ Get the filename from the parsed_url.path """
        return self.parsed_url.path.split('/')[-1]

    @property
    def guaranteed_file_path(self):
        """ Concatenate self.base_path and self.filename """
        return self.base_path + self.filename


class FileHandler(Handler):
    """ A handler for local paths """

    def handle(self, getter=None): #pylint: disable=W0613
        """ Write this file to base_path. """ 
        with open(self.guaranteed_file_path, "w") as writer:
            with open(self.parsed_url.path, "r") as reader:
                writer.write(reader.read())

        return self.guaranteed_file_path


class SFTPHandler(Handler):
    """ A handler for files on remote systems accessible via SSH. """

    def handle(self, getter=None):
        """ Write out the file and return the full path """
        host, port = self.host_and_port
        username, password = self.credentials
        transport = None

        if not port:
            port = DEFAULT_SSH_PORT

        if not getter:
            try:
                transport = paramiko.Transport((host, int(port)))
                transport.connect(username=username, password=password)
            except (BadAuthenticationType, AuthenticationException), e:
                if transport:
                    transport.close()
                raise HandlerError("Could not login. Bad Credentials")
            except (SSHException, socket.error), e:
                if transport:
                    transport.close()
                raise HandlerError(e)
            getter = paramiko.SFTPClient.from_transport(transport)
        else:
            getter = getter(host, port)

        getter.get(self.parsed_url.path, self.guaranteed_file_path)

        if transport and transport.is_active():
            getter.close()
            transport.close()

        return self.guaranteed_file_path


class HTTPHandler(Handler):
    """ A handler for files accessible via http/https"""

    def handle(self, getter=None):
        """ Write out the file and return the full path """

        if not getter:
            if self.parsed_url.scheme == 'http':
                getter = HTTPConnection 
            elif self.parsed_url.scheme == 'https':
                getter = HTTPSConnection
            else:
                raise HandlerError("Unexpected HTTPHandler URI scheme, "
                                   "expected https or http!")

        host, port = self.host_and_port

        with open(self.guaranteed_file_path, "w") as guaranteed_file:
            with getter(host, port) as conn:
                request = conn.request("GET", self.parsed_url.path)
                response = request.getresponse()
                guaranteed_file.write(response.read())

        return self.guaranteed_file_path
