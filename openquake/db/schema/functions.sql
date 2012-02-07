/*
  Functions used in the OpenQuake database.

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


CREATE OR REPLACE FUNCTION check_exposure_model() RETURNS TRIGGER
LANGUAGE plpgsql AS
$$
DECLARE
    whats_wrong TEXT := '';
    exception_msg TEXT := '';
BEGIN
    -- area_type is optional unless
    --     * stcoType is set to "per_area" or
    --     * recoType is set to "per_area"
    --     * cocoType is set to "per_area"
    IF NEW.area_type IS NULL AND NEW.coco_type = 'per_area' THEN
        whats_wrong = 'coco_type=per_area';
    END IF;
    IF NEW.area_type IS NULL AND NEW.reco_type = 'per_area' THEN
        IF whats_wrong <> '' THEN
            whats_wrong = whats_wrong || ', reco_type=per_area';
        ELSE
            whats_wrong = 'reco_type=per_area';
        END IF;
    END IF;
    IF NEW.area_type IS NULL AND NEW.stco_type = 'per_area' THEN
        IF whats_wrong <> '' THEN
            whats_wrong = whats_wrong || ', stco_type=per_area';
        ELSE
            whats_wrong = 'stco_type=per_area';
        END IF;
    END IF;
    IF whats_wrong <> '' THEN
        exception_msg := format_exc(TG_OP, 'area_type is mandatory for ' || whats_wrong, TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;

    -- area_unit is optional unless
    --     * stcoType is set to "per_area" or
    --     * recoType is set to "per_area"
    --     * cocoType is set to "per_area"
    IF NEW.area_unit IS NULL AND NEW.coco_unit = 'per_area' THEN
        whats_wrong = 'coco_unit=per_area';
    END IF;
    IF NEW.area_unit IS NULL AND NEW.reco_unit = 'per_area' THEN
        IF whats_wrong <> '' THEN
            whats_wrong = whats_wrong || ', reco_unit=per_area';
        ELSE
            whats_wrong = 'reco_unit=per_area';
        END IF;
    END IF;
    IF NEW.area_unit IS NULL AND NEW.stco_unit = 'per_area' THEN
        IF whats_wrong <> '' THEN
            whats_wrong = whats_wrong || ', stco_unit=per_area';
        ELSE
            whats_wrong = 'stco_unit=per_area';
        END IF;
    END IF;
    IF whats_wrong <> '' THEN
        exception_msg := format_exc(TG_OP, 'area_unit is mandatory for ' || whats_wrong, TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;

    IF whats_wrong <> '' THEN
        exception_msg := format_exc(TG_OP, 'area_unit is mandatory for ' || whats_wrong, TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;

    -- contents cost unit is mandatory if contents cost type is set
    IF NEW.coco_unit IS NULL AND NEW.coco_type IS NOT NULL THEN
        exception_msg := format_exc(TG_OP, 'coco_unit is mandatory for coco_type <' || NEW.coco_type || '>', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;

    -- retrofitting cost unit is mandatory if retrofitting cost type is set
    IF NEW.reco_unit IS NULL AND NEW.reco_type IS NOT NULL THEN
        exception_msg := format_exc(TG_OP, 'reco_unit is mandatory for reco_type <' || NEW.reco_type || '>', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.last_update := timezone('UTC'::text, now());
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION check_exposure_model() IS
'Make sure the inserted or modified exposure model record is consistent.';

CREATE OR REPLACE FUNCTION check_exposure_data() RETURNS TRIGGER
LANGUAGE plpgsql AS
$$
DECLARE
    emdl oqmif.exposure_model%ROWTYPE;
    exception_msg TEXT := '';
BEGIN
    SELECT * INTO emdl FROM oqmif.exposure_model WHERE id = NEW.exposure_model_id;

     -- structural cost:
     -- mandatory unless we compute fatalities in which case
     -- assetCategory will be set to "population"
    IF NEW.stco IS NULL AND emdl.category != 'population' THEN
        exception_msg := format_exc(TG_OP, 'structural cost mandatory for category <' || emdl.category || '>', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;

    -- number is optional unless
    --     * we compute fatalities or
    --     * stcoType differs from "aggregated" or
    --     * recoType differs from "aggregated"
    --     * cocoType differs from "aggregated"
    IF NEW.number_of_units IS NULL AND (emdl.category = 'population' OR emdl.coco_type != 'aggregated' OR emdl.stco_type != 'aggregated' OR emdl.reco_type != 'aggregated') THEN
        exception_msg := format_exc(TG_OP, 'number is mandatory for category <' || emdl.category || '>, stco_type <' || emdl.stco_type || '>, reco_type <' || emdl.reco_type || '>, coco_type <' || emdl.coco_type || '>', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;


    -- area is optional unless
    --     * stcoType is set to "per_area" or
    --     * recoType is set to "per_area"
    --     * cocoType is set to "per_area"
    IF NEW.area IS NULL AND (emdl.coco_type = 'per_area' OR emdl.stco_type = 'per_area' OR emdl.reco_type = 'per_area') THEN
        exception_msg := format_exc(TG_OP, 'area_unit is mandatory for stco_type <' || emdl.stco_type || '>, reco_type <' || emdl.reco_type || '>, coco_type <' || emdl.coco_type || '>', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;

    -- retrofitting cost: optional unless
    --     * we compute BCR ("impossible" to check here)
    --     * recoType is defined
    IF NEW.reco IS NULL AND emdl.reco_type IS NOT NULL THEN
        exception_msg := format_exc(TG_OP, 'retrofitting cost is mandatory for reco_type <' || emdl.reco_type || '>', TG_TABLE_NAME);
        RAISE '%', exception_msg;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.last_update := timezone('UTC'::text, now());
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION check_exposure_data() IS
'Make sure the inserted or modified exposure data is consistent.';



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
BEFORE INSERT OR UPDATE ON oqmif.exposure_model
FOR EACH ROW EXECUTE PROCEDURE check_exposure_model();

CREATE TRIGGER oqmif_exposure_data_before_insert_update_trig
BEFORE INSERT OR UPDATE ON oqmif.exposure_data
FOR EACH ROW EXECUTE PROCEDURE check_exposure_data();

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

CREATE TRIGGER oqmif_exposure_model_refresh_last_update_trig BEFORE UPDATE ON oqmif.exposure_model FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER oqmif_exposure_data_refresh_last_update_trig BEFORE UPDATE ON oqmif.exposure_data FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER riski_vulnerability_function_refresh_last_update_trig BEFORE UPDATE ON riski.vulnerability_function FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER riski_vulnerability_model_refresh_last_update_trig BEFORE UPDATE ON riski.vulnerability_model FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER uiapi_input_set_refresh_last_update_trig BEFORE UPDATE ON uiapi.input_set FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();
