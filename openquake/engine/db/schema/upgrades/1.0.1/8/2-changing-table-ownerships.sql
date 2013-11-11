DO
$$
DECLARE
    row record;
BEGIN
    FOR row IN SELECT * FROM pg_tables WHERE schemaname IN ('admin', 'hzrdr', 'riskr', 'hzrdi', 'riski', 'htemp', 'uiapi')
    LOOP
        EXECUTE 'ALTER TABLE ' || quote_ident(row.schemaname) || '.' || quote_ident(row.tablename) || ' OWNER TO oq_admin;';
    END LOOP;
END;
$$;
