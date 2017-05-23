# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2017, GEM Foundation
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER The software Hazard Modeller's Toolkit (openquake.hmtk) provided
# herein is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered
# as a separate entity. The software provided herein is designed and
# implemented by scientific staff. It is not developed to the design
# standards, nor subject to same level of critical review by
# professional software developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License  for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

import sys
import collections
import functools
from decorator import decorator


class CatalogueFunctionRegistry(collections.OrderedDict):
    """
    A collection of methods/functions working on catalogues.

    The registry also holds information about the type of the input arguments
    """

    def check_config(self, config, fields_spec):
        """
        Check that `config` has each field in `fields_spec` if a default
        has not been provided.
        """
        for field, type_info in fields_spec.items():
            has_default = not isinstance(type_info, type)
            if field not in config and not has_default:
                raise RuntimeError(
                    "Configuration not complete. %s missing" % field)

    def set_defaults(self, config, fields_spec):
        """
        Set default values got from `fields_spec` into the `config`
        dictionary
        """
        defaults = dict([(f, d)
                         for f, d in fields_spec.items()
                         if not isinstance(d, type)])
        for field, default_value in defaults.items():
            if field not in config:
                config[field] = default_value

    def add(self, method_name, completeness=False, **fields):
        """
        Class decorator.

        Decorate `method_name` by adding a call to `set_defaults` and
        `check_config`. Then, save into the registry a callable
        function with the same signature of the original method.

        :param str method_name:
            the method to decorate
        :param bool completeness:
            True if the method accepts in input an optional parameter
            for the completeness table
        :param fields:
            a dictionary of field spec corresponding to the
            keys expected to be present in the config dictionary
            for the decorated method, e.g.
            time_bin=numpy.float,
            b_value=1E-6
        """
        def class_decorator(class_obj):
            original_method = getattr(class_obj, method_name)
            if sys.version[0] == '2':  # Python 2
                original_method = original_method.im_func

            def caller(fn, obj, catalogue, config=None, *args, **kwargs):
                config = config or {}
                self.set_defaults(config, fields)
                self.check_config(config, fields)
                return fn(obj, catalogue, config, *args, **kwargs)
            new_method = decorator(caller, original_method)
            setattr(class_obj, method_name, new_method)
            instance = class_obj()
            func = functools.partial(new_method, instance)
            func.fields = fields
            func.model = instance
            func.completeness = completeness
            functools.update_wrapper(func, new_method)
            self[class_obj.__name__] = func
            return class_obj
        return class_decorator

    def add_function(self, completeness=False, **fields):
        """
        Function decorator.

        Decorate a function by adding a call to `set_defaults` and
        `check_config`. Then, save into the registry a callable
        function with the same signature of the original method

        :param fields:
            a dictionary of field spec, e.g.
            time_bin=numpy.float,
            b_value=1E-6
        """
        def dec(fn):
            if completeness:
                def fn_with_config_and_c(
                        catalogue, config, completeness_table=None):
                    return fn(catalogue, completeness_table, **config)
                fn_with_config = fn_with_config_and_c
            else:
                def fn_with_config_without_c(catalogue, config):
                    return fn(catalogue, **config)
                fn_with_config = fn_with_config_without_c
            fn_with_config.fields = fields
            fn_with_config.completeness = completeness
            fn.fields = fields
            self[fn.__name__] = fn_with_config
            return fn
        return dec
