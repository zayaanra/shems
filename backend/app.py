from flask import Flask, render_template, request, redirect, flash, jsonify, url_for, make_response, session
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies, jwt_required, get_jwt_identity

import mysql.connector

import db

app = Flask(__name__, template_folder='../frontend/templates')
app.config['JWT_SECRET_KEY'] = 'secret'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']

jwt = JWTManager(app)

ctx = mysql.connector.connect(host="localhost", user="root", passwd="password", database="shems")
cursor = ctx.cursor(prepared=True)

# TODO - insert service location
# TODO - insert smart device
# TODO - escape html

# TODO - this route should only be accessible to those with an auth token (logged in)
@app.route("/home", methods=["GET"])
@jwt_required()
def home():
    # TODO - fill in with customer data
    name = get_jwt_identity()
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # If the user submitted data, we'll try to authenticate them.
    # If authentication fails, we return 401 error. If successful, log the user in.
    if request.method == "POST":
        success = db.authenticate(cursor, request.form)
        if success:
            access_token = create_access_token(identity=request.form['username'])
            refresh_token = create_refresh_token(identity=request.form['username'])

            response = make_response("Logged In!", 200)
            set_access_cookies(response, access_token)
            set_refresh_cookies(response, refresh_token)
            return response
        else:
            return make_response("Bad username or password", 401)
    else:
        # If it's a GET request, just return the login page.
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # If the user submitted data, we'll insert the new customer into the DB if possible.
    # Then, return a response.
    if request.method == "POST":
        success = db.insertCustomer(ctx, cursor, request.form)
        if success:
            return redirect("/login", code=302)
        else:
            return make_response("Register failed. Either the passwords do not match, password too short (should be > 5 in length), or the name already exists in the database.", 400)
    else:
        # If it's a GET request, just return the register page.
        return render_template("register.html")

@app.route("/new-service-location", methods=["POST"])
def new_service_location():
    db.insertNewServiceLocation(ctx, cursor, request.form)
    return redirect("/home", code=302)

@app.route("/new-smart-device", methods=["POST"])
def new_smart_device():
    db.insertNewSmartDevice(ctx, cursor, request.form)
    return redirect("/home", code=302)

@app.route("/enroll-device", methods=["POST"])
@jwt_required()
def enroll_device():
    # TODO - fix csrf token
    db.enrollDevice(ctx, cursor, request.form, get_jwt_identity())




if __name__ == "__main__":
    app.run(debug=True)
    cursor.close()
    ctx.close()