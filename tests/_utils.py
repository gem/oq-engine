# Copyright (c) 2010-2012, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.


def deep_eq(a, b):
    """Deep compare two objects for equality by traversing __dict__s.

    :returns:
        True if the two objects are deeply equal, otherwise false.
    """
    try:
        _do_deep_eq(a, b)
    except AssertionError:
        return False
    return True


def _do_deep_eq(a, b):
    """Do the actual deep comparison. If two items up for comparison is not
    equal, a :exception:`ValueError` is raised (to :function:`_deep_eq`).
    """
    if isinstance(a, (list, tuple)):
        _test_seq(a, b)
    elif isinstance(a, dict):
        _test_dict(a, b)
    elif hasattr(a, '__dict__'):
        _test_dict(a.__dict__, b.__dict__)
    else:
        # must be a 'primitive'
        assert a == b


def _test_dict(a, b):
    """Compare `dict` types recursively."""
    assert len(a) == len(b)

    for key in a:
        left = a[key]
        right = b[key]

        if isinstance(left, (list, tuple)):
            _test_seq(left, right)
        elif isinstance(left, dict):
            _test_dict(left, right)
        elif hasattr(left, '__dict__'):
            assert left.__class__ == right.__class__
            _test_dict(left.__dict__, right.__dict__)
        else:
            # must be a 'primitive'
            assert left == right

def _test_seq(a, b):
    """Compare `list` or `tuple` types recursively."""
    assert len(a) == len(b)

    for i, item in enumerate(a):
        if isinstance(item, (list, tuple)):
            _test_seq(item, b[i])
        else:
            if hasattr(item, '__class__'):
                assert item.__class__ == b[i].__class__

            if hasattr(item, '__dict__'):
                _test_dict(item.__dict__, b[i].__dict__)
            else:
                assert item == b[i]
