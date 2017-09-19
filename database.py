import os
import sqlite3 as sq
import json

import time

import csv_reading


def init_db():
    try:
        c = sq.connect('./alcohol_study.db')
        cur = c.cursor()

        table_query = "SELECT name FROM sqlite_master WHERE type='table';"

        if not cur.execute(table_query).fetchall():
            set_up_tables(c)

        return c
    except sq.Error:
        import sys
        sys.exit(1)


def set_up_tables(conn):
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS pictures (
      name TEXT,
      link BLOB,
      evaluated BOOLEAN,
      username TEXT,
      finished BOOLEAN
    );

    CREATE TABLE IF NOT EXISTS picture_evaluation_data (
      id INTEGER PRIMARY KEY,
      picture_name TEXT,
      shows_people BOOLEAN,
      focused_people INTEGER,
      nonfocused_people INTEGER
    );

    CREATE TABLE IF NOT EXISTS picture_focal_result_data (
      id INTEGER,
      person_from_left INTEGER NOT NULL,
      answer_1 INTEGER,
      answer_1_text TEXT,
      answer_2 INTEGER,
      answer_3 INTEGER,
      answer_4 INTEGER,
      answer_5 INT,
      answer_6 INT,
      answer_7 INT,
      answer_8 INT,
      answer_9 INT,
      answer_10 INT,
      answer_11 INT,
      answer_12 INT
    );

    CREATE UNIQUE INDEX focal_index
    ON picture_focal_result_data(id, person_from_left);

    CREATE TABLE IF NOT EXISTS picture_non_focal_result_data (
      picture_name TEXT NOT NULL,
      answers BLOB
    );
    """)

    conn.commit()


def get_next_picture():
    c = init_db()
    cur = c.cursor()

    cur.execute("""
    SELECT link, username, ROWID FROM pictures
    WHERE evaluated = 0
    AND name != ''
    LIMIT 1;
    """)

    return cur.fetchall()[0]


def get_next_user_id_picture(id):
    c = init_db()
    cur = c.cursor()

    cur.execute('''
    SELECT link, ROWID FROM pictures
    WHERE evaluated = 0
    AND name != ''
    AND pictures.username = ?
    LIMIT 1
    ''', [id])

    return cur.fetchall()


def insert_picture(c,
                   name: str,
                   link: str,
                   username: str,
                   evaluated: bool = False,
                   finished: bool = False):
    cursor = c.cursor()

    try:
        _ = cursor.execute("SELECT * FROM pictures WHERE name=?",
                           [name]).fetchall()[0][0]

    except IndexError:
        cursor.execute("INSERT INTO pictures VALUES (?, ?, ?, ?, ?);",
                       [name,
                        link,
                        1 if evaluated else 0,
                        username,
                        1 if finished else 0])

    cursor.close()
    c.commit()


def count_unevaluated_pictures():
    conn = init_db()
    c = conn.cursor()

    return c.execute(
            "SELECT count(*) FROM pictures WHERE evaluated = 0 AND name != ''") \
        .fetchall()[0][0]


def insert_picture_eval_data(form):
    shows_people = True if form['containsPeople'] == 'Yes' else False
    picture_name = form['picture_name']
    focused_people = form['focalSubjects']
    nonfocused_people = form['nonFocalSubjects']
    identifier = form['picture_id']

    c = init_db()
    cur = c.cursor()

    cur.execute("""
    INSERT INTO picture_evaluation_data VALUES (?, ?, ?, ?, ?)
    """, [identifier, picture_name, shows_people, focused_people,
          nonfocused_people])

    c.commit()

    cur.execute("""
    UPDATE pictures SET evaluated = 1 WHERE link=?
    """, [picture_name])

    c.commit()


def get_user_ids():
    conn = init_db()
    c = conn.cursor()

    raw_data = c.execute("SELECT DISTINCT username FROM pictures").fetchall()
    return [t[0] for t in raw_data]


def get_waiting_user_ids():
    conn = init_db()
    c = conn.cursor()

    raw_data = c.execute("""
    SELECT DISTINCT username
    FROM pictures INNER JOIN picture_evaluation_data
      ON pictures.link = picture_evaluation_data.picture_name
    WHERE
    pictures.evaluated = 1
    AND picture_evaluation_data.shows_people = 1
    AND pictures.finished = 0
    """).fetchall()

    return [t[0] for t in raw_data]


def get_next_relevant_picture_for_user(user_id):
    """
    Selects the userID of the next RELEVANT picture for any given userID.
    Relevancy criteria:
    - Username is the same
    - The picture actually shows people.
    - It is not yet set to 'finished'.

    :param user_id: The userID to query for, usually from the index.html selector.
    :return: The picture_id of the next relevant picture. Throws an IndexError
     if there are none.
    """

    conn = init_db()
    cur = conn.cursor()

    raw_data = cur.execute(
            """SELECT pictures.ROWID
            FROM pictures INNER JOIN picture_evaluation_data
              ON pictures.link = picture_evaluation_data.picture_name
            WHERE pictures.username=?
            AND picture_evaluation_data.shows_people = 1
            AND pictures.finished = 0
            LIMIT 1""",
            [user_id]).fetchall()

    return raw_data[0][0]


def get_evaluation_data_for_picture(picture_file_name: str):
    conn = init_db()
    cur = conn.cursor()

    raw_data = cur.execute(
            "SELECT * FROM picture_evaluation_data WHERE picture_name = ?",
            [picture_file_name]).fetchall()[0]

    try:
        fp = int(raw_data[2])
    except ValueError:
        fp = 0

    try:
        ufp = int(raw_data[3])
    except ValueError:
        ufp = 0

    return fp, ufp


def upload_csv(files, app_config):
    csv_file = files['upload']
    filename = '{}.csv'.format(time.time())
    csv_file.save(os.path.join(app_config, filename))

    csv_reading.read_data_csv(os.path.join(app_config, filename))


def get_picture_by_id(id):
    """Fetches any given picture by its rowID, effectively enumerating
    all pictures.
    Returns a tuple representing the result row. \n
    Format: (file_name, link, evaluated, user_id, finished)"""
    conn = init_db()
    cur = conn.cursor()

    return cur.execute('''
    SELECT * FROM pictures WHERE ROWID = ?
    ''', [id]).fetchall()[0]


def get_user_id_by_picture_id(picture_id):
    cur = init_db().cursor()

    return cur\
        .execute('Select username From pictures where ROWID = ?', [picture_id])\
        .fetchall()[0][0]


def get_picture_eval_data_by_id(id):
    """
    Fetches the evaluation data for the given picture ID.
    Returns a tuple containing the row. Format:
    (id, link, shows_people, focused, unfocused)
    """
    conn = init_db()
    cur = conn.cursor()

    return cur.execute('''
    select * from picture_evaluation_data where id = ?
    ''', [id]).fetchall()[0]


def get_row_by_link(picture_link):
    """Fetches the given row ID in the pictures table by link.
    :param picture_link: Metricwire link to said picture.
    """

    conn = init_db()
    cur = conn.cursor()

    return cur.execute('''
    SELECT rowID FROM pictures WHERE link = ?
    ''', [picture_link]).fetchall()[0][0]


def save_focal_survey_result(f, iteration):
    conn = init_db()
    cur = conn.cursor()

    picture_id = f['id']
    person_from_left = iteration

    q1 = f['q1']
    q1_text = ''

    if q1 == 'A family member' or q1 == 'other':
        q1_text = f['q1_textbox']

    q2 = f['q2']
    if q2 == '':
        q2 = 0

    q3 = f['q3']
    q4 = f['q4']
    q5 = f['q5']
    q6 = f['q6']
    q7 = f['q7']
    q8 = f['q8']
    q9 = f['q9']
    q10 = f['q10']
    q11 = f['q11']
    q12 = f['q12']

    cur.execute("""
    INSERT OR REPLACE INTO picture_focal_result_data VALUES (?, ?, ?, ?, ?,
     ?, ?, ?, ?, ?,
     ?, ?, ?, ?, ?)
  """, [picture_id, person_from_left, q1, q1_text, q2, q3, q4, q5, q6, q7, q8,
        q9, q10, q11, q12])

    conn.commit()


def save_nf_survey_result(f, unfocused_people):
    conn = init_db()
    cur = conn.cursor()

    d = f.to_dict()
    d['unfocusedPeople'] = unfocused_people
    picture = d['id']

    j = json.dumps(d)

    cur.execute('''
    INSERT INTO picture_non_focal_result_data VALUES (?, ?)
    ''', [picture, j])
    conn.commit()

    set_done(picture)


def get_user_for_picture_id(picture_id):
    conn = init_db()
    cur = conn.cursor()

    return cur.execute('''
    select username from pictures where ROWID = ?
    ''', [picture_id]).fetchall()[0][0]


def set_done(picture_id):
    conn = init_db()
    cur = conn.cursor()

    cur.execute('''
    UPDATE pictures SET finished = 1 WHERE ROWID=?
    ''', [picture_id])
    conn.commit()


def drop_database():
    os.remove('./alcohol_study.db')
    init_db()


def has_nf_data(picture):
    c = init_db()
    cur = c.cursor()

    isempty = cur.execute('''
    SELECT * FROM picture_non_focal_result_data WHERE picture_name = ?
    ''', [picture]).fetchall()

    return isempty != []
