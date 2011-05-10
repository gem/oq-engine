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

-- Add a status to the uiapi.upload status table.

-- Rename the 'status_value' constraint in uiapi.oq_job first.
ALTER TABLE uiapi.oq_job DROP CONSTRAINT status_value;
ALTER TABLE uiapi.oq_job ADD CONSTRAINT job_status_value
        CHECK(status IN ('created', 'in-progress', 'failed', 'succeeded')),

-- Now add the status to the uiapi.upload table.
ALTER TABLE uiapi.upload ADD CONSTRAINT upload_status_value
        CHECK(status IN ('created', 'in-progress', 'failed', 'succeeded')),
