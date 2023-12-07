from flask import Flask, render_template, request, redirect, flash

import mysql.connector
import db

app = Flask(__name__, template_folder='../frontend/templates')

ctx = mysql.connector.connect(host="localhost", user="root", passwd="password", database="shems")
cursor = ctx.cursor(prepared=True)

# TODO - insert service location
# TODO - insert smart device

# TODO - this route should only be accessible to those with an auth token (logged in)
@app.route("/home")
def home():
    if request.method == "POST":
        form_name = request.form['form_name']
        if form_name == 'new_service_location':
            # TODO - insert new service location
            pass
        elif form_name == 'new_smart_device':
            # TODO - insert new smart device
            pass
        elif form_name == 'enrolled_device':
            # TODO - insert new enrolled device
            pass
    else:
        # TODO - fill in with customer data
        return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        success = db.authenticate(cursor, request.form)
        if success:
            return redirect("/home", code=302)
        else:
            return "Login failed"
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        success = db.insertCustomer(ctx, cursor, request.form)
        if success:
            return redirect("/login", code=302)
        else:
            return "Register failed. Either the passwords do not match, password too short (should be > 5 in length), or the name already exists in the database."
    else:
        return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)
    cursor.close()
    ctx.close()