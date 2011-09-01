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

import logging
import unittest

from openquake import signalling

from tests.utils.helpers import patch


class SignallingTestCase(unittest.TestCase):

    def test_generate_routing_key(self):
        self.assertEqual('log.failed.123',
                         signalling.generate_routing_key(123, 'failed'))

    def test_generate_routing_key_wrong_job_id(self):
        self.assertRaises(AssertionError, signalling.generate_routing_key,
                          'invalid job id', '*')

    def test_generate_routing_key_wrong_type(self):
        self.assertRaises(AssertionError, signalling.generate_routing_key,
                          123, 'invalid type')

    def test_signalling(self):
        """
        Test connecting to the server, binding a queue to the signalling
        exchange and signalling the outcome of a job.
        """

        # Create the exchange and bind a queue to it
        conn, ch = signalling.connect()

        qname = signalling.declare_and_bind_queue(0, ('succeeded',))

        # Send a message
        signalling.signal_job_outcome(0, 'succeeded')

        messages = []

        def callback(msg):
            messages.append(msg)
            ch.basic_cancel(msg.consumer_tag)

        ch.basic_consume(qname, callback=callback)

        while ch.callbacks:
            ch.wait()

        ch.close()
        conn.close()

        self.assertEqual(1, len(messages))

    def test_parse_routing_key_malformed(self):
        self.assertRaises(ValueError, signalling.parse_routing_key,
                          'log.warn.123.unexpected-part')

    def test_parse_routing_key_wrong_prefix(self):
        self.assertRaises(ValueError, signalling.parse_routing_key,
                          'aaa.warn.123')

    def test_parse_routing_key_job_id_not_integer(self):
        self.assertRaises(ValueError, signalling.parse_routing_key,
                          'log.warn.not-an-integer')

    def test_parse_routing_key_wrong_type(self):
        self.assertRaises(ValueError, signalling.parse_routing_key,
                          'log.not-a-valid-type.123')

    def test_parse_routing_key(self):
        job_id = 123
        type_ = 'warn'

        self.assertEqual((job_id, type_),
                         signalling.parse_routing_key(
                             'log.%s.%s' % (type_, job_id)))


class CollectorTestCase(unittest.TestCase):
    def test_collector_logs_messages(self):
        level = 'warn'

        with patch('openquake.signalling.Collector.run') as run:

            def run_(mc):
                class FakeMessage(object):
                    def __init__(self, body, routing_key):
                        self.body = body
                        self.delivery_info = {
                            'routing_key': routing_key}

                msg = FakeMessage('a msg',
                            signalling.generate_routing_key(123, level))
                mc.message_callback(msg)

            run.side_effect = run_

            class FakeLogger(object):
                def __init__(self):
                    self.logs = []

                def log(self, level, msg):
                    self.logs.append((level, msg))

            logger = FakeLogger()

            collector = signalling.Collector('*', logger)
            collector.run()

            self.assertEqual([(getattr(logging, level.upper()), 'a msg')],
                             logger.logs)
