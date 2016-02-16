CREATE TABLE test_hazard_calculation (
   id SERIAL PRIMARY KEY,
   description TEXT NOT NULL);

CREATE TABLE test_lt_source_model (
   id SERIAL PRIMARY KEY,
   hazard_calculation_id INTEGER NOT NULL,
   ordinal INTEGER NOT NULL,
   sm_lt_path VARCHAR[] NOT NULL,
   sm_name VARCHAR NOT NULL);
