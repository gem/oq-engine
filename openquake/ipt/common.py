# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2019 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
from os.path import basename
from django.conf import settings
from openquakeplatform.python3compat import encode


def bool2s(v):
    return "True" if v else "False"


def get_tmp_path(userid):
    tmp_path = os.path.normpath(os.path.join(
        settings.FILE_PATH_FIELD_DIRECTORY, userid, 'tmp'))
    if os.path.exists(tmp_path):
        if os.path.isfile(tmp_path):
            raise IOError('[%s] is not a directory' % tmp_path)
    else:
        os.makedirs(tmp_path)
    return tmp_path


def get_full_path(userid, namespace, subdir_and_filename=""):
    return os.path.normpath(os.path.join(settings.FILE_PATH_FIELD_DIRECTORY,
                            userid, namespace, subdir_and_filename))


def zwrite_or_collect(z, userid, namespace, fname, file_collect):
    """
    If z is None add ("file", basename, pathname) to a list,
    else append the file to the zip object
    """
    bname = basename(fname)
    if z is None:
        for item in file_collect:
            if item[1] == bname:
                raise ValueError(
                    'File "{bname}" already exists.'
                    ' Upload it again with a different name.')
        file_collect.append(["file", bname, fname])
    else:
        for item_name in z.namelist():
            if item_name == bname:
                raise ValueError(
                    f'File "{bname}" already exists.'
                    ' Upload it again with a different name.')
        z.write(get_full_path(userid, namespace, fname), bname)


def zwrite_or_collect_str(z, fname, content, file_collect):
    if z is None:
        file_collect.append(["string", fname, content])
    else:
        z.writestr(fname, encode(content))
