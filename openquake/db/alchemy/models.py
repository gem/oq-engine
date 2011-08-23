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
        return(":organization: %s, %s" % (self.id, self.name))


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
        return(":oq_user: %s, %s" % (self.id, self.user_name))


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
        return(":upload: %s, %s" % (self.id, self.path))


class OqParams(Base):
    __tablename__ = "oq_params"
    __table_args__ = {"schema": "uiapi"}

    id = sa.Column(sa.Integer, primary_key=True)
    job_type = sa.Column(sa.Enum("classical", "event_based", "deterministic",
                                 native_enum=False),
                         nullable=False, default="classical")
    upload_id = sa.Column(sa.Integer, sa.ForeignKey("uiapi.upload.id"))
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
    truncation_level = sa.Column(sa.Float, nullable=False, default=3.0)
    reference_vs30_value = sa.Column(sa.Float, nullable=False)
    imls = sa.Column(postgresql.ARRAY(sa.Float),
                     doc="Intensity measure levels")
    poes = sa.Column(postgresql.ARRAY(sa.Float),
                     doc="Probabilities of exceedence")
    realizations = sa.Column(sa.Integer, doc="Number of logic tree samples")
    histories = sa.Column(sa.Integer, doc="Number of seismicity histories")
    gm_correlated = sa.Column(sa.Boolean, doc="Ground motion correlation flag")
    region = ga.GeometryColumn(ga.Polygon(2), nullable=False)
    last_update = sa.Column(sa.DateTime, sa.FetchedValue())

    def __repr__(self):
        return(":params: %s, %s (:upload: %s)" % (
            self.id, self.job_type, self.upload.id))


class OqJob(Base):
    __tablename__ = "oq_job"
    __table_args__ = {"schema": "uiapi"}

    id = sa.Column(sa.Integer, primary_key=True)
    owner_id = sa.Column(sa.Integer, sa.ForeignKey("admin.oq_user.id"),
                          nullable=False)
    owner = relationship("OqUser")
    job_type = sa.Column(sa.Enum("classical", "event_based", "deterministic",
                                 native_enum=False),
                         nullable=False, default="classical")
    description = sa.Column(sa.String, nullable=False, default="")
    path = sa.Column(sa.String, nullable=False, unique=True)
    status = sa.Column(sa.Enum("pending", "running", "failed", "succeeded",
                               native_enum=False),
                       nullable=False, default="pending")
    duration = sa.Column(sa.Integer, nullable=False, default=0)
    job_pid = sa.Column(sa.Integer, nullable=False, default=0)
    supervisor_pid = sa.Column(sa.Integer, nullable=False, default=0)
    oq_params_id = sa.Column(sa.Integer, sa.ForeignKey("uiapi.oq_params.id"),
                             nullable=False)
    oq_params = relationship("OqParams")
    last_update = sa.Column(sa.DateTime, sa.FetchedValue())

    def __repr__(self):
        return(":job: %s, %s, %s (:params: %s)" % (
            self.id, self.job_type, self.path, self.oq_params.id))


class Output(Base):
    __tablename__ = "output"
    __table_args__ = {"schema": "uiapi"}

    id = sa.Column(sa.Integer, primary_key=True)
    owner_id = sa.Column(sa.Integer, sa.ForeignKey("admin.oq_user.id"),
                          nullable=False)
    owner = relationship("OqUser")
    oq_job_id = sa.Column(sa.Integer, sa.ForeignKey("uiapi.oq_job.id"),
                             nullable=False)
    oq_job = relationship("OqJob", backref="output_set")
    path = sa.Column(sa.String, unique=True)
    display_name = sa.Column(sa.String, nullable=False)
    db_backed = sa.Column(sa.Boolean, nullable=False, default=False)
    output_type = sa.Column(
        sa.Enum("unknown", "hazard_curve", "hazard_map", "loss_curve",
                "loss_map", native_enum=False), nullable=False)
    size = sa.Column(sa.Integer, nullable=False, default=0)
    shapefile_path = sa.Column(sa.String)
    min_value = sa.Column(sa.Float)
    max_value = sa.Column(sa.Float)
    last_update = sa.Column(sa.DateTime, sa.FetchedValue())

    def __repr__(self):
        return(":output: %s, %s, %s, %s" % (
            self.id, self.output_type, self.path, self.size))


class HazardMap(Base):
    __tablename__ = "hazard_map"
    __table_args__ = {"schema": "hzrdr"}

    id = sa.Column(sa.Integer, primary_key=True)
    output_id = sa.Column(sa.Integer, sa.ForeignKey("uiapi.output.id"),
                          nullable=False)
    output = relationship("Output", backref="hazardmap_set")
    poe = sa.Column(sa.Float, nullable=False)
    statistic_type = sa.Column(
        sa.Enum("mean", "quantile", native_enum=False))
    quantile = sa.Column(sa.Float)

    def __repr__(self):
        return(":hazard_map: %s, %s" % (
            self.id, self.poe))


class HazardMapData(Base):
    __tablename__ = "hazard_map_data"
    __table_args__ = {"schema": "hzrdr"}

    id = sa.Column(sa.Integer, primary_key=True)
    hazard_map_id = sa.Column(sa.Integer, sa.ForeignKey("hzrdr.hazard_map.id"),
                              nullable=False)
    hazard_map = relationship("HazardMap", backref="hazardmapdata_set")
    location = ga.GeometryColumn(ga.Point(2), nullable=False)
    value = sa.Column(sa.Float, nullable=False)

    def __repr__(self):
        return(":hazard_map_data: %s, %s" % (
            self.id, self.value))


class HazardCurve(Base):
    __tablename__ = "hazard_curve"
    __table_args__ = {"schema": "hzrdr"}

    id = sa.Column(sa.Integer, primary_key=True)
    output_id = sa.Column(sa.Integer, sa.ForeignKey("uiapi.output.id"),
                          nullable=False)
    output = relationship("Output", backref="hazardcurve_set")
    end_branch_label = sa.Column(sa.String)
    statistic_type = sa.Column(
        sa.Enum("mean", "median", "quantile", native_enum=False))
    quantile = sa.Column(sa.Float)

    def __repr__(self):
        return(":hazard_curve: %s, %s" % (
            self.id, self.statistic_type or self.end_branch_label))


class HazardCurveData(Base):
    __tablename__ = "hazard_curve_data"
    __table_args__ = {"schema": "hzrdr"}

    id = sa.Column(sa.Integer, primary_key=True)
    hazard_curve_id = sa.Column(
        sa.Integer, sa.ForeignKey("hzrdr.hazard_curve.id"),
        nullable=False)
    hazard_curve = relationship("HazardCurve",
                                backref="hazardcurvedata_set")
    poes = sa.Column(postgresql.ARRAY(sa.Float), nullable=False,
                     doc="Probabilities of exceedence")
    location = ga.GeometryColumn(ga.Point(2), nullable=False)

    def __repr__(self):
        return(":hazard_curve_data: %s, %s" % (
            self.id, self.poes))


class GMFData(Base):
    __tablename__ = "gmf_data"
    __table_args__ = {"schema": "hzrdr"}

    id = sa.Column(sa.Integer, primary_key=True)
    output_id = sa.Column(sa.Integer, sa.ForeignKey("uiapi.output.id"),
                          nullable=False)
    output = relationship("Output", backref="gmfdata_set")
    location = ga.GeometryColumn(ga.Point(2), nullable=False)
    ground_motion = sa.Column(sa.Float)

    def __repr__(self):
        return(":hgmf_data: %s, %s, %s" % (
            self.id, self.location, self.ground_motion))


class LossMap(Base):
    __tablename__ = "loss_map"
    __table_args__ = {"schema": "riskr"}

    id = sa.Column(sa.Integer, primary_key=True)

    output_id = sa.Column(sa.Integer, sa.ForeignKey("uiapi.output.id"),
                          nullable=False)
    output = relationship("Output", backref="lossmap_set")

    deterministic = sa.Column(sa.Boolean, nullable=False)
    loss_map_ref = sa.Column(sa.String, nullable=True)
    end_branch_label = sa.Column(sa.String, nullable=True)
    category = sa.Column(sa.String, nullable=True)
    unit = sa.Column(sa.String, nullable=True)
    poe = sa.Column(sa.Float, nullable=True)

    def __repr__(self):
        return(":loss_map: %s" % self.id)


class LossMapData(Base):
    __tablename__ = "loss_map_data"
    __table_args__ = {"schema": "riskr"}

    id = sa.Column(sa.Integer, primary_key=True)

    loss_map_id = sa.Column(sa.Integer,
                            sa.ForeignKey("riskr.loss_map.id"),
                            nullable=False)
    loss_map = relationship("LossMap",
                            backref="lossmapdata_set")

    asset_ref = sa.Column(sa.String, nullable=False)
    location = ga.GeometryColumn(ga.Point(2), nullable=False)
    value = sa.Column(sa.Float, nullable=False)
    std_dev = sa.Column(sa.Float, nullable=False, default=0.0)

    def __repr__(self):
        return(":loss_map_data: %s" % self.id)


class LossCurve(Base):
    __tablename__ = "loss_curve"
    __table_args__ = {"schema": "riskr"}

    id = sa.Column(sa.Integer, primary_key=True)
    output_id = sa.Column(sa.Integer, sa.ForeignKey("uiapi.output.id"),
                          nullable=False)
    output = relationship("Output", backref="losscurve_set")

    end_branch_label = sa.Column(sa.String)
    category = sa.Column(sa.String)
    unit = sa.Column(sa.String)

    def __repr__(self):
        return ":loss_curve: %s" % self.id


class LossCurveData(Base):
    __tablename__ = "loss_curve_data"
    __table_args__ = {"schema": "riskr"}

    id = sa.Column(sa.Integer, primary_key=True)
    loss_curve_id = sa.Column(sa.Integer,
                              sa.ForeignKey("riskr.loss_curve.id"),
                              nullable=False)
    loss_curve = relationship("LossCurve", backref="losscurvedata_set")

    location = ga.GeometryColumn(ga.Point(2), nullable=False)
    asset_ref = sa.Column(sa.String, nullable=False)
    losses = sa.Column(postgresql.ARRAY(sa.Float), nullable=False)
    poes = sa.Column(postgresql.ARRAY(sa.Float), nullable=False,
                     doc="Probabilities of exceedence")

    def __repr__(self):
        return(":loss_curve_data: %s" % self.id)
