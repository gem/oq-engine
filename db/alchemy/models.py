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


import geoalchemy as ga
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class Organization(Base):
    __tablename__ = "organization"
    __table_args__ = {"schema": "admin"}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    address = sa.Column(sa.String)
    url = sa.Column(sa.String)
    users = relationship("OqUser", backref="organization")
    last_update = sa.Column(sa.DateTime, sa.FetchedValue())

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return(":organization: %s" % self.name)


class OqUser(Base):
    __tablename__ = "oq_user"
    __table_args__ = {"schema": "admin"}
    id = sa.Column('id', sa.Integer, primary_key=True)
    user_name = sa.Column(sa.String, nullable=False)
    full_name = sa.Column(sa.String, nullable=False)
    organization_id = sa.Column(
        sa.Integer, sa.ForeignKey("admin.organization.id"), nullable=False)
    data_is_open = sa.Column(sa.Boolean, nullable=False, default=True)
    last_update = sa.Column(sa.DateTime, sa.FetchedValue())

    def __init__(self, user_name):
        self.user_name = user_name

    def __repr__(self):
        return(":oq_user: %s" % self.user_name)


class Upload(Base):
    __tablename__ = "upload"
    __table_args__ = {"schema": "uiapi"}

    id = sa.Column(sa.Integer, primary_key=True)
    owner_id = sa.Column(sa.Integer, sa.ForeignKey("admin.oq_user.id"),
                          nullable=False)
    owner = relationship("OqUser")
    description = sa.Column(sa.String, nullable=False, default="")
    path = sa.Column(sa.String, nullable=False, unique=True)
    status = sa.Column(sa.Enum("pending", "running", "failed", "succeeded",
                               native_enum=False),
                       nullable=False, default="pending")
    job_pid = sa.Column(sa.Integer, nullable=False, default=0)
    last_update = sa.Column(sa.DateTime, sa.FetchedValue())

    def __repr__(self):
        return(":upload: %s" % self.path)


class OqParams(Base):
    __tablename__ = "oq_params"
    __table_args__ = {"schema": "uiapi"}

    id = sa.Column(sa.Integer, primary_key=True)
    job_type = sa.Column(sa.Enum("classical", "event_based", "deterministic",
                                 native_enum=False),
                         nullable=False, default="classical")
    upload_id = sa.Column(sa.Integer, sa.ForeignKey("uiapi.upload.id"),
                          nullable=False)
    upload = relationship("Upload")
    region_grid_spacing = sa.Column(sa.Float, nullable=False)
    min_magnitude = sa.Column(sa.Float)
    investigation_time = sa.Column(sa.Float)
    component = sa.Column(sa.Enum("average", "gmroti50", native_enum=False),
                          nullable=False)
    imt = sa.Column(sa.Enum("pga", "sa", "pgv", "pgd", native_enum=False),
                    nullable=False)
    period = sa.Column(sa.Float)
    truncation_type = sa.Column(sa.Enum("none", "onesided", "twosided",
                                        native_enum=False),
                                nullable=False)
    truncation_level = sa.Column(sa.Float, nullable=False, default=0.0)
    reference_vs30_value = sa.Column(sa.Float, nullable=False)
    imls = sa.Column(postgresql.ARRAY(sa.Float))
    poes = sa.Column(postgresql.ARRAY(sa.Float))
    realizations = sa.Column(sa.Integer)
    histories = sa.Column(sa.Integer)
    gm_correlated = sa.Column(sa.Boolean)
    region = ga.GeometryColumn(ga.Polygon(2))
    last_update = sa.Column(sa.DateTime, sa.FetchedValue())

    def __repr__(self):
        return(":params: %s (:upload: %s)" % (self.job_type, self.upload.id))


ga.GeometryDDL(OqParams.__table__)
