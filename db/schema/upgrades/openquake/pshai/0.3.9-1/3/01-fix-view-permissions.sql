/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Grant permissions for dropped/recreated views.

GRANT SELECT ON pshai.complex_source TO GROUP openquake;
GRANT SELECT ON pshai.simple_source TO GROUP openquake;
GRANT SELECT ON pshai.complex_rupture TO GROUP openquake;
GRANT SELECT ON pshai.simple_rupture TO GROUP openquake;
