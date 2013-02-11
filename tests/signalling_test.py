# -*- coding: utf-8 -*-

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

import unittest
import threading

import kombu
import kombu.entity
import kombu.messaging

from openquake.engine.utils import config
from openquake.engine import signalling


class AMQPMessageConsumerTestCase(unittest.TestCase):
    def setUp(self):
        cfg = config.get_section('amqp')
        self.connection = kombu.BrokerConnection(hostname=cfg.get('host'),
                                                 userid=cfg['user'],
                                                 password=cfg['password'],
                                                 virtual_host=cfg['vhost'])
        self.channel = self.connection.channel()
        self.exchange = kombu.entity.Exchange(cfg['exchange'], type='topic',
                                              channel=self.channel)
        self.producer = kombu.messaging.Producer(self.channel,
                                                 exchange=self.exchange,
                                                 serializer="json")

    def tearDown(self):
        self.channel.close()
        self.connection.close()

    def test_message_callback(self):
        messages = []
        timeouts = []

        class Consumer(signalling.AMQPMessageConsumer):
            def message_callback(self, payload, msg):
                messages.append((payload, msg))
                if len(messages) == 2:
                    raise StopIteration()

            def timeout_callback(self):
                timeouts.append(1)
                raise StopIteration()

        consumer = Consumer(routing_key='ROUTING.KEY.#', timeout=2)
        consumer_thread = threading.Thread(target=consumer.run)
        consumer_thread.start()

        self.producer.publish(['skip', 'this'], routing_key='ROUTING')
        self.producer.publish(['foo', 'bar'], routing_key='ROUTING.KEY')
        self.producer.publish({'bazquux': 42}, routing_key='ROUTING.KEY.ZZ')

        consumer_thread.join()
        self.assertFalse(timeouts)
        self.assertEqual(len(messages), 2)
        (p1, m1), (p2, m2) = messages

        self.assertEqual(p1, ["foo", "bar"])
        self.assertEqual(p2, {'bazquux': 42})
        self.assertEqual(m1.delivery_info['routing_key'], 'ROUTING.KEY')
        self.assertEqual(m2.delivery_info['routing_key'], 'ROUTING.KEY.ZZ')

    def test_timeot_callback(self):
        timeouts = []

        class Consumer(signalling.AMQPMessageConsumer):
            def timeout_callback(self):
                timeouts.append(1)
                if len(timeouts) == 2:
                    raise StopIteration()

        consumer = Consumer(routing_key='', timeout=0.2)
        consumer.run()

        self.assertEqual(len(timeouts), 2)
