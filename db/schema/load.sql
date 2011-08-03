/*
  Static data for the OpenQuake database schema.

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


INSERT INTO admin.organization(name) VALUES('GEM Foundation');
INSERT INTO admin.oq_user(user_name, full_name, organization_id) VALUES('openquake', 'Default user', 1);

INSERT INTO admin.revision_info(artefact, revision) VALUES('openquake/admin', '0.3.9-1');
INSERT INTO admin.revision_info(artefact, revision, step) VALUES('openquake/eqcat', '0.3.9-1', 2);
INSERT INTO admin.revision_info(artefact, revision, step) VALUES('openquake/hzrdi', '0.4.2', 0);
INSERT INTO admin.revision_info(artefact, revision, step) VALUES('openquake/hzrdr', '0.4.2', 0);
INSERT INTO admin.revision_info(artefact, revision, step) VALUES('openquake/oqmif', '0.4.2', 2);
INSERT INTO admin.revision_info(artefact, revision, step) VALUES('openquake/riski', '0.4.2', 0);
INSERT INTO admin.revision_info(artefact, revision, step) VALUES('openquake/riskr', '0.4.2', 0);
INSERT INTO admin.revision_info(artefact, revision, step) VALUES('openquake/uiapi', '0.4.2', 2);
