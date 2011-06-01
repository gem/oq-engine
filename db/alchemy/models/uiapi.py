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


from sqlalchemy import *
from sqlalchemy.dialects import postgresql


metadata = MetaData()


organization = Table('organization', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable = False),
    Column('address', String),
    Column('url', String),
    schema='admin'
)

owner = Table('owner', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_name', String, nullable = False),
    Column('full_name', String, nullable = False),
    Column(
        'organization_id', Integer, ForeignKey("admin.organization.id"),
        nullable=False),
    Column('data_is_open', Boolean, nullable=False),
    schema='admin'
)

upload = Table('upload', metadata,
    Column('id', Integer, primary_key=True),
    Column('owner_id', Integer, ForeignKey("admin.owner.id"), nullable=False),
    Column('description', String, nullable = False, default=""),
    Column('path', String, nullable = False, unique=True),
    Column('status', String, nullable = False, default="pending"),
    Column('job_pid', Integer, nullable = False, default=0),
    schema='uiapi'
)

oq_params = Table('oq_params', metadata,
    Column('id', Integer, primary_key=True),
    Column('job_type', String, nullable = False),
    Column(
        'upload_id', Integer, ForeignKey("uiapi.upload.id"), nullable=False),
    Column('region_grid_spacing', Float, nullable = False),
    Column('min_magnitude', Float, nullable = False),
    Column('component', String, nullable = False),
    Column('imt', String, nullable = False),
    Column('period', Float),
    Column('truncation_type', String, nullable = False),
    Column('truncation_level', Float),
    Column('reference_vs30_value', Float, nullable = False),
    Column('imls', postgresql.ARRAY(float)),
    Column('poes', postgresql.ARRAY(float)),
    Column('realizations', Integer),
    Column('histories', Integer),
    Column('gm_correlated', Boolean),
    schema='uiapi'
)


