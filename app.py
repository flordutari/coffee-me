import os
import re
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
COFFEE_VALUE = 3


def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/buy-coffee", methods=["POST"])
@login_required
def buy_coffee():
    referrer = get_referrer()

    # Connect db
    db = conn.cursor()
    # Find user
    db.execute("SELECT * FROM `coffee-me`.users WHERE id = %s",
               session["user"]["id"])
    user = db.fetchone()

    # Find project
    project_id = request.form["projectId"]
    db.execute("SELECT * FROM `coffee-me`.projects WHERE id = %s",
               project_id)
    project = db.fetchone()

    coffees = float(request.form["coffeesQuantity"])
    message = request.form["contributorMessage"]
    message_name = request.form["contributorName"]

    if user["cash"] - coffees * COFFEE_VALUE >= 0:
        coffees_sum = project["coffees"] + coffees
        cash_substraction = user["cash"] - coffees * COFFEE_VALUE

        # Set user cash in session
        session["user"]["cash"] = cash_substraction

        # Create transaction
        db.execute("INSERT INTO `coffee-me`.transaction(project_id, coffees, contributor, message, message_name) VALUES(%s, %s, %s, %s, %s)",
                   (project_id, coffees, user["id"], message, message_name))

        # Add coffee to project
        db.execute("UPDATE `coffee-me`.projects SET coffees = %s WHERE id = %s",
                   (coffees_sum, project_id))

        # Substract cash to user
        db.execute("UPDATE `coffee-me`.users SET cash = %s WHERE id = %s",
                   (cash_substraction, user["id"]))
    else:
        return apology("Sorry, you don't have enough cash", 403, referrer)

    return redirect(request.referrer)


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
    referrer = get_referrer()
    new_image = ""
    old_image = ""

    # Connect db
    db = conn.cursor()

    title = request.form.get("title")
    description = request.form.get("description")
    image = request.files["image"]
    if image.filename:
        new_image = upload(request.files["image"])
    else:
        old_image = request.form.get("imageHidden")

    if new_image:
        image = new_image["url"]
    elif old_image:
        image = old_image

    # Ensure all data was submitted
    if not (title or description):
        return apology("must provide a title and a description", 403, referrer)

    if "project_id" in session:
        # Query database to update the project
        db.execute(
            "UPDATE `coffee-me`.projects SET title=%s, description = %s,image = %s WHERE id = %s",
            (title, description, image, session["project_id"]))
    return redirect("/my-project")


@app.route("/login", methods=["GET", "POST"])
def login():
    referrer = get_referrer()

    # Forget any user
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403, referrer)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403, referrer)

        # Query database for email
        email = request.form.get("email")
        db = conn.cursor()
        db.execute("SELECT * FROM `coffee-me`.users WHERE email = %s", (email))
        user = db.fetchone()

        # Ensure email exists and password is correct
        if not user or not check_password_hash(user["hash"], request.form.get("password")):
            return apology("invalid email and/or password", 403, referrer)

        # Remember which user has logged in
        user = {
            "id": user["id"],
            "cash": user["cash"],
        }
        session['user'] = user

        db = conn.cursor()
        db.execute("SELECT * FROM `coffee-me`.projects WHERE user_id = %s",
                   session["user"]["id"])
        project = db.fetchone()

        if project:
            session["project_id"] = project["id"]

        session["referrer"] = request.url

        conn.commit()
        # Redirect user to referrer if there is one
        if referrer:
            return redirect(referrer)
        else:
            return redirect("/")
    # User reached route via GET
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    # Forget any user
    session.clear()

    # Redirect user to index
    return redirect("/")


@app.route("/my-project", methods=["GET", "POST"])
@login_required
def my_project():
    referrer = get_referrer()

    # Connect db
    db = conn.cursor()

    if request.method == "POST":
        user_id = session["user"]["id"]
        title = request.form.get("title")
        description = request.form.get("description")
        if request.files:
            image = upload(request.files["image"])

        # Ensure all data was submitted
        if not (title or description):
            return apology("must provide a title and a description", 403, referrer)

        # Query database to create project
        db.execute("INSERT INTO `coffee-me`.projects (user_id, title, description, image) VALUES (%s, %s, %s, %s)",
                   (user_id, title, description, image["url"]))
        session["project_id"] = db.lastrowid
        conn.commit()

        # Redirect user to my project
        return redirect("/my-project")
    else:
        db.execute("SELECT * FROM `coffee-me`.projects WHERE user_id = %s",
                   session["user"]["id"])
        project = db.fetchone()

        conn.commit()
        session["referrer"] = request.url
        return render_template("my-project.html", project=project)


@app.route("/payment")
@login_required
def payment():
    if request.method == "GET":
        return render_template("payment.html",
                               key=stripe_keys["publishable_key"])


@app.route("/project-<string:id>", methods=["GET"])
def project(id):
    # Connect db
    db = conn.cursor()
    # Get project info
    db.execute("SELECT * FROM `coffee-me`.projects WHERE id = %s", id)
    project = db.fetchone()

    # Get project messages
    db.execute("SELECT coffees, message, message_name FROM `coffee-me`.transaction WHERE project_id = %s", id)
    messages = db.fetchall()

    conn.commit()
    # Save get referrer in session
    session["referrer"] = request.url
    return render_template("project.html", project=project, messages=messages)


@app.route("/projects")
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

    total = len(projects)
    pagination_projects = projects[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total)

    # Save get referrer in session
    session["referrer"] = request.url

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


@app.route("/signup", methods=["GET", "POST"])
def signup():
    referrer = get_referrer()
    # User reached route via POST
    if request.method == "POST":

        # Ensure name and lastname were submitted
        if not request.form.get("name") or not request.form.get("lastname"):
            return apology("Must provide name and lastname", 403, referrer)

        # Ensure user email was submitted
        if not request.form.get("email"):
            return apology("Must provide an email", 403, referrer)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Must provide password", 403, referrer)

        # Query database for email
        email = request.form.get("email")

        # Check email format
        email_match = re.match(r"\w+@\w+\.\w+", email)
        if not email_match:
            return apology("Email format is not correct", 403, referrer)

        # Validate password
        password = request.form.get("password")
        password_match = re.match(r"^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%^&-+=()])(?=\\S+$).{8, 20}$", password)
        if not password_match:
            return apology("Password must contain 8 digits, an uppercase letter, a lowercase letter and a number", 403, referrer)

        db = conn.cursor()
        db.execute("SELECT * FROM `coffee-me`.users WHERE email = %s",
                   (email))
        rows = db.fetchall()

        # Ensure that email doesn't exist
        if len(rows) > 0:
            return apology("The email provided already exists! choose another please", 403, referrer)

        hash = generate_password_hash(password)
        # Query database to create user
        db.execute("INSERT INTO `coffee-me`.users (email, hash) VALUES (%s, %s)",
                   (email, hash))

        conn.commit()

        # Redirect user to index
        return redirect("/")

        # User reached route via GET
    else:
        return render_template("signup.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


def get_referrer():
    if "referrer" in session:
        referrer = session["referrer"]
    else:
        referrer = None
    return referrer
