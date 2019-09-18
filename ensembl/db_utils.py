from sqlalchemy import create_engine, text

def get_databases_list(db_uri, query):
  """
  List databases on a specified MySQL server
  Arguments:
    db_uri : URI of MySQL server e.g. mysql://user@host:3306/
    query : optional regular expression to filter databases e.g. .*_core_.*
  """
  if (db_uri.startswith('mysql') == False):
    raise ValueError('list_databases can only work with MySQL databases')

  engine = create_engine(db_uri)
  if (query == None):
    s = text("select schema_name from information_schema.schemata")
  else:
    s = text("select schema_name from information_schema.schemata where schema_name rlike :q")
  with engine.connect() as con:
    return [str(r[0]) for r in con.execute(s, {"q": query}).fetchall()]
