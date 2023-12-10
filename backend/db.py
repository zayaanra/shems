from datetime import date, datetime, timedelta

import bcrypt
import pandas as pd

def insertCustomer(ctx, cursor, data):
    username = data['username']
    password = data['password']
    confirmed = data['confirmPassword']
    billing_addr = data['Billing']

    # if password does not equal the confirmed or password too short, registration fails
    if password != confirmed or len(password) < 5:
        return False
    
    # if a registered customer already exists under this name, registration fails
    query = ("SELECT * FROM Customers WHERE name = %s")
    cursor.execute(query, (username,))
    result = cursor.fetchall()
    if result:
        return False
    
    # salt + hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    # insert into DB and commit
    query = ("INSERT INTO Customers (name, billing_addr, password) VALUES (%s, %s, %s)")
    cursor.execute(query, (username, billing_addr, hashed.decode("utf-8")))

    ctx.commit()

    return True

def authenticate(cursor, data):
    username = data['username']
    password = data['password']

    # if the given customer doesn't exist, login fails
    query = ("SELECT * FROM Customers WHERE name = %s")
    cursor.execute(query, (username,))
    result = cursor.fetchall()
    if not result:
        return False
    
    # Check if user gave us correct credentials
    for row in result:
        hashed = row[3]
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    return result


def insertNewServiceLocation(ctx, cursor, data, user):
    # Fetch all data submitted
    addr = data['addr']
    unit = data['unit']
    square_ft = float(data['square_ft'])
    num_bedrooms = int(data['num_bedrooms'])
    num_occupants = int(data['num_occupants'])
    date_owned = datetime.strptime(data['date_owned'], '%Y-%m-%d').date()
    zipcode = data['zipcode']

    # insert into DB and commit
    q1 = ("INSERT INTO ServiceLocations (addr, unit, square_ft, bedrooms, occupants, date_owned, zipcode) VALUES (%s, %s, %s, %s, %s, %s, %s)")
    cursor.execute(q1, (addr, unit, square_ft, num_bedrooms, num_occupants, date_owned.strftime('%Y-%m-%d'), zipcode))

    # Find the user this service location is being registered under
    q2 = ("SELECT cid FROM Customers WHERE name = %s")
    cursor.execute(q2, (user,))
    r1 = cursor.fetchone()
    cid = r1[0]

    # Find the sid of the newly registered service location
    q3 = ("SELECT sid FROM ServiceLocations WHERE addr = %s AND unit = %s")
    cursor.execute(q3, (addr, unit))
    r2 = cursor.fetchone()
    sid = r2[0]

    # Insert into OwnedLocations
    q4 = ("INSERT INTO OwnedLocations (cid, sid) VALUES (%s, %s)")
    cursor.execute(q4, (cid, sid))

    ctx.commit()

def insertNewSmartDevice(ctx, cursor, data):
    # Fetch all data submitted
    dv_type = data["type"]
    model = data["models"]

    # Get the model ID for the submitted model
    query = ("SELECT mid FROM Models WHERE name = %s")
    cursor.execute(query, (model,))
    result = cursor.fetchone()
    

    # insert into DB and commit
    query = ("INSERT INTO Devices (type, mid) VALUES (%s, %s)")
    cursor.execute(query, (dv_type, result[0]))

    ctx.commit()

def enrollDevice(ctx, cursor, data, user):
    # Fetch all data submitted
    dv_type = data["type"]
    addr = data["addr"]
    unit = data["unit"]

    # Find the device ID for this type of device
    q1 = ("SELECT did FROM Devices WHERE type = %s")
    cursor.execute(q1, (dv_type,))
    r1 = cursor.fetchone()
    did = r1[0]

    # Find the service location and user for which this (addr, unit) belongs to
    q2 = ("SELECT sid, cid FROM Customers NATURAL JOIN ServiceLocations WHERE name = %s AND addr = %s AND unit = %s")
    cursor.execute(q2, (user, addr, unit))
    r2 = cursor.fetchone()
    sid, cid = r2[0], r2[1]

    # Insert the newly enrolled device into the DB
    q3 = ("INSERT INTO EnrolledDevices (did, sid, cid) VALUES (%s, %s, %s)")
    cursor.execute(q3, (did, sid, cid))
    
    ctx.commit()

def fetchEnergyConsumptionByMonth(cursor, data, user):
    # Fetch start/finish dates for user selected time period
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    finish_date = datetime.strptime(data['finish_date'], '%Y-%m-%d').date()
    
    # Get energy consumption data for time period by month
    query = ("SELECT DATE(timestamp), SUM(value) AS energy_consumption \
             FROM Customers NATURAL JOIN EnrolledDevices NATURAL JOIN Events \
             WHERE label = 'energy use' AND DATE(timestamp) BETWEEN %s AND %s AND name = %s\
             GROUP BY DATE(timestamp)\
             ")
    cursor.execute(query, (start_date, finish_date, user))
    result = cursor.fetchall()

    x = pd.date_range(start_date, finish_date-timedelta(days=1),freq='d')
    y = [0] * len(x)
    for row in result:
        date, value = row
        date = pd.Timestamp(date)
        try:
            idx = x.get_loc(date)
            y[idx] = value
        except KeyError as e:
            print(f"KeyError: {e}, Date: {date}")

    return x, y

# TODO - is supporting concurrent access to DB necessary?