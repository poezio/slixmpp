''' Database helper functions '''


def table_exists(db_con, name):
    """ Check if the specified table exists in the db. """

    query = """ SELECT name FROM sqlite_master
            WHERE type='table' AND name=?;
        """
    return db_con.execute(query, (name, )).fetchone() is not None


def user_version(db_con):
    """ Return the value of PRAGMA user_version. """
    return db_con.execute('PRAGMA user_version').fetchone()[0]
