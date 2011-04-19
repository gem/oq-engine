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

CREATE OR REPLACE FUNCTION check_rupture_sources() RETURNS TRIGGER
LANGUAGE plpgsql AS
$$
DECLARE
    num_sources INTEGER := 0;
    violations TEXT := '';
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
    IF num_sources > 1 THEN
        IF TG_OP = 'INSERT' THEN
            RAISE 'INSERT: more than one rupture source (%)', violations;
        ELSE
            RAISE 'UPDATE: more than one rupture source (%)', violations;
        END IF;
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
    IF num_sources > 1 THEN
        IF TG_OP = 'INSERT' THEN
            RAISE 'INSERT: more than one seismic source input (%)', violations;
        ELSE
            RAISE 'UPDATE: more than one seismic source input (%)', violations;
        END IF;
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
        IF TG_OP = 'INSERT' THEN
            RAISE 'INSERT: no magnitude frequency distribution set (%)', TG_TABLE_NAME;
        ELSE
            RAISE 'UPDATE: no magnitude frequency distribution set (%)', TG_TABLE_NAME;
        END IF;
    ELSE
        IF num_sources > 1 THEN
            IF TG_OP = 'INSERT' THEN
                RAISE 'INSERT: only one magnitude frequency distribution can be set (%)', TG_TABLE_NAME;
            ELSE
                RAISE 'UPDATE: only one magnitude frequency distribution can be set (%)', TG_TABLE_NAME;
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION check_only_one_mfd_set() IS
'Make sure only one magnitude frequency distribution is set.';
