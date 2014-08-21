def upgrade(conn):
    curs = conn.cursor()
    values = [
        (5, 2, 0, ['b11', 'b21'], 'other_model.xml'),
        (6, 2, 1, ['b21', 'b12'], 'other_model.xml'),
    ]
    curs.executemany(
        'INSERT INTO test.lt_source_model '
        'VALUES (%s, %s, %s, %s, %s)', values)
