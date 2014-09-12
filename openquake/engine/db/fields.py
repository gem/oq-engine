# Copyright (c) 2010-2014, GEM Foundation.
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

"""Custom Django field and formfield types (for models and forms."""

import ast

import numpy
import re
import zlib
import json
import cPickle as pickle

from django.utils.encoding import smart_unicode
from django.contrib.gis import forms
from django.contrib.gis.db import models as djm

#: regex for splitting string lists on whitespace and/or commas
ARRAY_RE = re.compile(r'[\s,]+')

# Disable pylint for 'Too many public methods'
# pylint: disable=R0904


class StringArrayFormField(forms.Field):
    """
    Base class containing general functionality for handling list-like
    parameters.
    """
    # No change; customize this in subclasses if a cast is needed (to `float`,
    # for example)
    cast = str
    value_type = 'str'

    # Disable pylint for 'Method could be a function'
    # pylint: disable=R0201
    def clean(self, value):
        """Try to coerce either a string list of values (separated by
        whitespace and/or commas or a list/tuple of values to a list of
        floats. If unsuccessful, raise a
        :exc:`django.forms.ValidationError`
        """
        if value is None:
            return None

        if isinstance(value, (tuple, list)):
            try:
                value = [self.cast(x) for x in value]
            except (TypeError, ValueError):
                raise forms.ValidationError(
                    'Could not coerce sequence values to `float` values'
                )
        elif isinstance(value, str):
            # it could be a string list, like this: "1, 2,3 , 4 5"
            # try to convert it to a an actual list and cast the values to the
            # chosen type
            if len(value) == 0:
                # It's an empty string list
                value = []
            else:
                try:
                    value = [self.cast(x) for x in ARRAY_RE.split(value)]
                except ValueError:
                    raise forms.ValidationError(
                        'Could not coerce `str` to a list of `%s` values'
                        % self.value_type
                    )
        else:
            raise forms.ValidationError(
                'Could not convert value to `list` of `%s` values: %s'
                % (self.value_type, value)
            )
        return value


class FloatArrayFormField(StringArrayFormField):
    """Form field for properly handling float arrays/lists."""

    cast = float
    value_type = 'float'


class PickleFormField(forms.Field):
    """Form field for Python objects which are pickle and saved to the
    database."""

    def clean(self, value):
        """We assume that the Python value specified for this field is exactly
        what we want to pickle and save to the database.

        The value will not modified.
        """
        return value


class FloatArrayField(djm.Field):
    """This field models a postgres `float` array."""

    def db_type(self, connection):
        return 'float[]'

    def get_prep_value(self, value):
        if value is None:
            return None

        # Normally, the value passed in here will be a list.
        # It could also be a string list, each value separated by
        # comma/whitespace.
        if isinstance(value, str):
            if len(value) == 0:
                # It's an empty string list
                value = []
            else:
                # try to coerce the string to a list of floats
                value = [float(x) for x in ARRAY_RE.split(value)]
                # If there's an exception here, just let it be raised.
        return "{" + ', '.join(str(v) for v in value) + "}"

    def formfield(self, **kwargs):
        """Specify a custom form field type so forms know how to handle fields
        of this type.
        """
        defaults = {'form_class': FloatArrayFormField}
        defaults.update(kwargs)
        return super(FloatArrayField, self).formfield(**defaults)


class IntArrayField(djm.Field):
    """This field models a postgresql `int` array"""

    # TODO(lp) implement the corresponding form field
    def db_type(self, connection):
        return 'int[]'

    def get_prep_value(self, value):
        if value is None:
            return
        return "{%s}" % ','.join(str(v) for v in value)


class CharArrayField(djm.Field):
    """This field models a postgres `varchar` array."""

    def db_type(self, _connection=None):
        return 'varchar[]'

    def to_python(self, value):
        """
        Split strings on whitespace or commas and return the list.

        If the input ``value`` is not a string, just return the value (for
        example, if ``value`` is already a list).
        """
        if isinstance(value, basestring):
            return list(ARRAY_RE.split(value))

        return value

    def get_prep_value(self, value):
        """Return data in a format that has been prepared for use as a
        parameter in a query.

        :param value: sequence of string values to be saved in a varchar[]
            field
        :type value: list or tuple

        >>> caf = CharArrayField()
        >>> caf.get_prep_value(['foo', 'bar', 'baz123'])
        '{"foo", "bar", "baz123"}'
        """
        if value is None:
            return None

        # Normally, the value passed in here will be a list.
        # It could also be a string list, each value separated by
        # comma/whitespace.
        if isinstance(value, str):
            if len(value) == 0:
                # It's an empty string list
                value = []
            else:
                # try to coerce the string to a list of strings
                value = list(ARRAY_RE.split(value))
        return '{' + ', '.join('"%s"' % str(v) for v in value) + '}'

    def formfield(self, **kwargs):
        """
        Specify a custom form field type so forms know how to handle fields of
        this type.
        """
        defaults = {'form_class': StringArrayFormField}
        defaults.update(kwargs)
        return super(CharArrayField, self).formfield(**defaults)


class LiteralField(djm.Field):
    """
    Convert from Postgres TEXT to Python objects and viceversa by using
    `ast.literal_eval` and `repr`.
    """

    __metaclass__ = djm.SubfieldBase

    def db_type(self, _connection=None):
        return 'text'

    def to_python(self, value):
        if value is not None:
            return ast.literal_eval(value)

    def get_prep_value(self, value):
        return repr(value)


class PickleField(djm.Field):
    """Field for transparent pickling and unpickling of python objects."""

    __metaclass__ = djm.SubfieldBase

    SUPPORTED_BACKENDS = set((
        'django.contrib.gis.db.backends.postgis',
        'django.db.backends.postgresql_psycopg2'
    ))

    def db_type(self, connection):
        """Return "bytea" as postgres' column type."""
        assert connection.settings_dict['ENGINE'] in self.SUPPORTED_BACKENDS
        return 'bytea'

    def to_python(self, value):
        """Unpickle the value."""
        if isinstance(value, (buffer, str, bytearray)) and value:
            return pickle.loads(str(value))
        else:
            return value

    def get_prep_value(self, value):
        """Pickle the value."""
        return bytearray(pickle.dumps(value, pickle.HIGHEST_PROTOCOL))

    def formfield(self, **kwargs):
        """Specify a custom form field type so forms don't treat this as a
        default type (such as a string). Any Python object is valid for this
        field type.
        """
        defaults = {'form_class': PickleFormField}
        defaults.update(kwargs)
        return super(PickleField, self).formfield(**defaults)


class GzippedField(djm.Field):
    """
    Automatically stores gzipped text as a bytearray
    """
    __metaclass__ = djm.SubfieldBase

    def db_type(self, _connection):
        return 'bytea'

    def get_prep_value(self, value):
        """Compress the value"""
        return bytearray(zlib.compress(value))

    def to_python(self, value):
        """Decompress the value"""
        return zlib.decompress(value)


class DictField(PickleField):
    """Field for storing Python `dict` objects (or a JSON text representation.
    """

    def to_python(self, value):
        """The value of a DictField can obviously be a `dict`. The value can
        also be specified as a JSON string. If it is, convert it to a `dict`.
        """
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                # This string is not JSON.
                value = super(DictField, self).to_python(value)
        else:
            value = super(DictField, self).to_python(value)

        return value


class NumpyListField(PickleField):
    """
    Field for storing numpy arrays as pickled blobs. The actual blob stored in
    the database is simply a pickled `list`. When the field is instantiated,
    the value is converted back to a numpy array.
    """

    def to_python(self, value):
        """
        Try to reconstruct a `numpy.ndarray` from the given ``value``.

        :param value:
            The pickled representation of an object which can be reconstituted
            using `pickle.loads`.
        """
        if value is None:
            return None

        # first, unpickle:
        value = super(NumpyListField, self).to_python(value)
        if isinstance(value, (list, tuple, numpy.ndarray)):
            return numpy.array(value)

        # NOTE: If the value is not a list or tuple, raise an exception.
        # The reason we do this is because this field type is intended to be
        # used only for storing list-like data. (Technically any object can be
        # wrapped in a numpy array, like `numpy.array(object())`, but this is
        # not our use case.
        raise ValueError(
            "Unexpected value of type '%s'. Expected 'list' or 'tuple'."
            % type(value)
        )

    def get_prep_value(self, value):
        """
        Convert the ``value`` to the pickled representation of a `list`. If
        ``value`` is a `numpy.ndarray`, it will be converted to a list of the
        same size and shape before being pickled.

        :param value:
            A `list`, `tuple`, or `numpy.ndarray`.
        """
        # convert to list first before pickling, if it's a numpy array
        if isinstance(value, numpy.ndarray):
            return super(NumpyListField, self).get_prep_value(value.tolist())
        else:
            if not isinstance(value, (list, tuple)):
                raise ValueError(
                    "Unexpected value of type '%s'. Expected 'list', 'tuple', "
                    "or 'numpy.ndarray'"
                    % type(value)
                )


class OqNullBooleanField(djm.NullBooleanField):
    """
    A `NullBooleanField` that can convert meaningful strings to boolean
    values (in the case of config file parameters).
    """

    def to_python(self, value):
        """
        If ``value`` is a `str`, try to extract some boolean value from it.
        """
        if isinstance(value, str):
            if value.lower() in ('t', 'true', 'y', 'yes'):
                value = True
            elif value.lower() in ('f', 'false', 'n', 'no'):
                value = False
        # otherwise, it will just get cast to a bool, which could produce some
        # strange results
        value = super(OqNullBooleanField, self).to_python(value)
        return value


class NullFloatField(djm.FloatField):
    """
    A nullable float field that handles blank input values properly.
    """

    def get_prep_value(self, value):
        if isinstance(value, basestring):
            if value.strip():
                return super(NullFloatField, self).get_prep_value(value)
            else:
                return None
        else:
            return value


class NullTextField(djm.TextField):
    def __init__(self, **kwargs):
        kwargs.update(dict(blank=True, null=True))
        super(NullTextField, self).__init__(**kwargs)

    def formfield(self, **kwargs):
        """
        Specify a custom form field type so forms know how to handle fields of
        this type.
        """
        defaults = {'form_class': NullCharField}
        defaults.update(kwargs)
        return super(NullTextField, self).formfield(**defaults)


class NullCharField(forms.CharField):
    def to_python(self, value):
        "Returns a Unicode object."
        if value is None:
            return None
        else:
            return smart_unicode(value)
