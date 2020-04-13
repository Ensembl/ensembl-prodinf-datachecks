from sqlalchemy import create_engine, text


def get_databases_list(server_uri, query):
    """
    List databases on a specified MySQL server
    Arguments:
      server_uri : URI of MySQL server e.g. mysql://user@host:3306/
      query : optional regular expression to filter databases e.g. .*_core_.*
    """
    if db_uri.startswith('mysql') is False:
        raise ValueError('list_databases can only work with MySQL databases')

    engine = create_engine(server_uri)
    if query is None:
        s = text("select schema_name from information_schema.schemata")
    else:
        s = text("select schema_name from information_schema.schemata where schema_name rlike :q")
    with engine.connect() as con:
        return [str(r[0]) for r in con.execute(s, {"q": query}).fetchall()]


def get_db_type(db_uri):
    """
    Retrieve the value for the 'schema_type' meta_key from a database
    Arguments:
      db_uri : URI of MySQL database e.g. mysql://user@host:3306/db_name_core_100_1
    """
    s = text("select meta_value from meta where meta_key = 'schema_type'")
    engine = create_engine(db_uri)
    with engine.connect() as con:
        row = con.execute(s).fetchone()
        return str(row[0])
