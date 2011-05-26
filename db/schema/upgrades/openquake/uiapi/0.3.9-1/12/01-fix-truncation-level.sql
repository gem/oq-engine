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

-- Drop unneded column.
ALTER TABLE uiapi.output DROP COLUMN shapefile_url;

-- Make the 'truncation_level' column optional.
ALTER TABLE uiapi.oq_params ALTER COLUMN truncation_level DROP NOT NULL;
-- Add a constraint to govern when the 'truncation_level' column may be NULL.
ALTER TABLE uiapi.oq_params ADD CONSTRAINT truncation_level_is_set
CHECK(((truncation_type = 'none') AND (truncation_level IS NULL))
      OR ((truncation_type != 'none') AND (truncation_level IS NOT NULL)));
