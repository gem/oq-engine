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

CREATE OR REPLACE FUNCTION check_rupture_sources() RETURNS TRIGGER
LANGUAGE plpgsql AS
$$
DECLARE
    num_sources INTEGER := 0;
    violations TEXT := '';
    exception_msg TEXT := '';
BEGIN
    IF NEW.point IS NOT NULL THEN
        num_sources := num_sources + 1;
        violations = 'point';
    END IF;
    IF NEW.simple_fault_id IS NOT NULL THEN
        num_sources := num_sources + 1;
        violations = violations || ' simple_fault_id';
    END IF;
    IF NEW.complex_fault_id IS NOT NULL THEN
        num_sources := num_sources + 1;
        violations = violations || ' complex_fault_id';
    END IF;
    IF num_sources = 0 THEN
        exception_msg := format_exc(TG_OP, 'no seismic inputs', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    ELSE
        IF num_sources > 1 THEN
            exception_msg := format_exc(TG_OP, 'more than one seismic input <' || violations || '>', TG_TABLE_NAME);
            RAISE '%', exception_msg;
        END IF;
    END IF;

    IF NEW.point IS NOT NULL AND NEW.si_type != 'point' THEN
        exception_msg := format_exc(TG_OP, 'type should be point <' || NEW.si_type || '>', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;
    IF NEW.simple_fault_id IS NOT NULL AND NEW.si_type != 'simple' THEN
        exception_msg := format_exc(TG_OP, 'type should be simple <' || NEW.si_type || '>', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;
    IF NEW.complex_fault_id IS NOT NULL AND NEW.si_type != 'complex' THEN
        exception_msg := format_exc(TG_OP, 'type should be complex <' || NEW.si_type || '>', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.last_update := timezone('UTC'::text, now());
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION check_rupture_sources() IS
'Make sure a rupture only has one source (point, simple or complex fault).';

CREATE OR REPLACE FUNCTION check_source_sources() RETURNS TRIGGER
LANGUAGE plpgsql AS
$$
DECLARE
    num_sources INTEGER := 0;
    violations TEXT := '';
    exception_msg TEXT := '';
BEGIN
    IF NEW.point IS NOT NULL THEN
        num_sources := num_sources + 1;
        violations = 'point';
    END IF;
    IF NEW.area IS NOT NULL THEN
        num_sources := num_sources + 1;
        violations = violations || ' area';
    END IF;
    IF NEW.simple_fault_id IS NOT NULL THEN
        num_sources := num_sources + 1;
        violations = violations || ' simple_fault_id';
    END IF;
    IF NEW.complex_fault_id IS NOT NULL THEN
        num_sources := num_sources + 1;
        violations = violations || ' complex_fault_id';
    END IF;
    IF num_sources = 0 THEN
        exception_msg := format_exc(TG_OP, 'no seismic inputs', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    ELSE
        IF num_sources > 1 THEN
            exception_msg := format_exc(TG_OP, 'more than one seismic input <' || violations || '>', TG_TABLE_NAME);
            RAISE '%', exception_msg;
        END IF;
    END IF;

    IF NEW.point IS NOT NULL OR NEW.area IS NOT NULL THEN
        IF NEW.hypocentral_depth IS NULL THEN
            exception_msg := format_exc(TG_OP, 'hypocentral_depth missing', TG_TABLE_NAME);
            RAISE '%', exception_msg;
        END IF;
        IF NEW.r_depth_distr_id IS NULL THEN
            exception_msg := format_exc(TG_OP, 'r_depth_distr_id missing', TG_TABLE_NAME);
            RAISE '%', exception_msg;
        END IF;
    ELSE
        IF NEW.hypocentral_depth IS NOT NULL THEN
            exception_msg := format_exc(TG_OP, 'hypocentral_depth set', TG_TABLE_NAME);
            RAISE '%', exception_msg;
        END IF;
        IF NEW.r_depth_distr_id IS NOT NULL THEN
            exception_msg := format_exc(TG_OP, 'r_depth_distr_id set', TG_TABLE_NAME);
            RAISE '%', exception_msg;
        END IF;
    END IF;

    IF NEW.point IS NOT NULL AND NEW.si_type != 'point' THEN
        exception_msg := format_exc(TG_OP, 'type should be point <' || NEW.si_type || '>', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;
    IF NEW.area IS NOT NULL AND NEW.si_type != 'area' THEN
        exception_msg := format_exc(TG_OP, 'type should be area <' || NEW.si_type || '>', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;
    IF NEW.simple_fault_id IS NOT NULL AND NEW.si_type != 'simple' THEN
        exception_msg := format_exc(TG_OP, 'type should be simple <' || NEW.si_type || '>', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;
    IF NEW.complex_fault_id IS NOT NULL AND NEW.si_type != 'complex' THEN
        exception_msg := format_exc(TG_OP, 'type should be complex <' || NEW.si_type || '>', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.last_update := timezone('UTC'::text, now());
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION check_source_sources() IS
'Make sure a seismic source only has one source (area, point, simple or complex fault).';

CREATE OR REPLACE FUNCTION check_only_one_mfd_set() RETURNS TRIGGER
LANGUAGE plpgsql AS
$$
DECLARE
    num_sources INTEGER := 0;
    exception_msg TEXT := '';
BEGIN
    IF NEW.mfd_tgr_id IS NOT NULL THEN
        -- truncated Gutenberg-Richter
        num_sources := num_sources + 1;
    END IF;
    IF NEW.mfd_evd_id IS NOT NULL THEN
        -- evenly discretized
        num_sources := num_sources + 1;
    END IF;
    IF num_sources = 0 THEN
        exception_msg := format_exc(TG_OP, 'no magnitude frequency distribution', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    ELSE
        IF num_sources > 1 THEN
            exception_msg := format_exc(TG_OP, 'more than one magnitude frequency distribution', TG_TABLE_NAME);
            RAISE '%', exception_msg;
        END IF;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.last_update := timezone('UTC'::text, now());
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION check_only_one_mfd_set() IS
'Make sure only one magnitude frequency distribution is set.';

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
    imt = NEW["imt"]
    if NEW["format"] == "discrete":
        assert imls and len(imls) > 0, "no IMLs for discrete fragility model"
        assert imt, "no IMT for discrete fragility model"
        assert imt in imts, "invalid IMT (%s)" % imt
    else:
        assert imls is None, "IMLs defined for continuous fragility model"
        assert not imt, "IMT defined for continuous fragility model"

    return "OK"
$$ LANGUAGE plpythonu;


COMMENT ON FUNCTION pcheck_fragility_model() IS
'Make sure the inserted continuous fragility model record is consistent.';


CREATE OR REPLACE FUNCTION pcheck_ffc()
  RETURNS TRIGGER
AS $$
    NEW = TD["new"] # new data resulting from insert or update

    # get the associated fragility model record
    q = ("SELECT * FROM riski.fragility_model WHERE id = %s" %
         NEW["fragility_model_id"])
    [fmdl] = plpy.execute(q)

    ls = NEW["ls"]
    lss = fmdl["lss"]
    assert ls and ls in lss, (
        "invalid limit state (%s), not in: %s" % (ls, lss))
    taxonomy = NEW["taxonomy"]
    assert fmdl["format"] == "continuous", (
        "mismatch: discrete model but continuous function (%s, %s)"
        % (ls, taxonomy))

    return "OK"
$$ LANGUAGE plpythonu;


COMMENT ON FUNCTION pcheck_ffc() IS
'Make sure the inserted continuous fragility function record is consistent.';


CREATE OR REPLACE FUNCTION pcheck_ffd()
  RETURNS TRIGGER
AS $$
    NEW = TD["new"] # new data resulting from insert or update

    # get the associated fragility model record
    q = ("SELECT * FROM riski.fragility_model WHERE id = %s" %
         NEW["fragility_model_id"])
    [fmdl] = plpy.execute(q)

    ls = NEW["ls"]
    lss = fmdl["lss"]
    assert ls and ls in lss, (
        "invalid limit state (%s), not in: %s" % (ls, lss))
    taxonomy = NEW["taxonomy"]
    assert fmdl["format"] == "discrete", (
        "mismatch: continuous model but discrete function (%s, %s)"
        % (ls, taxonomy))

    len_poes = len(NEW["poes"])
    len_imls = len(fmdl["imls"])
    assert len_poes == len_imls, (
        "#poes differs from #imls (%s != %s) for discrete function (%s, %s)"
        % (len_poes, len_imls, ls, taxonomy))

    return "OK"
$$ LANGUAGE plpythonu;


COMMENT ON FUNCTION pcheck_ffd() IS
'Make sure the inserted discrete fragility function record is consistent.';


CREATE TRIGGER riskr_dmg_dist_total_data_before_insert_update_trig
BEFORE INSERT OR UPDATE ON riskr.dmg_dist_total_data
FOR EACH ROW EXECUTE PROCEDURE
riskr.pcheck_dmg_state_dmg_dist_total_data();
-- End Damage Distribution, Total

CREATE TRIGGER hzrdi_rupture_before_insert_update_trig
BEFORE INSERT OR UPDATE ON hzrdi.rupture
FOR EACH ROW EXECUTE PROCEDURE check_rupture_sources();

CREATE TRIGGER hzrdi_source_before_insert_update_trig
BEFORE INSERT OR UPDATE ON hzrdi.source
FOR EACH ROW EXECUTE PROCEDURE check_source_sources();

CREATE TRIGGER hzrdi_r_rate_mdl_before_insert_update_trig
BEFORE INSERT OR UPDATE ON hzrdi.r_rate_mdl
FOR EACH ROW EXECUTE PROCEDURE check_only_one_mfd_set();

CREATE TRIGGER hzrdi_simple_fault_before_insert_update_trig
BEFORE INSERT OR UPDATE ON hzrdi.simple_fault
FOR EACH ROW EXECUTE PROCEDURE check_only_one_mfd_set();

CREATE TRIGGER hzrdi_complex_fault_before_insert_update_trig
BEFORE INSERT OR UPDATE ON hzrdi.complex_fault
FOR EACH ROW EXECUTE PROCEDURE check_only_one_mfd_set();

CREATE TRIGGER oqmif_exposure_model_before_insert_update_trig
BEFORE INSERT ON oqmif.exposure_model
FOR EACH ROW EXECUTE PROCEDURE pcheck_exposure_model();

CREATE TRIGGER oqmif_exposure_data_before_insert_update_trig
BEFORE INSERT ON oqmif.exposure_data
FOR EACH ROW EXECUTE PROCEDURE pcheck_exposure_data();

CREATE TRIGGER riski_fragility_model_before_insert_update_trig
BEFORE INSERT ON riski.fragility_model
FOR EACH ROW EXECUTE PROCEDURE pcheck_fragility_model();

CREATE TRIGGER riski_ffc_before_insert_update_trig
BEFORE INSERT ON riski.ffc
FOR EACH ROW EXECUTE PROCEDURE pcheck_ffc();

CREATE TRIGGER riski_ffd_before_insert_update_trig
BEFORE INSERT ON riski.ffd
FOR EACH ROW EXECUTE PROCEDURE pcheck_ffd();

CREATE TRIGGER eqcat_magnitude_before_insert_update_trig
BEFORE INSERT OR UPDATE ON eqcat.magnitude
FOR EACH ROW EXECUTE PROCEDURE check_magnitude_data();

CREATE TRIGGER admin_organization_refresh_last_update_trig BEFORE UPDATE ON admin.organization FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER admin_oq_user_refresh_last_update_trig BEFORE UPDATE ON admin.oq_user FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER eqcat_catalog_refresh_last_update_trig BEFORE UPDATE ON eqcat.catalog FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER eqcat_surface_refresh_last_update_trig BEFORE UPDATE ON eqcat.surface FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER hzrdi_fault_edge_refresh_last_update_trig BEFORE UPDATE ON hzrdi.fault_edge FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER hzrdi_mfd_evd_refresh_last_update_trig BEFORE UPDATE ON hzrdi.mfd_evd FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER hzrdi_mfd_tgr_refresh_last_update_trig BEFORE UPDATE ON hzrdi.mfd_tgr FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER hzrdi_r_depth_distr_refresh_last_update_trig BEFORE UPDATE ON hzrdi.r_depth_distr FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER hzrdi_focal_mechanism_refresh_last_update_trig BEFORE UPDATE ON hzrdi.focal_mechanism FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER riski_vulnerability_function_refresh_last_update_trig BEFORE UPDATE ON riski.vulnerability_function FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER riski_vulnerability_model_refresh_last_update_trig BEFORE UPDATE ON riski.vulnerability_model FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();
