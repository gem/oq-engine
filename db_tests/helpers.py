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


"""
Helper classes/functions needed across multiple database related unit tests.
"""


import os
import shutil
import tempfile

from db.alchemy.db_utils import Session
from db.alchemy.models import OqJob, OqParams, OqUser, Output, Upload
from tests.helpers import TestMixin


class DbTestMixin(TestMixin):
    """Mixin class with various helper methods."""

    def setup_upload(self, dbkey=None):
        """Create an upload with associated inputs.

        :param integer dbkey: if set use the upload record with given db key.
        :returns: a :py:class:`db.alchemy.models.Upload` instance
        """
        session = Session.get()
        if dbkey:
            upload = session.query(Upload).filter(Upload.id==dbkey).one()
            return upload

        user = session.query(OqUser).filter(OqUser.user_name=="openquake").one()
        upload = Upload(owner=user, path=tempfile.mkdtemp())
        session.add(upload)
        session.commit()
        return upload

    def teardown_upload(self, upload, filesystem_only=True):
        """
        Tear down the file system (and potentially db) artefacts for the
        given upload.

        :param upload: the :py:class:`db.alchemy.models.Upload` instance
            in question
        :param bool filesystem_only: if set the upload/input database records
            will be left intact. This saves time and the test db will be
            dropped/recreated prior to the next db test suite run anyway.
        """
        # This is like "rm -rf path"
        shutil.rmtree(upload.path, ignore_errors=True)
        if filesystem_only:
            return
        session = Session.get()
        session.delete(upload)
        session.commit()

    def setup_classic_job(self, create_job_path=True, upload_id=None):
        """Create a classic job with associated upload and inputs.

        :param integer upload_id: if set use upload record with given db key.
        :param bool create_job_path: if set the path for the job will be
            created and captured in the job record
        :returns: a :py:class:`db.alchemy.models.OqJob` instance
        """
        session = Session.get()
        upload = self.setup_upload(upload_id)
        oqp = OqParams()
        oqp.job_type = "classical"
        oqp.upload = upload
        oqp.region_grid_spacing = 0.01
        oqp.min_magnitude = 5.0
        oqp.investigation_time = 50.0
        oqp.component = "gmroti50"
        oqp.imt = "pga"
        oqp.truncation_type = "twosided"
        oqp.truncation_level = 3
        oqp.reference_vs30_value = 760
        oqp.imls = [
            0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376, 0.0527,
            0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556, 0.778]
        oqp.poes = [0.01, 0.10]
        oqp.realizations = 1
        oqp.region = (
            "POLYGON((-81.3 37.2, -80.63 38.04, -80.02 37.49, -81.3 37.2))")
        session.add(oqp)
        job = OqJob(oq_params=oqp, owner=upload.owner, job_type="classical")
        session.add(job)
        session.commit()
        if create_job_path:
            job.path = os.path.join(upload.path, str(job.id))
            session.add(job)
            session.commit()
            os.mkdir(job.path)
            os.chmod(job.path, 0777)
        return job

    def teardown_job(self, job, filesystem_only=True):
        """
        Tear down the file system (and potentially db) artefacts for the
        given job.

        :param job: the :py:class:`db.alchemy.models.OqJob` instance
            in question
        :param bool filesystem_only: if set the oq_job/oq_param/upload/input
            database records will be left intact. This saves time and the test
            db will be dropped/recreated prior to the next db test suite run
            anyway.
        """
        oqp = job.oq_params
        self.teardown_upload(oqp.upload, filesystem_only=filesystem_only)
        if filesystem_only:
            return
        session = Session.get()
        session.delete(job)
        session.delete(oqp)
        session.commit()

    def setup_output(self, job_to_use=None, output_type="hazard_map",
                     db_backed=True):
        """Create an output object of the given type.

        :param job_to_use: if set use the passed
            :py:class:`db.alchemy.models.OqJob` instance as opposed to
            creating a new one.
        :param str output_type: map type, one of "hazard_map", "loss_map"
        :param bool db_backed: initialize the property of the newly created
            :py:class:`db.alchemy.models.Output` instance with this value.
        :returns: a :py:class:`db.alchemy.models.Output` instance
        """
        job = job_to_use if job_to_use else self.setup_classic_job()
        output = Output(owner=job.owner, oq_job=job, output_type=output_type,
                        db_backed=db_backed)
        output.path = self.touch(
            dir=os.path.join(job.path, "computed_output"), suffix=".xml",
            prefix="hzrd." if output_type == "hazard_map" else "loss.")
        session = Session.get()
        session.add(output)
        session.commit()
        return output

    def generate_output_path(self, job, output_type="hazard_map"):
        """Return a random output path for the given job."""
        path = self.touch(
            dir=os.path.join(job.path, "computed_output"), suffix=".xml",
            prefix="hzrd." if output_type == "hazard_map" else "loss.")
        return path

    def teardown_output(self, output, teardown_job=True, filesystem_only=True):
        """
        Tear down the file system (and potentially db) artefacts for the
        given output.

        :param output: the :py:class:`db.alchemy.models.Output` instance
            in question
        :param bool teardown_job: the associated job and its related artefacts
            shall be torn down as well.
        :param bool filesystem_only: if set the various database records will
            be left intact. This saves time and the test db will be
            dropped/recreated prior to the next db test suite run anyway.
        """
        job = output.oq_job
        if not filesystem_only:
            session = Session.get()
            session.delete(output)
            session.commit()
        if teardown_job:
            self.teardown_job(job, filesystem_only=filesystem_only)
