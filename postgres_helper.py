from typing import Tuple, List
import resources as res
import psycopg2

"""Organize DB functions in one file to make repeated accesses easier"""


def setup_db():
    con = psycopg2.connect(res.DATABASE_URL, sslmode='require')
    print(f"Database opened.")
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS cinemas (server_id TEXT NOT NULL UNIQUE, text_id TEXT NOT NULL, voice_id TEXT NOT NULL, PRIMARY KEY(voice_id, server_id, text_id));')
    cur.execute('CREATE TABLE IF NOT EXISTS movies (m_id TEXT NOT NULL, m_name TEXT NOT NULL, m_release_year TEXT NOT NULL, m_img TEXT, m_link TEXT, PRIMARY KEY(m_id));')
    cur.execute('CREATE TABLE IF NOT EXISTS users (disc_id TEXT NOT NULL UNIQUE, lbxd_id TEXT NOT NULL UNIQUE, PRIMARY KEY(disc_id));')
    cur.execute('CREATE TABLE IF NOT EXISTS watchlist (lbxd_id TEXT NOT NULL, movie_id TEXT NOT NULL, FOREIGN KEY(movie_id) REFERENCES movies(m_id) ON DELETE CASCADE, FOREIGN KEY(lbxd_id) REFERENCES users(lbxd_id) ON DELETE CASCADE, PRIMARY KEY(lbxd_id, movie_id));')
    con.commit()
    con.close()


def execute(sql, values: Tuple, fetch=False):
    """Executes SQL command binding values to it.
    fetch_one = True -> fetchone
    fetch_one = False -> fetchall
    """
    result = None
    db = psycopg2.connect(res.DATABASE_URL, sslmode='require')
    cursor = db.cursor()
    #sql = 'SELECT * FROM users WHERE disc_id = ?'
    cursor.execute(sql, values)
    if fetch:
        result = cursor.fetchone()

    db.commit()
    cursor.close()
    db.close()

    return result


def fetch_user(user_id):
    user_id = str(user_id)
    """Returns:
    - The Discord ID for the given LBXD User
    - The LBXD ID for the given Discord User
    - None if no user was found"""
    db = psycopg2.connect(res.DATABASE_URL, sslmode='require')
    cursor = db.cursor()
    if user_id.isnumeric():  # -> Discord ID
        is_discord = True
        sql = "SELECT * FROM users WHERE disc_id = %s"
    else:
        is_discord = False
        sql = "SELECT * FROM users WHERE lbxd_id = %s"

    cursor.execute(sql, (user_id,))
    result = cursor.fetchone()

    db.commit()
    cursor.close()
    db.close()
    if is_discord:
        return result[1] if result else None  # Return LBXD
    else:
        return result[0] if result else None  # Redurn DISC


def fetch_users() -> List:  # TODO this should probably be removed
    """Returns a list of all Users in the database (disc_id, lbxd_id)"""
    db = psycopg2.connect(res.DATABASE_URL, sslmode='require')
    cursor = db.cursor()
    users = cursor.execute("SELECT * FROM users")
    if users:
        users = cursor.fetchall()
    db.commit()
    cursor.close()
    db.close()
    return users


def fetch_links_from_userlist(user_list: List) -> List:
    """Takes a list of Members on a server and returns the lbxd links found in the db for those"""
    if not user_list:  # Empty or None
        return []

    user_tuple = tuple([str(member.id) for member in user_list])  # ID Tuple (2552747, 235626, 62742, etc)
    db = psycopg2.connect(res.DATABASE_URL, sslmode='require')
    cursor = db.cursor()
    sql = f"SELECT * FROM users WHERE disc_id IN {user_tuple}"
    cursor.execute(sql)
    users = cursor.fetchall()
    db.commit()
    cursor.close()
    db.close()
    return users


def fetch_cinemas(id):
    id = str(id)
    """Returns the Cinema ID (text, voice) for the given server or None if there isn't one"""
    db = psycopg2.connect(res.DATABASE_URL, sslmode='require')
    cursor = db.cursor()

    cursor.execute("SELECT text_id, voice_id FROM cinemas WHERE server_id = %s", (id,))
    server = cursor.fetchone()
    cursor.execute("SELECT text_id, voice_id FROM cinemas WHERE voice_id = %s", (id,))
    voice = cursor.fetchone()
    cursor.execute("SELECT text_id, voice_id FROM cinemas WHERE text_id = %s", (id,))
    text = cursor.fetchone()

    result = server if server else voice if voice else text if text else None
    db.commit()
    cursor.close()
    db.close()
   # If channel found in DB but not on Server, return Null
    return (result[0], result[1]) if result else None


def delete_cinemas(id):
    id = str(id)
    """Takes a channel (text or voice) or server ID that will be used to delete a cinema linking from the database"""
    db = psycopg2.connect(res.DATABASE_URL, sslmode='require')
    cursor = db.cursor()

    cursor.execute(
        "SELECT server_id, voice_id, text_id FROM cinemas WHERE server_id = %s OR voice_id = %s OR text_id = %s", (id, id, id))
    result = cursor.fetchone()
    if result:
        cursor.execute("DELETE FROM cinemas WHERE server_id = %s OR voice_id = %s OR text_id = %s", (id, id, id))
    # else there is probably an error
    db.commit()
    cursor.close()
    db.close()
