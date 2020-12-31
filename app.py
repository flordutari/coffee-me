import os
import pymysql
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure database
conn = pymysql.connect(
    host = os.environ.get("DB_HOSTNAME"),
    port = 3306,
    user = os.environ.get("DB_USERNAME"),
    password = os.environ.get("DB_PASSWORD"),
    db = os.environ.get("DB_ID"),
    cursorclass = pymysql.cursors.DictCursor
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for email
        email = request.form.get("email")
        db = conn.cursor()
        db.execute("SELECT * FROM `coffee-me`.users WHERE email = %s",
                    (email))
        rows = db.fetchall()

        # Ensure email exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid email and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        conn.commit()
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to index
    return redirect("/")

@app.route("/projects")
@login_required
def projects():
    return render_template("projects.html")

@app.route("/signup", methods=["POST"])
def signup():
    # Ensure name and lastname were submitted
    if not request.form.get("name") or not request.form.get("lastname"):
        return apology("must provide name and lastname", 403)

    # Ensure user email was submitted
    if not request.form.get("email"):
        return apology("must provide an email", 403)

    # Ensure password was submitted
    elif not request.form.get("password"):
        return apology("must provide password", 403)

    # Query database for email
    email = request.form.get("email")
    db = conn.cursor()
    db.execute("SELECT * FROM `coffee-me`.users WHERE email = %s",
                (email))
    rows = db.fetchall()

    # Ensure that email doesn't exist
    if len(rows) > 0:
        return apology("The email provided already exists! choose another please", 403)

    hash = generate_password_hash(request.form.get("password"))
    # Query database to create user
    db.execute("INSERT INTO `coffee-me`.users (email, hash) VALUES (%s, %s)",
                (email, hash))

    conn.commit()
    # Redirect user to login
    return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)
