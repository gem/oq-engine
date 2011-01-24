#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Eventually this will manage shared system state via kvs,
for now it's just global variables :)
"""

import cPickle

__all__ = ["memoize", "STATE"]

STATE = {}

# 
# def memoize(function, limit=None):
#     return function

def memoize(function, limit=None):
    """Decorator to memoize functions using global state"""
    if isinstance(function, int):
        def int_wrapper(func):
            """Wrapped method that will memoize its output"""
            return memoize(func, function)
        return int_wrapper

    _list = []
    def memoize_wrapper(*args, **kwargs):
        """Wrapped method that will memoize its output"""
        key = cPickle.dumps((args, kwargs))
        try:
            _list.append(_list.pop(_list.index(key)))
        except ValueError:
            STATE[key] = function(*args, **kwargs)
            _list.append(key)
            if limit is not None and len(_list) > limit:
                del STATE[_list.pop(0)]

        return STATE[key]

    memoize_wrapper._memoize_dict = STATE
    memoize_wrapper._memoize_list = _list
    memoize_wrapper._memoize_limit = limit
    memoize_wrapper._memoize_origfunc = function
    memoize_wrapper._func_name = function.func_name
    return memoize_wrapper
