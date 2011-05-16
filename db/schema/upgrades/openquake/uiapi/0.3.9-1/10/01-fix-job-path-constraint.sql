/*
    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License version 3
    only, as published by the Free Software Foundation.

    OpenQuake is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License version 3 for more details
    (a copy is included in the LICENSE file that accompanied this code).

    You should have received a copy of the GNU Lesser General Public License
    version 3 along with OpenQuake.  If not, see
    <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.
*/

-- The uiapi.oq_job.path column should be optional as long as the job has not
-- been started. This patch allows 'path' to be NULL if 'status' is 'pending'.

ALTER TABLE uiapi.oq_job DROP CONSTRAINT job_path_value;
ALTER TABLE uiapi.oq_job ADD CONSTRAINT job_path_value
    CHECK((status IN ('running', 'failed', 'succeeded') AND path IS NOT NULL)
          OR (status = 'pending'));
