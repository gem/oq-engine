/*
  Functions used in the OpenQuake database.

  Copyright (c) 2010-2012, GEM Foundation.

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

CREATE OR REPLACE FUNCTION check_magnitude_data() RETURNS TRIGGER
LANGUAGE plpgsql AS
$$
DECLARE
    num_sources INTEGER := 0;
    exception_msg TEXT := '';
BEGIN
    IF NEW.mb_val IS NOT NULL THEN
        num_sources := num_sources + 1;
    END IF;
    IF NEW.ml_val IS NOT NULL THEN
        num_sources := num_sources + 1;
    END IF;
    IF NEW.ms_val IS NOT NULL THEN
        num_sources := num_sources + 1;
    END IF;
    IF NEW.mw_val IS NOT NULL THEN
        num_sources := num_sources + 1;
    END IF;
    IF num_sources = 0 THEN
        exception_msg := format_exc(TG_OP, 'no magnitude value set', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.last_update := timezone('UTC'::text, now());
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION check_magnitude_data() IS
'Make sure that at least one magnitude value is set.';

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
    q = ("SELECT * FROM oqmif.exposure_model WHERE id = %s" %
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

-- Damage Distribution, Per Asset
CREATE OR REPLACE FUNCTION riskr.pcheck_dmg_state_dmg_dist_per_asset_data()
    RETURNS TRIGGER
AS $$
    def fmt(err):
        return "%s (%s)" % (err, TD["table_name"])

    # make sure that NEW.dmg_state is in dmg_dist_per_asset.dmg_states
    NEW = TD["new"]

    ps = plpy.prepare(
        "SELECT dmg_states FROM riskr.dmg_dist_per_asset WHERE id=$1",
        ["integer"])
    [ddps] = plpy.execute(ps, [NEW["dmg_dist_per_asset_id"]])

    if not NEW["dmg_state"] in ddps["dmg_states"]:
        raise Exception(fmt("Invalid dmg_state '%s', must be one of %s"
                            % (NEW["dmg_state"], ddps["dmg_states"])))

    return "OK"
$$ LANGUAGE plpythonu;


COMMENT ON FUNCTION riskr.pcheck_dmg_state_dmg_dist_per_asset_data() IS
'Make sure that each inserted or modified riskr.dmg_dist_per_asset_data record
 has a valid dmg_state.';


CREATE TRIGGER riskr_dmg_dist_per_asset_data_before_insert_update_trig
BEFORE INSERT OR UPDATE ON riskr.dmg_dist_per_asset_data
FOR EACH ROW EXECUTE PROCEDURE
riskr.pcheck_dmg_state_dmg_dist_per_asset_data();
-- End Damage Distribution, Per Asset

-- Damage Distribution, Per Taxonomy
CREATE OR REPLACE FUNCTION riskr.pcheck_dmg_state_dmg_dist_per_taxonomy_data()
    RETURNS TRIGGER
AS $$
    def fmt(err):
        return "%s (%s)" % (err, TD["table_name"])

    # make sure that NEW.dmg_state is in dmg_dist_per_taxonomy.dmg_states
    NEW = TD["new"]

    ps = plpy.prepare(
        "SELECT dmg_states FROM riskr.dmg_dist_per_taxonomy WHERE id=$1",
        ["integer"])

    [ddpt] = plpy.execute(ps, [NEW["dmg_dist_per_taxonomy_id"]])

    if not NEW["dmg_state"] in ddpt["dmg_states"]:
        raise Exception(fmt("Invalid dmg_state '%s', must be one of %s"
                            % (NEW["dmg_state"], ddpt["dmg_states"])))

    return "OK"
$$ LANGUAGE plpythonu;


COMMENT ON FUNCTION riskr.pcheck_dmg_state_dmg_dist_per_taxonomy_data() IS
'Make sure that each inserted or modified riskr.dmg_dist_per_taxonomy_data
 record has a valid dmg_state.';


CREATE TRIGGER riskr_dmg_dist_per_taxonomy_data_before_insert_update_trig
BEFORE INSERT OR UPDATE ON riskr.dmg_dist_per_taxonomy_data
FOR EACH ROW EXECUTE PROCEDURE
riskr.pcheck_dmg_state_dmg_dist_per_taxonomy_data();
-- End Damage Distribution, Per Taxonomy

-- Damage Distribution, Total
CREATE OR REPLACE FUNCTION riskr.pcheck_dmg_state_dmg_dist_total_data()
    RETURNS TRIGGER
AS $$
    def fmt(err):
        return "%s (%s)" % (err, TD["table_name"])

    # make sure that NEW.dmg_state is in dmg_dist_total.dmg_states
    NEW = TD["new"]

    ps = plpy.prepare(
        "SELECT dmg_states FROM riskr.dmg_dist_total WHERE id=$1",
        ["integer"])

    [ddt] = plpy.execute(ps, [NEW["dmg_dist_total_id"]])

    if not NEW["dmg_state"] in ddt["dmg_states"]:
        raise Exception(fmt("Invalid dmg_state '%s', must be one of %s"
                            % (NEW["dmg_state"], ddt["dmg_states"])))

    return "OK"
$$ LANGUAGE plpythonu;


COMMENT ON FUNCTION riskr.pcheck_dmg_state_dmg_dist_total_data() IS
'Make sure that each inserted or modified riskr.dmg_dist_total record has a
 valid dmg_state.';


CREATE OR REPLACE FUNCTION pcheck_fragility_model()
  RETURNS TRIGGER
AS $$
    imts = ("pga", "sa", "pgv", "pgd", "ia", "rsd", "mmi")
    NEW = TD["new"] # new data resulting from insert or update

    def fmt(err):
        return "%s (%s)" % (err, TD["table_name"])

    if len(NEW["lss"]) == 0:
        raise Exception(fmt("no limit states supplied"))

    imls = NEW["imls"]
    no_damage_limit = NEW["no_damage_limit"]
    imt = NEW["imt"]
    if NEW["format"] == "discrete":
        assert NEW.get("max_iml") is None, "Maximum IML not allowed for discrete fragility model"
        assert NEW.get("min_iml") is None, "Minimum IML not allowed for discrete fragility model"
        assert imls and len(imls) > 0, "no IMLs for discrete fragility model"
        assert imt, "no IMT for discrete fragility model"
        assert imt in imts, "invalid IMT (%s)" % imt
        if no_damage_limit is not None:
            assert no_damage_limit < imls[0], "No Damage Limit must be less than IML values"
            assert no_damage_limit >= 0, "No Damage Limit must be a positive value"

    else:
        assert imls is None, "IMLs defined for continuous fragility model"
        assert not imt, "IMT defined for continuous fragility model"
        assert no_damage_limit is None, ("No Damage Limit defined for "
            "continuous fragility model")

    return "OK"
$$ LANGUAGE plpythonu;


CREATE OR REPLACE FUNCTION pcheck_oq_job_profile()
  RETURNS TRIGGER
AS $$
    # By default we will merely consent to the insert/update operation.
    result = "OK"

    NEW = TD["new"] # new data resulting from insert or update

    if NEW["calc_mode"] != "uhs":
        imt = NEW["imt"]
        assert imt in ("pga", "sa", "pgv", "pgd", "ia", "rsd", "mmi"), (
            "Invalid intensity measure type: '%s'" % imt)

        if imt == "sa":
            assert NEW["period"] is not None, (
                "Period must be set for intensity measure type 'sa'")
        else:
            assert NEW["period"] is None, (
                "Period must not be set for intensity measure type '%s'" % imt)
    else:
        # This is a uhs job.
        if NEW["imt"] != "sa" or NEW["period"] is not None:
            # The trigger will return a modified row.
            result = "MODIFY"

        if NEW["imt"] != "sa":
            NEW["imt"] = "sa"
        if NEW["period"] is not None:
            NEW["period"] = None

    return result
$$ LANGUAGE plpythonu;


COMMENT ON FUNCTION pcheck_oq_job_profile() IS
'Make sure the inserted/updated job profile record is consistent.';


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


CREATE TRIGGER uiapi_cnode_stats_before_update_trig
BEFORE UPDATE ON uiapi.cnode_stats
FOR EACH ROW EXECUTE PROCEDURE uiapi.pcount_cnode_failures();


CREATE TRIGGER riskr_dmg_dist_total_data_before_insert_update_trig
BEFORE INSERT OR UPDATE ON riskr.dmg_dist_total_data
FOR EACH ROW EXECUTE PROCEDURE riskr.pcheck_dmg_state_dmg_dist_total_data();
-- End Damage Distribution, Total

CREATE TRIGGER oqmif_exposure_model_before_insert_update_trig
BEFORE INSERT ON oqmif.exposure_model
FOR EACH ROW EXECUTE PROCEDURE pcheck_exposure_model();

CREATE TRIGGER oqmif_exposure_data_before_insert_update_trig
BEFORE INSERT ON oqmif.exposure_data
FOR EACH ROW EXECUTE PROCEDURE pcheck_exposure_data();

CREATE TRIGGER uiapi_oq_job_profile_before_insert_update_trig
BEFORE INSERT OR UPDATE ON uiapi.oq_job_profile
FOR EACH ROW EXECUTE PROCEDURE pcheck_oq_job_profile();

CREATE TRIGGER eqcat_magnitude_before_insert_update_trig
BEFORE INSERT OR UPDATE ON eqcat.magnitude
FOR EACH ROW EXECUTE PROCEDURE check_magnitude_data();

CREATE TRIGGER admin_organization_refresh_last_update_trig BEFORE UPDATE ON admin.organization FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER admin_oq_user_refresh_last_update_trig BEFORE UPDATE ON admin.oq_user FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER eqcat_catalog_refresh_last_update_trig BEFORE UPDATE ON eqcat.catalog FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER eqcat_surface_refresh_last_update_trig BEFORE UPDATE ON eqcat.surface FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();
