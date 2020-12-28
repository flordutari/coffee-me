import os
from flaskext.mysql import MySQL
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
app.config["MYSQL_HOST"] = os.environ.get("DB_HOSTNAME")
app.config["MYSQL_USER"] = os.environ.get("DB_USERNAME")
app.config["MYSQL_PASSWORD"] = os.environ.get("DB_PASSWORD")
app.config["MYSQL_DB"] = os.environ.get("DB_ID")

mysql = MySQL(app)
conn = mysql.connect()
cursor =conn.cursor()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    # User reached route via POST
    if request.method == "POST":

        # Ensure user email was submitted
        if not request.form.get("email"):
            return apology("must provide an email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for email
        rows = cursor.execute("SELECT * FROM users WHERE email = :email",
                        email = request.form.get("email"))

        # Ensure that email doesn't exist
        if len(rows) > 0:
            return apology("The email provided already exists! choose another please", 403)

        # Query database to create user
        cursor.execute("INSERT INTO users (email, hash) VALUES (:email, :hash)",
                        email = request.form.get("email"), hash=generate_password_hash(request.form.get("password")))

        # Redirect user to login
        return redirect("/login")

    # User reached route via GET
    else:
        return render_template("signup.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)
