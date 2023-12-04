from flask import Flask

# import mysql.connector

app = Flask(__name__)
# db = mysql.connector.connect()

# TODO - Need to set login functionality (login page)
# TODO - Need to set up a register functionality (register page)
# TODO - Set up authentication
# TODO - Set up cookies to stay logged in
# TODO - Set up DB

@app.route("/")
def home():
    return "Hello World!"