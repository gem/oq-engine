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

-- Exposure model
ALTER TABLE oqmif.exposure_model ADD COLUMN owner_id INTEGER NOT NULL;
ALTER TABLE oqmif.exposure_model ADD COLUMN name VARCHAR NOT NULL;

ALTER TABLE oqmif.exposure_model ADD CONSTRAINT oqmif_exposure_model_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

COMMENT ON COLUMN oqmif.exposure_model.owner_id IS 'The foreign key to the user who owns the exposure model in question';
COMMENT ON COLUMN oqmif.exposure_model.name IS 'The exposure model name';
