#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Eventually this will manage shared system state via memcached,
for now it's just global variables :)
"""

import cPickle
import sys


__all__ = ["memoize", "STATE"]

STATE = {}

# 
# def memoize(function, limit=None):
#     return function

def memoize(function, limit=None):
    if isinstance(function, int):
        def memoize_wrapper(f):
            return memoize(f, function)

        return memoize_wrapper

    dict = {}
    list = []
    def memoize_wrapper(*args, **kwargs):
        key = cPickle.dumps((args, kwargs))
        try:
            list.append(list.pop(list.index(key)))
        except ValueError:
            STATE[key] = function(*args, **kwargs)
            list.append(key)
            if limit is not None and len(list) > limit:
                del STATE[list.pop(0)]

        return STATE[key]

    memoize_wrapper._memoize_dict = STATE
    memoize_wrapper._memoize_list = list
    memoize_wrapper._memoize_limit = limit
    memoize_wrapper._memoize_origfunc = function
    memoize_wrapper.func_name = function.func_name
    return memoize_wrapper
