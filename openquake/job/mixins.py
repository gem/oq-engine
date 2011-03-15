#   Mixins from https://github.com/ChristopherMacGown/pynpoint
#   Copyright 2010 Christopher MacGown (http://github.com/ChristopherMacGown)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#   Modifications by Global Earthquake Model Foundation
#   Copyright 2010 Global Earthquake Model Foundation
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" Mixin class """

def loader(target, mixin):
    """ Load the mixin into the target's class """
    target.__class__.__bases__ += (mixin,)
    return target

def unloader(target, mixin):
    """ Unload the mixin from the target's class __bases__"""
    bases = list(target.__class__.__bases__)
    bases.remove(mixin)
    target.__class__.__bases__ = tuple(bases)


class Mixin:
    """ A callable that handles mixing behaviour into a target, and
    provides the opener api so we can use it with the python with 
    syntax.
    """
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
        """ Load a mixin, if it's a subclass, also load the proxied mixin"""
        if issubclass(self.mixin, Mixin):
            self._load_proxied_mixin()

        return loader(self.target, self.mixin)

    def _unload(self):
        """ Unload a mixin, if it's a subclass, also load the proxied mixin"""
        if issubclass(self.mixin, Mixin):
            self._unload_proxied_mixin()

        return unloader(self.target, self.mixin)

    def _load_proxied_mixin(self):
        """ Load the proxied mixin requested by the calculation mode """

        calc_mode = self.target[self.key]
        loader(self.target, self.mixin.mixins[calc_mode]['mixin'])

    def _unload_proxied_mixin(self):
        """ Unload the proxied mixin requested by the calculation mode """
        calc_mode = self.target[self.key]
        unloader(self.target, self.mixin.mixins[calc_mode]['mixin'])

    @classmethod
    def ordered_mixins(cls):
        """ Return a list of mixins sorted by the order value specified at 
        registration """

        return [(k, v['mixin'])
                 for (k, v)
                 in sorted(cls.mixins.items(), key=lambda x: x[1]['order'])]

    @classmethod
    def register(cls, key, mixin, order=0):
        """ Register a new mixin. We expect a string key, a class, and an 
        optional order. The order is really only optional in the mixin 
        proxies."""
        if not key in cls.mixins:
            cls.mixins[key] = {'mixin': mixin, 'order': order }
