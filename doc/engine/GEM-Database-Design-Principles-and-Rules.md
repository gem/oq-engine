# GEM database design rules and principles

## Introduction and motivation

Due to the global scope and nature of the GEM project a number of databases will be developed independently and eventually delivered to the GEM model facility.

Upon delivery these databases will need to be integrated and operated by the GEM model facility in consideration of some of the following questions and challenges:

 - what degree of interoperability between these databases is required, are there e.g. cross-cutting data and/or queries needed by GEM components?
 - what is the envisaged RAM/storage capacity required by these databases? How do we scale in case that more capacity is needed? How do we prevent capacity resource starvation?
 - what users and components are allowed what kind of access to what database artefacts? How fine-grained does the authorisation model need to be?
 - what are the computational requirements of these databases? How do we ensure a fair utilisation of computational resources? What constitutes fairness?
 - how de we make sure that database administrators and architects can read, revise and maintain the schemas of these disparate databases with reasonable effort? How about adding and revising queries etc. in the process of integration and tuning?

It will be difficult to provide answers to most of the questions above *a priori*.
However, if some best practices are observed, the resulting database designs will have the qualities needed for a secure deployment as well as the subsequent scaling and tuning in the data centre.

Here is a selection of these best practices in a nut shell:

1. namespace everything: all database design artefacts should live in an appropriate project name space. No global names please!
1. tablespace everything: all database tables should be mapped to a table space.
1. userspace everything: all major components in a project should have an appropriate *database* user and use it when connecting to the database.
1. secure everything: all access permissions to tables must be defined explicitly for the appropriate *database* users.
1. have conventions for everything: all database design artefacts should adhere to certain naming conventions. All database tables should adhere to certain *design* conventions. Entities appearing in many databases should all be named the same way.

## Deployment considerations

### Revisions

Your database (design) should work with

 * [PostgreSQL 9.1](http://www.postgresql.org/docs/9.1/static/release-9-1-3.html)
 * [PostGIS 1.5](http://postgis.refractions.net/news/20100311/)

## GIS considerations

### Geometry versus geography

When choosing between the geometry and the geography types please bear in mind

 - geography types are ideally suited for simple measurements and relationship
   checks on data covering *large* areas. Conversely, geometry types are
   preferable when operating on smaller areas (like a town, region or small
   country).
 - geometry types have the advantage of a much richer set of functions, faster
   relationship checks and of wider tool support.

Please note that the geography type was only introduced in PostGIS `rev. 1.5`.
The *geometry versus geography* recommendations are likely to change if and
when we switch to PostGIS `rev. 2` or above.

## Name spaces

Every database design artefact e.g. table, function, sequence etc. shall be defined in an appropriate project name space. In the postgres database these name spaces are called "schemas".
Every project shall be allocated a 5-letter prefix/schema name for each database they plan to deliver into the GEM model facility.
Example: the earthquake catalog database is allocated the `eqcat` name space (or postgres `schema`).

    CREATE SCHEMA eqcat;
    CREATE TABLE eqcat.catalog (
    ...
    );

Please see also the [postgres manual page on schemas](http://www.postgresql.org/docs/9.1/static/ddl-schemas.html "Postgres manual page on schemas")

## Table spaces

In order to facilitate capacity scaling as well as tuning all tables shall be created in a table space.
All table spaces shall be prefixed with the project's schema name e.g.:

    CREATE TABLESPACE eqcat_ts LOCATION '/mnt/eqcat/ts/main';
    CREATE TABLE eqcat.catalog (
    ...
    ) TABLESPACE eqcat_ts;

Please see also the [postgres manual page on table spaces](http://www.postgresql.org/docs/9.1/static/manage-ag-tablespaces.html "Postgres manual page on table spaces")


## Database users

In order to facilitate proper database security (authentication, authorisation and auditing) as well as database administration and operation (logs, tuning) each project shall introduce a database user for each major subsystem or component.

All database access permissions and authorisations will be tied to these database users.

Every database user shall be prefixed by the `schema` name of the project that introduces it. Example:

    CREATE ROLE eqcat_reader LOGIN PASSWORD ’string’;

If at all possible have separate users for components that only read the database versus the ones that read *and* write.

Please see also the [postgres manual page on roles](http://www.postgresql.org/docs/9.1/static/user-manag.html "Postgres manual page on roles")

## Security considerations

All database user accounts must be secured e.g. by setting appropriate passwords.
Only the minimal permissions required for a working system should be granted to any one database user.

When in doubt whether to "reuse" an existing database user or introduce another one, do the latter.

Maintain a list of all database users that are in use in the system. Maintain a list of all access permissions granted to a database user.
The latter should ideally be an idempotent SQL script that can be executed (via psql) to define a user's access permissions.

Please see also the [postgres manual page on permissions](http://www.postgresql.org/docs/9.1/static/sql-grant.html "Postgres manual page on permissions")

## Naming rules

Stick to sensible naming rules and be consistent [but not excessive :-)](http://www.dilbert.com/strips/comic/2011-04-23/)

SQL is case insensitive, but please stick to lower case for data definition language (DDL) artefacts.
Use underscores as opposed to camel case. Database tables and columns should ideally consist of three words at a maximum.

Avoid lengthy DDL artefact names. When in doubt define *and document* project-specific acronyms and stick to these.

The same entities should be named the same in all databases e.g. `lon` and `lat` as opposed to `longitude` and `latitude`.

Have a project dictionary listing all
 * acronyms
 * terms that have a project-specific meaning

Every index shall be prefixed by the schema and the table name. Assuming the following table definition:

    CREATE TABLE eqcat.catalog (
        id SERIAL PRIMARY KEY,
        catnum INTEGER,
        creation_date TIMESTAMP
    ) TABLESPACE eqcat_ts;

[An index](http://www.postgresql.org/docs/9.1/static/sql-createindex.html) should be created like so:

    CREATE INDEX eqcat_catalog_catnum_creation_date_idx
    ON eqcat.catalog(catnum, creation_date);

Please note how the name lists the columns that are being indexed.

### Use lower case and underscores

All names should be in lower case.  Use underscores as opposed to camel case.
Database tables and columns should ideally consist of three words at a maximum.

### Primary keys

Every table needs to have a primary key with the name `id`. Example:

    CREATE TABLE a.xxx (
        id SERIAL PRIMARY KEY,
    ) TABLESPACE a_ts;

### Foreign keys

    CREATE TABLE a.xxx (
        id SERIAL PRIMARY KEY,
    ) TABLESPACE a_ts;

    CREATE TABLE a.yyy (
        id SERIAL PRIMARY KEY,
        xxx_id INTEGER
    ) TABLESPACE a_ts;

    ALTER TABLE a.yyy ADD CONSTRAINT a_yyy_xxx_fk
    FOREIGN KEY (xxx_id) REFERENCES a.xxx(id) ON DELETE <behaviour>;

All foreign keys should be defined as above

 * define foreign key constraints outside of tables in order to facilitate ETL operations etc.
 * the foreign key column should be called <target-table-name>_id
 * the foreign key constraint should be called
   <postgres-schema>_<source-table-name>_<target-table-name>_fk
 * define the `ON DELETE` behaviour as appropriate to the tables at hand.

## Documentation

Be absolutely fanatic about documentation and invest in it! Database schemas are a reflection of a system's domain model and should be understood by all project stake holders (developers, administrators, scientists etc.).

### Built-in schema documentation

Have a [separate file](https://github.com/gem/oq-engine/blob/master/db/schema/comments.sql) with built-in schema documentation i.e. something along the lines of:

    COMMENT ON SCHEMA pshai IS 'PSHA input model';
    COMMENT ON TABLE pshai.mfd_evd IS 'Magnitude frequency distribution, evenly discretized.';
    COMMENT ON COLUMN pshai.mfd_evd.magnitude_type IS 'Magnitude type i.e. one of:
        - body wave magnitude (Mb)
        - duration magnitude (Md)
        - local magnitude (Ml)
        - surface wave magnitude (Ms)
        - moment magnitude (Mw)';

That way schema diagrams and documentation can be reverse engineered from the actual database using various tools.

### Project/model dictionary

Have a dictionary of all terms that are particular to the project and/or system domain model. This facilitates communication and helps avoid misunderstandings.

Try coming up with a tool that parses the built-in schema documentation and generates the dictionary from it (partially).

### A picture is worth a thousand words

Use database diagrams (e.g. [entity relationship](http://en.wikipedia.org/wiki/Entity-relationship_model)) to document the schema!
Ideally, you should have an [overview diagram](https://github.com/gem/oq-engine/wiki/images/db/pshai.png) that depicts how things hang together and a number of [more detailed diagrams](https://github.com/gem/oq-engine/wiki/images/db/ssources.png) showing more information.

## Other rules and recommendations

### Avoid compound database table keys if at all possible.

Enough said :-)

### Err on the side of simplicity

The agile ideas apply to database schema design as well :-) Your schema design should be simple and specific. Also, schemas are a living, breathing thing, they grow with the system.
Don't try to define everything straight-away but build the schema in a number of iterations/increments as needed by the features that are added to the system.

### Avoid overly generic schemas

Dare to be specific :-) Overly generic schema have a high cognitive cost (i.e. they are difficult to grok) and that usually propagates to all the software that makes use of such a schema resulting in bugs, unmaintainable code and all the other problems you do *not* want to have.

### Surrogate keys

Each table shall have a [`serial`](http://www.postgresql.org/docs/9.1/static/datatype-numeric.html#DATATYPE-SERIAL) surrogate key defined as follows:

    CREATE TABLE eqcat.catalog (
        id SERIAL PRIMARY KEY,
        ...
    ) TABLESPACE eqcat_ts;

### Ropes and knots

Run a tidy ship and tie things down :-) e.g. by introducing appropriate constraints where applicable. Example:

    -- seismic input type
    si_type VARCHAR NOT NULL DEFAULT 'simple'
        CONSTRAINT si_type_val CHECK (si_type IN ('complex', 'point', 'simple')),

This way all the code that accesses the database can rely on the fact that the `si_type` column can have only three possible values and there is no need to repeat this check all over the place.

Another example: if you know beforehand that a property must be unique in some context then state it:

    CREATE UNIQUE INDEX admin_oq_user_user_name_uniq_idx ON admin.oq_user(user_name);

### Track revisions or update times

We plan to store the results of seismic calculations along with the calculation inputs (source models). However, changes to certain source model properties may invalidate the stored results.
It is hence important to be able to perceive/track changes to source model properties in the database. There is a number of ways to achieve this. What follows are just two variants.

#### The sequence variant

Add a [sequence](http://www.postgresql.org/docs/9.1/static/functions-sequence.html) to all seismic source model tables and draw a new value from it upon each update (e.g. in an `BEFORE` update trigger).

#### Using a time stamp

Have a `last_update` time stamp in each seismic source model table and refresh it upon each update. See e.g. the `pshai.source` table in [`openquake.sql`](https://github.com/gem/oq-engine/blob/master/db/schema/openquake.sql) and the associated `refresh_last_update()` trigger function in [`functions.sql`](https://github.com/gem/oq-engine/blob/master/openquake/db/schema/functions.sql).

### Separate schema definitions from code, indexes and security settings

In order to facilitate gradual database installations and/or upgrades the following should be in separate files

- [database functions (stored procedures)](https://github.com/gem/oq-engine/blob/master/openquake/db/schema/functions.sql)
- [index definitions](https://github.com/gem/oq-engine/blob/master/openquake/db/schema/indexes.sql)
- [users and access permissions](https://github.com/gem/oq-engine/blob/master/openquake/db/schema/security.sql)
- [built-in schema documentation](https://github.com/gem/oq-engine/blob/master/openquake/db/schema/comments.sql)

### Have a deployment script

Make it possible for developers and/or any other stake holders to deploy the schema for the purpose of development, testing and learning. Have a [deployment script](https://github.com/gem/oq-engine/blob/master/bin/create_oq_schema).

### Keep schema version information in the database

Keep version information pertaining to the database schema in the database. This facilitates the writing of schema and data migration code at a later stage.

See e.g. the `revision_info` table in [`openquake.sql`](https://github.com/gem/oq-engine/blob/master/openquake/db/schema/openquake.sql) and the [rows we insert into it](https://github.com/gem/oq-engine/blob/master/openquake/db/schema/load.sql) upon database creation.

## Examples

Please see the [current OpenQuake database schema definition](https://github.com/gem/oq-engine/blob/master/openquake/db/schema/openquake.sql) for more examples.

***

[[link_to_notes (this goes to etherpad)]]


Back to [[Blue prints|BluePrints]]

