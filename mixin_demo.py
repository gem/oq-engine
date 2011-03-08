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



import time


class Mixin(object):
    mixins = {}
    def __init__(self, target, mixin, key=""):
        self.key = key.upper() + "_CALCULATION_MODE"
        self.target = target
        self.mixin = mixin

    def __enter__(self):
        return self._load()

    def __exit__(self, *args):
        self._unload()

    def _load(self):
        if issubclass(self.mixin, type(self)):
            self._proxied_mixin()

        self.target.__class__.__bases__ += (self.mixin,)
        return self.target

    def _unload(self):
        bases = list(self.target.__class__.__bases__)
        bases.remove(self.mixin)
        self.target.__class__.__bases__ = tuple(bases)

    def _proxied_mixin(self):
        calculation_mode = self.target.params[self.key]
        self.mixin = self.mixin.mixins[calculation_mode]['mixin']

    @classmethod
    def ordered_mixins(cls):
        return [(k, v['mixin'])
                 for (k, v)
                 in sorted(cls.mixins.items(), key=lambda x: x[1]['order'])]

    @classmethod
    def register(cls, key, mixin, order=0):
        if not key in cls.mixins:
            cls.mixins[key] = {'mixin': mixin, 'order': order }

    @classmethod
    def unregister(cls, key):
        del mixins[key]


class ProxyMixin(Mixin):
    mixins = {}


class ProxiedMixin:
    @classmethod
    def execute(cls):
        print '    In Proxied Mixin'


class UnproxiedMixin:
    @classmethod
    def execute(cls):
        print '    In Unproxied Mixin'


class SomeClass(object):
    params = {"SOMEKEY_CALCULATION_MODE": "ProxiedMixin"}
    pass


Mixin.register("MixinProxy", ProxyMixin, order=1)
Mixin.register("UnproxiedMixin", UnproxiedMixin, order=2)

ProxyMixin.register("ProxiedMixin", ProxiedMixin)


some_object = SomeClass()
print "method resolution order: "
print some_object.__class__.__mro__
print "the execute method: "
try:
    some_object.execute()
except AttributeError, e:
    print e

for (key, mixin) in Mixin.ordered_mixins():
    print
    print "----"
    print
    time.sleep(1)
    print "key: %s" % key
    print "mixin: %s" % mixin
    with Mixin(some_object, mixin, key="SOMEKEY") as mixed_in: 
        print "method resolution order: " 
        print mixed_in.__class__.__mro__
        print "the execute method:" 
        mixed_in.execute()
