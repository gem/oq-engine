# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


"""
Utility functions of general interest.
"""

from collections import OrderedDict
import cPickle
import itertools
import pprint


def singleton(cls):
    """This class decorator facilitates the definition of singletons."""
    instances = {}

    def getinstance(*args, **kwargs):
        """
        Return an instance from the cache if present, create one otherwise.
        """
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return getinstance


# Memoize taken from the Python Cookbook that handles also unhashable types
class MemoizeMutable:
    """ This decorator enables method/function caching in memory """
    def __init__(self, fun):
        self.fun = fun
        self.memo = {}

    def __call__(self, *args, **kwds):
        key = cPickle.dumps(args, 1) + cPickle.dumps(kwds, 1)
        if not key in self.memo:
            self.memo[key] = self.fun(*args, **kwds)

        return self.memo[key]


def str2bool(value):
    """Convert a string representation of a boolean value to a bool."""
    return value.lower() in ("true", "yes", "t", "1")


# The module private variable below will be used to store the job ID.
_THE_JOB_ID = -1


def get_job_id():
    """Return the job ID."""
    return _THE_JOB_ID


def set_job_id(job_id):
    """Set the job ID."""
    global _THE_JOB_ID  # pylint: disable=W0603
    _THE_JOB_ID = job_id


def flag_set(section, setting):
    """True if the given setting is enabled in openquake.cfg

    :param string section: name of the configuration file section
    :param string setting: name of the configuration file setting

    :returns: True if the setting is enabled in openquake.cfg, False otherwise
    """
    from openquake.utils import config

    setting = config.get(section, setting)  # pylint: disable=W0404
    if setting is None:
        return False
    return str2bool(setting)


class AdHocObject(object):
    """Provides ad-hoc objects with a defined set of properties.

    These are underpinned by a `SortedDict` i.e. the properties appear
    in order which makes it easier to use them in tests for example.
    """

    def __init__(self, type_name, attrs, values=None, default=None):
        # Internal attribute data.
        self.__dict__["_ia_type_name"] = type_name
        if isinstance(attrs, basestring):
            attrs = [a.strip() for a in attrs.split(",")]
        self.__dict__["_ia_attrs"] = set(attrs)
        if values:
            self.__dict__["_ia_data"] = OrderedDict(zip(attrs, values))
        else:
            self.__dict__["_ia_data"] = OrderedDict(zip(attrs,
                                                    itertools.repeat(default)))

    def __getattr__(self, attr):
        """Access a property by name object-style."""
        if attr in self.__dict__["_ia_attrs"]:
            return self.__dict__["_ia_data"].get(attr)
        else:
            raise AttributeError("'AdHocObject' object has no attribute '%s'" %
                                 attr)

    def __setattr__(self, attr, value):
        """Set a property's value by name object-style."""
        if attr in self.__dict__["_ia_attrs"]:
            self.__dict__["_ia_data"][attr] = value
        else:
            raise AttributeError("'AdHocObject' object has no attribute '%s'" %
                                 attr)

    def __eq__(self, other):
        """True if the two data dictionaries are equal."""
        return  self.__dict__["_ia_data"] == other.__dict__["_ia_data"]

    def __ne__(self, other):
        """True if the two data dictionaries are *not* equal."""
        return  not(self == other)

    def __iter__(self):
        """Return a dict-style iterator."""
        return  self.__dict__["_ia_data"].iteritems()

    def __contains__(self, key):
        """True if object has a property called `key`."""
        return  key in self.__dict__["_ia_data"]

    def keys(self):
        """Return an ordered list of all property names."""
        return  self.__dict__["_ia_data"].keys()

    def values(self):
        """Return an ordered list of all property values."""
        return  self.__dict__["_ia_data"].values()

    def items(self):
        """Return an ordered list of all name/property pairs."""
        return  self.__dict__["_ia_data"].items()

    def get(self, key, default=None):
        """Access a property by name."""
        return  self.__dict__["_ia_data"].get(key, default)

    def __setitem__(self, key, value):
        """Set a property's value dict style."""
        setattr(self, key, value)

    def __str__(self):
        """Called by the str() built-in function and by the print statement."""
        return "%s, %s" % (self.__dict__["_ia_type_name"],
                           pprint.pformat(self.__dict__["_ia_data"].items()))

    def __repr__(self):
        """Called by the repr() built-in function and by string conversions."""
        return "AdHocObject('%s', %s, values=%s)" % (
            self.__dict__["_ia_type_name"],
            str(self.__dict__["_ia_data"].keys()),
            str(self.__dict__["_ia_data"].values()))
