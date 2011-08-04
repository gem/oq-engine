/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- All triggers that refresh the 'last_update' time stamps shall stick to the
-- UTC time zone.

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

CREATE OR REPLACE FUNCTION refresh_last_update() RETURNS TRIGGER
LANGUAGE plpgsql AS
$$
DECLARE
BEGIN
    NEW.last_update := timezone('UTC'::text, now());
    RETURN NEW;
END;
$$;
