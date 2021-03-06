import sqlite3
from flask import g, session, redirect
from functools import wraps



def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def login_required_admin(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("admin_id") is None:
            return "403 Forbidden", 403
        return f(*args, **kwargs)
    return decorated_function

# connect to database flask way
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('note.db')
        db.row_factory = sqlite3.Row
    return db

def con():
    con= get_db().cursor()
    return con


def make_list(semesters):
    """ create new new dict of semester as key and subject as value and
        and append to list and return list
    """

    # connection
    db = con()

    # variable declaration
    temp_list=[]
    n_list=[]
    n_dict={}

    for semester in semesters:
        # qerry this sub as per semester id
        subjects = db.execute("SELECT subject_id, subject_title FROM subjects WHERE semester_id =?", (semester['id'],)).fetchall()

        for sub in subjects:
            temp_list.append(sub)

        n_dict[semester["title"]]=temp_list
        n_list.append(n_dict)
        # make empty
        n_dict={}
        temp_list=[]

    return n_list


def format_date(date):
    # formats the data e.g 09/10/2018 to 2018-10-09
    formated_date = date.split("/")
    formated_date.reverse()
    formated_date = '-'.join(formated_date)
    return formated_date

