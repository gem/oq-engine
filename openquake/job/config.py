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

class Validator(object):

    def is_valid(self):
        raise NotImplementedError()

    def error_message(self):
        raise NotImplementedError()


class ValidatorSet(Validator):

    def __init__(self):
        super(ValidatorSet, self).__init__()

        self.validators = []
        self.error_messages = []

    def is_valid(self):
        result = True

        for validator in self.validators:
            if not validator.is_valid():
                self.error_messages.append(validator.error_message())
                result = False

        return result

    def error_message(self):
        return self.error_messages

    def append(self, validator):
        self.validators.append(validator)
