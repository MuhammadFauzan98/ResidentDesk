import sqlite3
from flask import Blueprint, session, redirect, render_template, request
from .utils import login_required, db_connection

routes = Blueprint('routes', __name__)

@routes.route('/')
def index():
    return render_template("index.html")

@routes.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        dbcon = db_connection()
        cursor = dbcon.cursor()

        cursor.execute("SELECT * FROM users WHERE name = ?", (username,))
        row = cursor.fetchall()

        if len(row) != 1 or row[0]['password_hash'] != password:
            dbcon.close()
            return "error: invalid username or password"
        
        session['user_id'] = row[0]['id']

        cursor.close()
        dbcon.close()

        return redirect("/admin-dashboard") if (row[0]['role'] == 'admin') else redirect("/dashboard")



    else:
        return render_template("login.html")
    
@routes.route('/logout')
def logout():
    session.clear()
    return redirect("/")