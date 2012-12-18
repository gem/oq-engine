# coding=utf-8
# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import kombu
import unittest

from openquake.calculators import base

class ExchangeConnArgsTestCase(unittest.TestCase):

    def test_exchange_and_conn_args(self):
        expected_conn_args = {
            'password': 'guest', 'hostname': 'localhost', 'userid': 'guest',
            'virtual_host': '/',
            }

        exchange, conn_args = base.exchange_and_conn_args()

        self.assertEqual('oq.tasks', exchange.name)
        self.assertEqual('direct', exchange.type)

        self.assertEqual(expected_conn_args, conn_args)


class SignalTestCase(unittest.TestCase):

    def test_signal_task_complete(self):
        job_id = 7
        num_sources = 10

        def test_callback(body, message):
            self.assertEqual(dict(job_id=job_id, num_items=num_sources),
                body)
            message.ack()

        exchange, conn_args = base.exchange_and_conn_args()
        routing_key = base.ROUTING_KEY_FMT % dict(job_id=job_id)
        task_signal_queue = kombu.Queue(
            'tasks.job.%s' % job_id, exchange=exchange,
            routing_key=routing_key, durable=False, auto_delete=True)

        with kombu.BrokerConnection(**conn_args) as conn:
            task_signal_queue(conn.channel()).declare()
            with conn.Consumer(task_signal_queue,
                callbacks=[test_callback]):

                # send the signal:
                base.signal_task_complete(
                    job_id=job_id, num_items=num_sources)
                conn.drain_events()
