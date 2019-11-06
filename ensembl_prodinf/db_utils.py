# Utilities for interacting with databases
from sqlalchemy import create_engine, text
from ensembl_prodinf.server_utils import get_file_sizes
from sqlalchemy.engine.url import make_url

def list_databases(db_uri, query):
    """
    List databases on a specified MySQL server
    Arguments:
      db_uri : URI of MySQL server e.g. mysql://user@host:3306/
      query : optional regular expression to filter databases e.g. .*_core_.*
    """
    if(db_uri.startswith('mysql')==False):
        raise ValueError('list_databases can only work with MySQL databases')

    engine = create_engine(db_uri)
    if(query == None):
        s = text("select schema_name from information_schema.schemata")
    else:
        s = text("select schema_name from information_schema.schemata where schema_name rlike :q")
    with engine.connect() as con:
        return [str(r[0]) for r in con.execute(s, {"q":query}).fetchall()]

def get_database_sizes(db_uri, query, dir_name):
    """
    List sizes of databases on a specified MySQL server
    Arguments:
      db_uri : URI of MySQL server e.g. mysql://user@host:3306/ (file system must be accessible)
      query : optional regular expression to filter databases e.g. .*_core_.*
      dir_name : location of MySQL data files on server
    """
    db_list = list_databases(db_uri, query)
    url = make_url(db_uri)
    dir_name = dir_name + '/' + str(url.port) + '/data'
    sizes = get_file_sizes(url.host, dir_name)
    return {db: sizes[db] for db in db_list if db in sizes.keys()}
