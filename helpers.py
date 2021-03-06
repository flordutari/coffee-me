from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400, referrer=None):
    """Render message as an apology to user."""
    return render_template("apology.html",
                           code=code,
                           message=message,
                           referrer=referrer
                           ), code


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user") is None:
            if "project-" in request.referrer:
                return render_template("login.html", phrase="*You need to login before buying a coffee")
            else:
                return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
