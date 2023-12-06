from flask import Flask, render_template, request, redirect

import mysql.connector
import db

app = Flask(__name__, template_folder='../frontend/templates')

ctx = mysql.connector.connect(host="localhost", user="root", passwd="password", database="shems")
cursor = ctx.cursor(prepared=True)

# TODO - Set up authentication
# TODO - Set up cookies to stay logged in
# TODO - Set up DB

@app.route("/")
def home():
    return "Hello World!"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # TODO - Process login information (authenticate)
        success = db.authenticate(cursor, request.form)
        if success:
            # TODO - Redirect to customer's homepage and fill in with customer data
            return "Login successful"
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