# Utilities for interacting with databases
from sqlalchemy import create_engine, text

def list_databases(db_uri, query):

    if(db_uri.startswith('mysql')==False):
        raise ValueError('list_databases can only work with MySQL databases')

    engine = create_engine(db_uri)
    s = text("select schema_name from information_schema.schemata where schema_name rlike :q")
    noms = []
    with engine.connect() as con:
        return [str(r[0]) for r in con.execute(s, {"q":query}).fetchall()]
    
