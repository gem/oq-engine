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

import unittest

from openquake import signalling


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
