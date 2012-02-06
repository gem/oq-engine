/*
  Static data for the OpenQuake database schema.

    Copyright (c) 2010-2012, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


INSERT INTO admin.organization(name) VALUES('GEM Foundation');
INSERT INTO admin.oq_user(user_name, full_name, organization_id) VALUES('openquake', 'Default user', 1);

INSERT INTO admin.revision_info(artefact, revision, step) VALUES('openquake', '0.4.2', 17);
