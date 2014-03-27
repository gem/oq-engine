# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


"""
Utility functions related to OpenQuake version information.
"""


from datetime import datetime
from datetime import timedelta


def info(version_data):
    """Return a string with the OpenQuake version infomation.

    Version info data set to -1 will be ignored and assumed to have value
    zero.
    Release dates that lie more than 30 days in the future are ignored.

    :param version_data: A 4-tuple of integers that are the major, minor and
        sprint number respectively. The last datum is the number of seconds
        since epoch and represents the release date.

    :returns: A string with human readable OpenQuake version information.
    """
    error = "The OpenQuake version is not available."
    if not isinstance(version_data, tuple) or len(version_data) != 4:
        return error

    data = []
    for datum in version_data:
        if not isinstance(datum, int):
            return error
        if datum < -1:
            return error
        data.append(str(datum if datum > 0 else 0))

    result = "OpenQuake version %s" % ".".join(data[:3])

    seconds_since_epoch = version_data[-1]

    # Our versioning start on the date below.
    start = int(datetime(year=2011, month=4, day=8).strftime("%s"))
    # The release date should not be more than 30 days in the future.
    end = int((datetime.today() + timedelta(days=30)).strftime("%s"))

    if end > seconds_since_epoch > start:
        release_date = datetime.utcfromtimestamp(
            seconds_since_epoch).isoformat()
        result += ", released %sZ" % release_date

    return result
