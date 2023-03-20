from flask import render_template
from frontend import app
@app.route("/")
def hello_world():
    return render_template("base.html")