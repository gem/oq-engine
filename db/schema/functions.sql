/*
  OpenQuake database schema definitions.

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


-- Copied from launchpad
CREATE OR REPLACE FUNCTION null_count(p_values anyarray) RETURNS integer
LANGUAGE plpgsql IMMUTABLE RETURNS NULL ON NULL INPUT AS
$$
DECLARE
    v_index integer;
    v_null_count integer := 0;
BEGIN
    FOR v_index IN array_lower(p_values,1)..array_upper(p_values,1) LOOP
        IF p_values[v_index] IS NULL THEN
            v_null_count := v_null_count + 1;
        END IF;
    END LOOP;
    RETURN v_null_count;
END;
$$;

COMMENT ON FUNCTION null_count(anyarray) IS
'Return the number of NULLs in the first row of the given array.';
