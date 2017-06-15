INSERT INTO test_hazard_calculation (id, description)
VALUES (1, 'First calculation');

INSERT INTO test_hazard_calculation (id, description)
VALUES (2, 'Second calculation');

INSERT INTO test_lt_source_model 
VALUES (1, 1, 0, '{b1}', 'source_model.xml');

INSERT INTO test_lt_source_model
VALUES (2, 1, 1, '{b2}', 'source_model.xml');

INSERT INTO test_lt_source_model
VALUES (3, 2, 0, '{b11,b12}', 'other_model.xml');

INSERT INTO test_lt_source_model
VALUES (4, 2, 1, '{b21,b22}', 'other_model.xml');
