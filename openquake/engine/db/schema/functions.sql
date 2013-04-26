/*
  Copyright (c) 2010-2013, GEM Foundation.

  OpenQuake is free software: you can redistribute it and/or modify it
  under the terms of the GNU Affero General Public License as published
  by the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  OpenQuake is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU Affero General Public License
  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
*/


CREATE OR REPLACE FUNCTION format_exc(operation TEXT, error TEXT, tab_name TEXT) RETURNS TEXT AS $$
BEGIN
    RETURN operation || ': error: ' || error || ' (' || tab_name || ')';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION refresh_last_update() RETURNS TRIGGER
LANGUAGE plpgsql AS
$$
DECLARE
BEGIN
    NEW.last_update := timezone('UTC'::text, now());
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION refresh_last_update() IS
'Refresh the ''last_update'' time stamp whenever a row is updated.';


CREATE OR REPLACE FUNCTION pcheck_exposure_model()
  RETURNS TRIGGER
AS $$
    NEW = TD["new"] # new data resulting from insert or update

    def fmt(err):
        return "%s (%s)" % (err, TD["table_name"])

    def check_xor(a, b):
        """Raise exception if only one of the items is defined."""
        if not ((NEW[a] and NEW[b]) or (not NEW[a] and not NEW[b])):
            raise Exception(fmt("%s (%s) and %s (%s) must both be either "
                                "defined or undefined" %
                                (a, NEW[a], b, NEW[b])))

    if NEW["area_type"] is None:
        violations = []
        for key in ["coco_type", "reco_type", "stco_type"]:
            if NEW.get(key) is not None and NEW[key] == "per_area":
                violations.append((key, NEW[key]))
        if violations:
            raise Exception(fmt("area_type is mandatory for <%s>" %
                                ", ".join("%s=%s" % v for v in violations)))

    if NEW["area_unit"] is None:
        violations = []
        for key in ["coco_type", "reco_type", "stco_type"]:
            if NEW.get(key) is not None and NEW[key] == "per_area":
                violations.append((key, NEW[key]))
        if violations:
            raise Exception(fmt("area_unit is mandatory for <%s>" %
                                ", ".join("%s=%s" % v for v in violations)))

    check_xor("coco_unit", "coco_type")
    check_xor("reco_unit", "reco_type")
    check_xor("stco_unit", "stco_type")
    if NEW["stco_type"] is None and NEW["category"] != "population":
        raise Exception(fmt("structural cost type is mandatory for "
                            "<category=%s>" % NEW["category"]))
    return "OK"
$$ LANGUAGE plpythonu;


COMMENT ON FUNCTION pcheck_exposure_model() IS
'Make sure the inserted or modified exposure model record is consistent.';


CREATE OR REPLACE FUNCTION pcheck_exposure_data()
  RETURNS TRIGGER
AS $$
    def fmt(err):
        return "%s (%s)" % (err, TD["table_name"])

    NEW = TD["new"] # new data resulting from insert or update

    # get the associated exposure model record
    q = ("SELECT * FROM riski.exposure_model WHERE id = %s" %
         NEW["exposure_model_id"])
    [emdl] = plpy.execute(q)

    if NEW["stco"] is None and emdl["category"] != "population":
        raise Exception(fmt("structural cost is mandatory for category <%s>" %
                            emdl["category"]))

    if NEW["number_of_units"] is None:
        violations = []
        if emdl["category"] == "population":
            violations.append(("category", "population"))
        for key in ["coco_type", "reco_type", "stco_type"]:
            if emdl.get(key) is None or emdl[key] == "aggregated":
                continue
            if (emdl[key] == "per_asset" or (emdl[key] == "per_area" and
                emdl["area_type"] == "per_asset")):
                violations.append((key, emdl[key]))
        if violations:
            raise Exception(fmt("number_of_units is mandatory for <%s>" %
                                ", ".join("%s=%s" % v for v in violations)))

    if NEW["area"] is None:
        violations = []
        for key in ["coco_type", "reco_type", "stco_type"]:
            if emdl.get(key) is not None and emdl[key] == "per_area":
                violations.append((key, emdl[key]))
        if violations:
            raise Exception(fmt("area is mandatory for <%s>" %
                                ", ".join("%s=%s" % v for v in violations)))
    if NEW["coco"] is None and emdl["coco_type"] is not None:
        raise Exception(fmt("contents cost is mandatory for <coco_type=%s>"
                            % emdl["coco_type"]))
    if NEW["reco"] is None and emdl["reco_type"] is not None:
        raise Exception(fmt("retrofitting cost is mandatory for <reco_type=%s>"
                            % emdl["reco_type"]))
    if NEW["stco"] is None and emdl["stco_type"] is not None:
        raise Exception(fmt("structural cost is mandatory for <stco_type=%s>"
                            % emdl["stco_type"]))


    return "OK"
$$ LANGUAGE plpythonu;


COMMENT ON FUNCTION pcheck_exposure_data() IS
'Make sure the inserted or modified exposure data is consistent.';


CREATE OR REPLACE FUNCTION uiapi.pcount_cnode_failures()
  RETURNS TRIGGER
AS $$
    from datetime import datetime

    OLD = TD["old"]
    NEW = TD["new"]

    if NEW["current_status"] != OLD["current_status"]:
        NEW["current_ts"] = datetime.utcnow()
        NEW["previous_ts"] = OLD["current_ts"]
        result = "MODIFY"

        if NEW["current_status"] == "down":
            # state transition: up -> down
            NEW["failures"] += 1
    else:
        result = "OK"

    return result
$$ LANGUAGE plpythonu;


COMMENT ON FUNCTION uiapi.pcount_cnode_failures() IS
'Update the failure count for the compute node at hand as needed.';


CREATE AGGREGATE array_concat(anyarray)(sfunc=array_cat, stype=anyarray, initcond='{}');


CREATE TRIGGER uiapi_cnode_stats_before_update_trig
BEFORE UPDATE ON uiapi.cnode_stats
FOR EACH ROW EXECUTE PROCEDURE uiapi.pcount_cnode_failures();

CREATE TRIGGER riski_exposure_model_before_insert_update_trig
BEFORE INSERT ON riski.exposure_model
FOR EACH ROW EXECUTE PROCEDURE pcheck_exposure_model();

CREATE TRIGGER riski_exposure_data_before_insert_update_trig
BEFORE INSERT ON riski.exposure_data
FOR EACH ROW EXECUTE PROCEDURE pcheck_exposure_data();

CREATE TRIGGER admin_organization_refresh_last_update_trig BEFORE UPDATE ON admin.organization FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER admin_oq_user_refresh_last_update_trig BEFORE UPDATE ON admin.oq_user FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();


/*
 * For a given realization and IMT, extract hazard curves from the temporary
 * location in `htemp.hazard_curve_progress` and save them to
 * `hzrdr.hazard_curve_data`, using the specified `hazard_curve_id` as a the
 * "container". This `hzrdr.hazard_curve` record needs to be created
 * beforehand, obviously.
 *
 * `imt` is the text representation of the intensity measure type. For
 * spectral acceleration (SA), the period is encoded in the name, like so:
 * "SA(0.025)"
 *
 * `lons` and `lats` represent the sites of interest for a given calculation.
 * The ordering is EXTREMELY important, because the indices of each location
 * correspond to a position in the `htemp.hazard_curve_progress.result_matrix`.
 */
CREATE OR REPLACE FUNCTION hzrdr.finalize_hazard_curves(
    hazard_calculation_id INTEGER,
    lt_realization_id INTEGER,
    hazard_curve_id INTEGER,
    imt VARCHAR,
    lons FLOAT[],
    lats FLOAT[]
)
    RETURNS VARCHAR
AS $$
    try:
        import cPickle as pickle
    except ImportError:
        import pickle

    def make_point_wkt(x, y):
        """
        Util function to convert x/y coordinates to POINT geom WKT
        """
        return "'SRID=4326;POINT(%s %s)'" % (x, y)

    query = ("""
    SELECT result_matrix
    FROM htemp.hazard_curve_progress
    WHERE lt_realization_id = %s
    AND imt = '%s'
    """ % (lt_realization_id, imt))
    [haz_curve_progress] = plpy.execute(query)

    query = ("""
    SELECT weight
    FROM hzrdr.lt_realization
    WHERE id = %s
    """ % lt_realization_id)
    [lt_realization] = plpy.execute(query)
    weight = lt_realization['weight']

    # the weight is optional, so convert None to NULL
    if weight is None:
        weight = 'NULL'

    # a 2d array
    result_matrix = pickle.loads(haz_curve_progress['result_matrix'])

    insert_query = """
    INSERT INTO hzrdr.hazard_curve_data
    (hazard_curve_id, poes, location, weight)
    VALUES %s
    """

    def gen_rows():
        for i, lon in enumerate(lons):
            lat = lats[i]

            point_wkt = make_point_wkt(lon, lat)
            poes = result_matrix[i]
            poes = "'{" +  ','.join(str(x) for x in poes) + "}'"
            row_tuple = (hazard_curve_id, poes, point_wkt, weight)
            row_values = '(' + ','.join(str(x) for x in row_tuple)  + ')'
            yield row_values

    insert_values = ','.join(gen_rows())

    insert_query %= insert_values
    plpy.execute(insert_query)
    return "OK"
$$ LANGUAGE plpythonu;

COMMENT ON FUNCTION hzrdr.finalize_hazard_curves(
    hazard_calculation_id INTEGER,
    lt_realization_id INTEGER,
    hazard_curve_id INTEGER,
    imt VARCHAR,
    lons FLOAT[],
    lats FLOAT[]
)
IS 'For a given realization and IMT, extract hazard curves from the temporary
location in `htemp.hazard_curve_progress` and save them to
`hzrdr.hazard_curve_data`, using the specified `hazard_curve_id` as a the
"container". This `hzrdr.hazard_curve` record needs to be created
beforehand, obviously.

`imt` is the text representation of the intensity measure type. For
spectral acceleration (SA), the period is encoded in the name, like so:
"SA(0.025)"

`lons` and `lats` represent the sites of interest for a given calculation.
The ordering is EXTREMELY important, because the indices of each location
correspond to a position in the `htemp.hazard_curve_progress.result_matrix`.';
