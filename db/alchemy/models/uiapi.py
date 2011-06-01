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


import sqlalchemy as sa


metadata = sa.MetaData()


upload = sa.Table('upload', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('owner_id', sa.Integer, sa.ForeignKey("admin.owner.id"),
              nullable=False),
    sa.Column('description', sa.String, nullable=False, default=""),
    sa.Column('path', sa.String, nullable=False, unique=True),
    sa.Column(
        "status",sa.Enum("pending", "running", "failed", "succeeded",
                         native_enum=False),
        nullable=False, default="pending"),
    sa.Column('job_pid', sa.Integer, nullable=False, default=0),
    schema='uiapi'
)

oq_params = sa.Table('oq_params', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('job_type', sa.String, nullable=False),
    sa.Column('upload_id', sa.Integer, sa.ForeignKey("uiapi.upload.id"),
              nullable=False),
    sa.Column('region_grid_spacing', sa.Float, nullable=False),
    sa.Column('min_magnitude', sa.Float, nullable=False),
    sa.Column('component', sa.String, nullable=False),
    sa.Column('imt', sa.String, nullable=False),
    sa.Column('period', sa.Float),
    sa.Column('truncation_type', sa.String, nullable=False),
    sa.Column('truncation_level', sa.Float),
    sa.Column('reference_vs30_value', sa.Float, nullable=False),
    sa.Column('imls', sa.dialects.postgresql.ARRAY(float)),
    sa.Column('poes', sa.dialects.postgresql.ARRAY(float)),
    sa.Column('realizations', sa.Integer),
    sa.Column('histories', sa.Integer),
    sa.Column('gm_correlated', sa.Boolean),
    schema='uiapi'
)
