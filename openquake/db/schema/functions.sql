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
