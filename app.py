import os
from cloudinary.uploader import upload
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_paginate import Pagination, get_page_args
import pymysql
import stripe
from tempfile import mkdtemp
from werkzeug.exceptions import HTTPException, InternalServerError
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

# Configure stripe
stripe_keys = {
  "secret_key": os.environ["SECRET_KEY"],
  "publishable_key": os.environ["PUBLISHABLE_KEY"]
}

stripe.api_key = stripe_keys["secret_key"]

# Configure cloudinary
app.config.from_mapping(
    CLOUDINARY_URL=os.environ["CLOUDINARY_URL"]
)

# Configure database
conn = pymysql.connect(
    host=os.environ["DB_HOSTNAME"],
    port=3306,
    user=os.environ["DB_USERNAME"],
    password=os.environ["DB_PASSWORD"],
    db=os.environ["DB_ID"],
    cursorclass=pymysql.cursors.DictCursor
)

# Check if the file is valid
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    amount = 500

    customer = stripe.Customer.create(
        email="sample@customer.com",
        source=request.form["stripeToken"]
    )

    stripe.Charge.create(
        customer=customer.id,
        amount=amount,
        currency="usd",
        description="Flask Charge"
    )

    return render_template("checkout.html", amount=amount)


@app.route("/delete-project", methods=["POST"])
def delete_project():
    # Connect db
    db = conn.cursor()

    if "project_id" in session:
        # Query database to delete the project
        db.execute("DELETE FROM `coffee-me`.projects WHERE id = %s",
                   (session["project_id"]))
        session.pop("project_id", None)

    return redirect("/my-project")


@app.route("/edit-project", methods=["POST"])
def edit_project():
    # Connect db
    db = conn.cursor()

    title = request.form.get("title")
    description = request.form.get("description")
    if request.files and request.files["image"] != request.form.get("image"):
        image = upload(request.files["image"])
    else:
        image = request.form.get("image")

    # Ensure all data was submitted
    if not (title or description):
        return apology("must provide a title and a description", 403)

    if "project_id" in session:
        # Query database to update the project
        db.execute(
            "UPDATE `coffee-me`.projectsSET title=%s, description = %s,image = %s WHERE id = %s",
            (title, description, image["url"], session["project_id"]))
    return redirect("/my-project")


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
        db.execute("SELECT * FROM `coffee-me`.users WHERE email = %s", (email))
        rows = db.fetchall()

        # Ensure email exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"],
                                                     request.form.get("password")):
            return apology("invalid email and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        db = conn.cursor()
        db.execute("SELECT * FROM `coffee-me`.projects WHERE user_id = %s",
                   session["user_id"])
        rows = db.fetchall()

        if len(rows) > 0:
            session["project_id"] = rows[0]["id"]

        conn.commit()
        # Redirect user to home page
        return redirect("/projects")

    # User reached route via GET
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to index
    return redirect("/")


@app.route("/my-project", methods=["GET", "POST"])
@login_required
def my_project():
    # Connect db
    db = conn.cursor()

    if request.method == "POST":
        user_id = session["user_id"]
        title = request.form.get("title")
        description = request.form.get("description")
        if request.files:
            image = upload(request.files["image"])

        # Ensure all data was submitted
        if not (title or description):
            return apology("must provide a title and a description", 403)

        # Query database to create project
        db.execute("INSERT INTO `coffee-me`.projects (user_id, title, description, image) VALUES (%s, %s, %s, %s)",
                   (user_id, title, description, image["url"]))
        session["project_id"] = db.lastrowid
        conn.commit()

        # Redirect user to my project
        return redirect("/my-project")
    else:
        db.execute("SELECT * FROM `coffee-me`.projects WHERE user_id = %s",
                   session["user_id"])
        project = db.fetchone()

        conn.commit()
        return render_template("my-project.html", project=project)


@app.route("/payment", methods=["GET"])
@login_required
def payment():
    if request.method == "GET":
        return render_template("payment.html", key=stripe_keys["publishable_key"])


@app.route("/project-<project_id>", methods=["GET"])
def project():
    return render_template("project.html")

@app.route("/projects", methods=["GET"])
def projects():
    title = request.args.get("title") or ""
    query = '%' + title + '%'

    # Create DB connection
    db = conn.cursor()
    # Get projects
    if title:
        db.execute("SELECT * FROM `coffee-me`.projects WHERE title LIKE %s", query)
    else:
        db.execute("SELECT * FROM `coffee-me`.projects")

    projects = db.fetchall()

    page, per_page, offset = get_page_args(page_parameter="page",
                                           per_page_parameter="per_page")
    # page = request.args.get(get_page_parameter(), type=int, default=1)
    total = len(projects)
    pagination_projects = projects[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total)
    return render_template("projects.html",
                           projects=pagination_projects,
                           page=page,
                           per_page=per_page,
                           pagination=pagination,
                           search=title
                           )


@app.route("/search", methods=["POST"])
def search_by_title():
    title = request.form.get("search")
    return redirect((url_for('projects', title=title)))


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
