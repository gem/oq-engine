# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2019 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import re
import zmq
import logging

context = zmq.Context()

# from integer socket_type to string
SOCKTYPE = {zmq.REQ: 'REQ', zmq.REP: 'REP',
            zmq.PUSH: 'PUSH', zmq.PULL: 'PULL',
            zmq.ROUTER: 'ROUTER', zmq.DEALER: 'DEALER'}


def bind(end_point, socket_type):
    """
    Bind to a zmq URL; raise a proper error if the URL is invalid; return
    a zmq socket.
    """
    sock = context.socket(socket_type)
    try:
        sock.bind(end_point)
    except zmq.error.ZMQError as exc:
        sock.close()
        raise exc.__class__('%s: %s' % (exc, end_point))
    return sock


def connect(end_point, socket_type):
    """
    Connect to a zmq URL; raise a proper error if the URL is invalid; return
    a zmq socket.
    """
    sock = context.socket(socket_type)
    try:
        sock.connect(end_point)
    except zmq.error.ZMQError as exc:
        sock.close()
        raise exc.__class__('%s: %s' % (exc, end_point))
    return sock


class Socket(object):
    """
    A Socket class to be used with code like the following::

     # server
     with Socket('tcp://127.0.0.1:9000', zmq.REP, 'bind') as sock:
         for tup in sock:
             sock.send(tup)

     # client
     with Socket('tcp://127.0.0.1:9000', zmq.REQ, 'connect') as sock:
        sock.send(tup)

    It also support zmq.PULL/zmq.PUSH sockets, which are asynchronous.

    :param end_point: zmq end point string
    :param socket_type: zmq socket type (integer)
    :param mode: default 'bind', accepts also 'connect'
    :param timeout: default 5000 ms, used when polling the underlying socket
    """
    def __init__(self, end_point, socket_type, mode, timeout=5000):
        assert socket_type in (zmq.REP, zmq.REQ, zmq.PULL, zmq.PUSH)
        assert mode in ('bind', 'connect'), mode
        if mode == 'bind':
            assert 'localhost' not in end_point, 'Use 127.0.0.1 instead'
        self.end_point = end_point
        self.socket_type = socket_type
        self.mode = mode
        self.timeout = timeout
        self.running = False

    def __enter__(self):
        """Instantiate the underlying zmq socket"""
        # first check if the end_point ends in :<min_port>-<max_port>
        port_range = re.search(r':(\d+)-(\d+)$', self.end_point)
        if port_range:
            assert self.mode == 'bind', self.mode
            p1, p2 = map(int, port_range.groups())
            end_point = self.end_point.rsplit(':', 1)[0]  # strip port range
            self.zsocket = context.socket(self.socket_type)
            port = self.zsocket.bind_to_random_port(end_point, p1, p2)
            # NB: will raise a ZMQBindError if no port is available
            self.port = port
        elif self.mode == 'bind':
            self.zsocket = bind(self.end_point, self.socket_type)
        else:  # connect
            self.zsocket = connect(self.end_point, self.socket_type)
        port = re.search(r':(\d+)$', self.end_point)
        if port:
            self.port = int(port.group(1))
        self.zsocket.__enter__()
        self.num_sent = 0
        return self

    def __exit__(self, *args):
        self.zsocket.__exit__(*args)
        del self.zsocket

    def __iter__(self):
        """
        Iterate on the socket and yield the received arguments. Exits if

        1. the flag .running is set to False
        2. SIGTERM is sent
        """
        # works with zmq.REP and zmq.PULL sockets
        self.running = True
        while self.running:
            try:
                if self.zsocket.poll(self.timeout):
                    args = self.zsocket.recv_pyobj()
                else:
                    # wait a bit more; print a warning for PULL sockets
                    if self.socket_type == 'PULL':
                        logging.warning('Timeout in %s', self)
                    continue
            except zmq.ZMQError:
                # sending SIGTERM raises ZMQError
                break
            yield args

    def send(self, obj):
        """
        Send an object to the remote server; block and return the reply
        if the socket type is REQ.

        :param obj:
            the Python object to send
        """
        self.zsocket.send_pyobj(obj)
        self.num_sent += 1
        if self.socket_type == zmq.REQ:
            return self.zsocket.recv_pyobj()

    def __repr__(self):
        return '<%s %s %s>' % (self.__class__.__name__,
                               SOCKTYPE[self.socket_type], self.mode)
