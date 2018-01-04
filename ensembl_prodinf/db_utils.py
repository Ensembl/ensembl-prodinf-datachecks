# Utilities for interacting with databases
from sqlalchemy import create_engine, text
from server_utils import get_file_sizes
from sqlalchemy.engine.url import make_url

def list_databases(db_uri, query):

    if(db_uri.startswith('mysql')==False):
        raise ValueError('list_databases can only work with MySQL databases')

    engine = create_engine(db_uri)
    s = text("select schema_name from information_schema.schemata where schema_name rlike :q")
    with engine.connect() as con:
        return [str(r[0]) for r in con.execute(s, {"q":query}).fetchall()]
    
def get_database_sizes(db_uri, query, dir_name):
    db_list = list_databases(db_uri, query)
    url = make_url(db_uri)
    dir_name = dir_name + '/' + str(url.port) + '/data'
    sizes = get_file_sizes(url.host, dir_name)
    return {db: sizes[db] for db in db_list}