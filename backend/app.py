from flask import Flask, render_template, request, redirect, flash, jsonify, url_for, make_response, session
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies, jwt_required, get_jwt_identity

import mysql.connector
import plotly_express as px
import pandas as pd
import logging

import db

app = Flask(__name__, template_folder='../frontend/templates')
app.config['JWT_SECRET_KEY'] = 'secret'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']

# TODO - fix csrf token
# NOTE - Unsafe CSRF.
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
# app.config['JWT_CSRF_CHECK_FORM'] = True
# app.config['JWT_CSRF_IN_COOKIES'] = True

# NOTE - When inserting new data, Flask doesn't seem to receive the changes until actual code is changed (which results in the Flask app refreshing itself)
# So, when demo'ing if needed, just make sure to edit the code (add a space or something) to refresh the app.

jwt = JWTManager(app)

ctx = mysql.connector.connect(host="localhost", user="root", passwd="password", database="shems")
cursor = ctx.cursor(prepared=True)

@app.route("/view", methods=["GET", "POST"])
@jwt_required()
def view():
    name = get_jwt_identity()
    # If POST request, reply with the appropiate plot.
    if request.method == "POST":
        form_name = request.form['form_name']
        if form_name == 'energy_consumption_time':
            # Now, with the fetched data for this view, we'll create a plot (bar graph) to represent the user data.
            # Return the HTML template with the plot inserted into it.
            x, y = db.fetchEnergyConsumptionByTime(cursor, request.form, name)
            df = pd.DataFrame({'Date': x, 'Energy Consumption': y})
            fig = px.bar(df, x='Date', y='Energy Consumption', orientation='v', title='Energy Consumption by date')
            fig.update_yaxes(range=[0, 100])
            plot_content = fig.to_html(full_html=False)
            return render_template("view.html", plot_content=plot_content)
        elif form_name == 'energy_consumption_device':
            # With the fetched data, we'll create a pie chart to represent the user data.
            # Return the HTML template with the pie chart inserted into it.
            data = db.fetchEnergyConsumptionByDevice(cursor, name)

            df = pd.DataFrame(data, columns=['Device Type', 'Percentage'])
            fig = px.pie(df, names='Device Type', values='Percentage', title='Energy Consumption by device type as percentage of total energy consumption')
            plot_content = fig.to_html(full_html=False)
            return render_template("view.html", plot_content=plot_content)
        elif form_name == 'energy_prices_zipcode':
            # With the fetched data, we'll create a line graph to represent the user data.
            # Each line represents the zip code of the customer's owned service locations and it's pricing over a selected time period.
            # Return the HTML template with the pie chart inserted into it.
            data = db.fetchEnergyPricingByZipcode(cursor, request.form, name)
            df_list = []
            for z, pts in data.items():
                line = pd.DataFrame(pts, columns=['Date', 'Energy Price'])
                line['Zip Code'] = z
                df_list.append(line)
            df = pd.concat(df_list, ignore_index=True)
            fig = px.line(df, x='Date', y='Energy Price', color='Zip Code', title='Energy Pricing by zip code over time', markers=True)
            fig.update_yaxes(range=[0, 100])
            plot_content = fig.to_html(full_html=False)
            return render_template("view.html", plot_content=plot_content)
        elif form_name == 'energy_consumption_location':
            # With the fetched data, create a bar graph to represent the user data.
            # Return the HTML template with the bar graph inserted into it.
            x, y = db.fetchEnergyConsumptionByServiceLocation(cursor, name)
            df = pd.DataFrame({'Service Location': x, 'Energy Consumption': y})
            fig = px.bar(df, x='Service Location', y='Energy Consumption', orientation='v', title='Energy Consumption by service location')
            fig.update_yaxes(range=[0, 100])
            plot_content = fig.to_html(full_html=False)
            return render_template("view.html", plot_content=plot_content)

    return render_template("view.html")

@app.route("/home", methods=["GET"])
@jwt_required()
def home():
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
@jwt_required()
def new_service_location():
    # Insert new service location
    db.insertNewServiceLocation(ctx, cursor, request.form, get_jwt_identity())
    return redirect("/home", code=302)

@app.route("/remove-service-location", methods=["POST"])
@jwt_required()
def remove_service_location():
    # Remove service location
    db.removeServiceLocation(ctx, cursor, request.form, get_jwt_identity())
    return redirect("/home", code=302)

@app.route("/view-service-locations", methods=["POST"])
@jwt_required()
def view_service_locations():
    result = db.viewServiceLocations(cursor, get_jwt_identity())
    return render_template("servicelocations.html", table_content=result)

@app.route("/enroll-device", methods=["POST"])
@jwt_required()
def enroll_device():
    # Enroll a new device
    db.enrollDevice(ctx, cursor, request.form, get_jwt_identity())
    return redirect("/home", code=302)

@app.route("/remove-enrolled-device", methods=["POST"])
@jwt_required()
def remove_enrolled_device():
    db.removeEnrolledDevice(ctx, cursor, request.form, get_jwt_identity())
    return redirect("/home", code=302)

@app.route("/view-enrolled-devices", methods=["POST"])
@jwt_required()
def view_enrolled_devices():
    result = db.viewEnrolledDevices(cursor, get_jwt_identity())
    return render_template("enrolleddevices.html", table_content=result)


if __name__ == "__main__":
    app.run(debug=True)
    cursor.close()
    ctx.close()