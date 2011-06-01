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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


metadata = sa.MetaData()


Base = declarative_base()


class Organization(Base):
    __tablename__ = 'organization'
    __table_args__ = {'schema':'admin'}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    address = sa.Column(sa.String)
    url = sa.Column(sa.String)
    users = relationship("OqUser", backref="organization")

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return(":organization: %s" % self.name)


class OqUser(Base):
    __tablename__ = 'oq_user'
    __table_args__ = {'schema':'admin'}
    id = sa.Column('id', sa.Integer, primary_key=True)
    user_name = sa.Column(sa.String, nullable=False)
    full_name = sa.Column(sa.String, nullable=False)
    organization_id = sa.Column(
        sa.Integer, sa.ForeignKey("admin.organization.id"), nullable=False)
    data_is_open = sa.Column(sa.Boolean, nullable=False)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return(":oq_user: %s" % self.user_name)
