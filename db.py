import sqlite3

from typing import Tuple, List
import resources as res

"""Organize DB functions in one file to make repeated accesses easier"""


def execute(sql, values: Tuple, fetch_one=True):
    """Executes SQL command binding values to it.
    fetch_one = True -> fetchone
    fetch_one = False -> fetchall
    """
    db = sqlite3.connect(res.DB_NAME)
    cursor = db.cursor()
    #sql = 'SELECT * FROM users WHERE disc_id = ?'
    cursor.execute(sql, values)
    if fetch_one:
        result = cursor.fetchone()
    else:
        result = cursor.fetchall()

    db.commit()
    cursor.close()
    db.close()

    return result


def fetch_user(user_id):
    """Returns:
    - The Discord ID for the given LBXD User
    - The LBXD ID for the given Discord User
    - None if no user was found"""
    db = sqlite3.connect(res.DB_NAME)
    cursor = db.cursor()
    if str(user_id).isnumeric():  # -> Discord ID
        is_discord = True
        sql = 'SELECT * FROM users WHERE disc_id = ?'
    else:
        is_discord = False
        sql = 'SELECT * FROM users WHERE lbxd_id = ?'

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
    db = sqlite3.connect(res.DB_NAME)
    cursor = db.cursor()
    users = cursor.execute('SELECT * FROM users').fetchall()
    db.commit()
    cursor.close()
    db.close()
    return users


def fetch_links_from_userlist(user_list: List) -> List:
    """Takes a list of Members on a server and returns the lbxd links found in the db for those"""
    if not user_list:  # Empty or None
        return []

    user_tuple = tuple([member.id for member in user_list])  # ID Tuple (2552747, 235626, 62742, etc)
    db = sqlite3.connect(res.DB_NAME)
    cursor = db.cursor()
    sql = f'SELECT * FROM users WHERE disc_id IN {user_tuple}'
    users = cursor.execute(sql).fetchall()
    db.commit()
    cursor.close()
    db.close()
    return users


def fetch_cinemas(id):
    """Returns the Cinema ID (text, voice) for the given server or None if there isn't one"""
    db = sqlite3.connect(res.DB_NAME)
    cursor = db.cursor()

    server = cursor.execute('SELECT text_id, voice_id FROM cinemas WHERE server_id = ?', (id,)).fetchone()
    voice = cursor.execute('SELECT text_id, voice_id FROM cinemas WHERE voice_id = ?', (id,)).fetchone()
    text = cursor.execute('SELECT text_id, voice_id FROM cinemas WHERE text_id = ?', (id,)).fetchone()

    result = server if server else voice if voice else text if text else None
    db.commit()
    cursor.close()
    db.close()
   # If channel found in DB but not on Server, return Null
    return (result[0], result[1]) if result else None


def delete_cinemas(id):
    """Takes a channel (text or voice) or server ID that will be used to delete a cinema linking from the database"""
    db = sqlite3.connect(res.DB_NAME)
    cursor = db.cursor()

    """server = cursor.execute('SELECT * FROM cinemas WHERE server_id = ?', (id,)).fetchone()
    voice = cursor.execute('SELECT * FROM cinemas WHERE voice_id = ?', (id,)).fetchone()
    text = cursor.execute('SELECT * FROM cinemas WHERE text_id = ?', (id,)).fetchone()
    if server:
        cursor.execute('DELETE FROM cinemas WHERE server_id = ?', (id,))
    elif voice:
        cursor.execute('DELETE FROM cinemas WHERE voice_id = ?', (id,))
    elif text:
        cursor.execute('DELETE FROM cinemas WHERE text_id = ?', (id,))"""
    result = cursor.execute(
        'SELECT server_id, voice_id, text_id FROM cinemas WHERE server_id = ? OR voice_id = ? OR text_id = ?', (id, id, id)).fetchone()
    if result:
        cursor.execute('DELETE FROM cinemas WHERE server_id = ? OR voice_id = ? OR text_id = ?', (id, id, id))
    # else there is probably an error
    db.commit()
    cursor.close()
    db.close()
