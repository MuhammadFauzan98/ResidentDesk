import os
import sqlite3
from functools import wraps
from flask import session, redirect

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    
    return decorated_function


def db_connection():
    BASE_DIR = os.path.abspath(os.path.dirname("database.db"))
    connection = sqlite3.connect(os.path.join(BASE_DIR, "database.db"))
    connection.row_factory = sqlite3.Row
    return connection


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS