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
clear: consider the tables `uiapi.output` and ``hzrdr.gmf``,
which are related by a foreign key. We want to import output records
and gmf records from CSV files generated from the COPY TO
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
non-trivial since the ids are used in the gmf.csv file.
which will have the form

2001<tab>1001<tab>...
2002<tab>1002<tab>...
2003<tab>1002<tab>...

assuming the ids in gmf in the original database starts
from 2001. We want to keep the relation between gmf.id
and output.id; in the target database the numbering may differ
but the associations must stay the same.

The solution used by the PGImporter is to use templates, i.e. CSV
files containing $-identifiers. Here is an example:

$ cat output.csv
$out1<tab>some<tab>thing<tab>...
$out2<tab>some<tab>thing<tab>...
$out3<tab>some<tab>thing<tab>...

$ cat gmf.csv
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

if the maximum id in the gmf table is 20000, it will replace

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
    >>> Replacer(dic, 2000).replace_ids('$coll1|$out1')
    '2001|1001'
    >>> dic  # populated dictionary
    OrderedDict([('out1', 1001), ('coll1', 2001)])
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

    # NB: the template variables must have number starting from 1
    def import_templ(self, table_name, templ):
        "Import a csv by replacing the ids; return the last inserted id"
        # NB: currval does not work on empty tables, this is why I use max;
        # nextval is also bad since it would increase the serial
        # number by 1 even when importing empty files
        self.curs.execute("select max(id) from %s" % table_name)
        max_id = self.curs.fetchone()[0] or 0
        repl = Replacer(self.dic, max_id)
        data = repl.replace_ids(templ)
        nlines = templ.count('\n')
        reserve_ids = "select nextval('%s_id_seq') "\
            "from generate_series(1, %d)" % (table_name, nlines)
        self.curs.execute(reserve_ids)  # make sure the ids are available
        self.curs.copy_from(StringIO(data), table_name)
        self.curs.execute("select max(id) from %s" % table_name)
        return self.curs.fetchone()[0] or 0  # latest id

    # NB: The approach used here is good for tests, but not for large data
    # sets, since it requires keeping everything in memory
    def import_all(self, table_name_data_list):
        """
        Import all the data in the list [(table_name, table_data), ...]
        in a single transaction. Notice that table_data must be a template
        string, not a stream.
        """
        try:
            for table_name, table_data in table_name_data_list:
                self.import_templ(table_name, table_data)
        except:
            self.conn.rollback()
            raise
        else:
            self.conn.commit()
