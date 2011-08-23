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

BEGIN;
CREATE LANGUAGE plpythonu;
CREATE OR REPLACE FUNCTION __temp_function_for_openquake_upgrade()
    RETURNS text
AS $$
  # get the output rows that need updating
  names = plpy.execute(
      "SELECT id, display_name"
      "    FROM uiapi.output"
      "    WHERE output_type = 'hazard_map'")
  # insert the new hazard_map row
  insert_map = plpy.prepare(
      "INSERT INTO uiapi.hazard_map"
      "        (output_id, poe, statistic_type, quantile)"
      "    VALUES"
      "        ($1, $2, $3, $4)"
      "    RETURNING id", ["int", "float", "text", "float"])
  # update hazard_map_data to point to the new hazard_map
  update_map_id = plpy.prepare(
      "UPDATE uiapi.hazard_map_data"
      "    SET hazard_map_id = $1"
      "    WHERE hazard_map_id = $2", ["int", "int"])

  # handles: hazardmap-0.01-mean.xml, hazardmap-0.01-quantile-0.5.xml
  for output in names:
      output_id = output['id']
      basename = output['display_name'].rsplit('.', 1)[0]
      parts = basename.split('-')

      assert len(parts) == 3 or len(parts) == 4
      assert parts[0] == 'hazardmap'

      poe = parts[1]
      stat_type = parts[2]
      if len(parts) == 4:
          quantile = parts[3]
      else:
          quantile = None

      map_id = plpy.execute(insert_map, [output_id, poe, stat_type, quantile])
      plpy.execute(update_map_id, [map_id[0]['id'], output_id])

  return
$$ LANGUAGE plpythonu;
SELECT __temp_function_for_openquake_upgrade();
DROP FUNCTION __temp_function_for_openquake_upgrade();
COMMIT;
