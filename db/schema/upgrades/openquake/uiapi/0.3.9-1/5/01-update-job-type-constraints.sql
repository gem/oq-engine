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

-- Update the job type constraints in uiapi.oq_job and uiapi.oq_params
-- Basically, replace 'probabilistic' with 'event_based'

ALTER TABLE uiapi.oq_job DROP CONSTRAINT job_type_value;
ALTER TABLE uiapi.oq_job ADD CONSTRAINT job_type_value
        CHECK(job_type in ('classical', 'event_based', 'deterministic'));

COMMENT ON COLUMN uiapi.oq_job.job_type IS 'One of: classical, event_based or deterministic.';

ALTER TABLE uiapi.oq_params DROP CONSTRAINT job_type_value;
ALTER TABLE uiapi.oq_params ADD CONSTRAINT job_type_value
        CHECK(job_type in ('classical', 'event_based', 'deterministic'));

COMMENT ON COLUMN uiapi.oq_params.job_type IS 'One of: classical, event_based or deterministic.';
