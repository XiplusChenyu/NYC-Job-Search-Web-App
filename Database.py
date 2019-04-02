from sqlalchemy import *

# Set up Database
DB_USER = "--------"
DB_PASSWORD = "------------"
DB_SERVER = "ny---------------st-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/n---------job"
engine = create_engine(DATABASEURI)

# Test Database
# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
