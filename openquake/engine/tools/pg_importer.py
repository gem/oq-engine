#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Autoincremental fields are evil and renowned database experts such as
Joe Celko have written books about why we should not use them.
However programmers keep repeating the same mistakes and ORMs
such as Django are entirely based on autoincremental fields.
Every Django table has an autoincremental field as primary key and
so every table in the openquake database has this structure.
That means that bulk imports are especially difficult when
you have foreign keys. An example make the issue immediately
clear: consider the tables `uiapi.output` and ``hzrdr.gmf_collection``,
which are related by a foreign key. We want to import output records
and gmf_collection records from CSV files generated from the COPY TO
command. The typical use case is for damping data from a db are importing it
into a different database. The same problem is also found when
populating a test database from CSV files.

The output.csv file will have the form

1001<tab>some<tab>thing<tab>...
1002<tab>some<tab>thing<tab>...
1003<tab>some<tab>thing<tab>...
...

assuming the ids starts for 1001 in the original database. In the
target database such ids could be taken and the problem is to
avoid id conflicts, i.e. primary key violations. The problem is
non-trivial since the ids are used in the gmf_collection.csv file.
which will have the form

2001<tab>1001<tab>...
2002<tab>1002<tab>...
2003<tab>1002<tab>...

assuming the ids in gmf_collection in the original database starts
from 2001. We want to keep the relation between gmf_collection.id
and output.id; in the target database the numbering may differ
but the associations must stay the same.

The solution used by the PGImporter is to use templates, i.e. CSV
files containing $-identifiers. Here is an example:

$ cat output.csv
$out1<tab>some<tab>thing<tab>...
$out2<tab>some<tab>thing<tab>...
$out3<tab>some<tab>thing<tab>...

$ cat gmf_collection.csv
$coll1<tab>$out1<tab>...
$coll2<tab>$out2<tab>...
$coll3<tab>$out3<tab>...

The PGImporter takes in input templates like these and replaces
the $-identifiers with the right numbers: it looks at the
maximum identifier in the target database and increments it;
for instance if the maximum id for the output table is 10000,
it will replace

$out1 -> 10001
$out2 -> 10002
$out3 -> 10003

if the maximum id in the gmf_collection table is 20000, it will replace

$coll1 -> 20001
$coll2 -> 20002
$coll3 -> 20003

This is enough to solve the problem of populating a test database; copying
data from a db to another is more cumbersome and will require a smarter
approach (perhaps by using temporary tables).
"""

import re
import string
from cStringIO import StringIO


class Replacer(object):
    """
    Helper class to replace ids in a template string. Here is an
    example of usage:

    >>> from collections import OrderedDict
    >>> dic = OrderedDict()
    >>> Replacer(dic, 1000).replace_ids('$out1|some|thing')
    '1001|some|thing'
    >>> Replacer(dic, 2000).replace_ids('$coll10|$out1')
    '2010|1001'
    >>> dic  # populated dictionary
    OrderedDict([('out1', 1001), ('coll10', 2010)])
    """
    ID = re.compile(r'^\$[a-z]+(\d+)', re.MULTILINE)

    def __init__(self, dic, start):
        self.dic = dic
        self.start = start

    # internal function intentially without docstring
    def _replace_ids(self, match):
        number = int(match.group(1))
        varname = match.group(0)[1:]  # strip the $ from the variable
        self.dic[varname] = self.start + number
        return str(self.start + number)

    def replace_ids(self, templ):
        "Materialize a template by replacing the ids"
        t = self.ID.sub(self._replace_ids, templ)
        return string.Template(t).substitute(**self.dic)


class PGImporter(object):
    """
    Import data in a Postgres database by using a text format suitable
    for COPY FROM. The importer solves the problem with autoincremental
    ids by replacing templates with the right ids.
    """
    def __init__(self, conn):
        self.conn = conn
        self.curs = conn.cursor()
        self.dic = {}

    def import_templ(self, table_name, templ):
        "Import a csv by replacing the ids"
        # NB: currval does not work on empty tables, this is why I use max
        self.curs.execute("select max(id) from %s" % table_name)
        max_id = self.curs.fetchone()[0] or 0
        data = Replacer(self.dic, max_id).replace_ids(templ)
        self.curs.copy_from(StringIO(data), table_name)
        # make sure the serial field is incremented correctly
        next_id = max_id + data.count('\n')
        setval = "select setval('%s_id_seq', %s)" % (table_name, next_id)
        self.curs.execute(setval)

    def import_all(self, table_name_data_list):
        """
        Import all the data in the list [(table_name, table_data), ...]
        in a single transaction.
        """
        try:
            for table_name, table_data in table_name_data_list:
                self.import_templ(table_name, table_data)
        except:
            self.conn.rollback()
            raise
        else:
            self.conn.commit()
