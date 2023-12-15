from datetime import date, datetime, timedelta

import bcrypt
import pandas as pd
import collections
import html

def insertCustomer(ctx, cursor, data):
    username = data['username']
    password = data['password']
    confirmed = data['confirmPassword']
    billing_addr = data['Billing']

    # if password does not equal the confirmed or password too short, registration fails
    if password != confirmed or len(password) < 5:
        return False
    
    try:
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
    except Exception as e:
        ctx.rollback()
        raise e
    

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
    addr = html.escape(data['addr'])
    unit = html.escape(data['unit'])
    square_ft = float(data['square_ft'])
    num_bedrooms = int(data['num_bedrooms'])
    num_occupants = int(data['num_occupants'])
    date_owned = datetime.strptime(data['date_owned'], '%Y-%m-%d').date()
    zipcode = html.escape(data['zipcode'])

    # Check if this service location already exists

    try:
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
    except Exception as e:
        ctx.rollback()
        raise e

def removeServiceLocation(ctx, cursor, data, user):
    # Fetch all the data submitted
    addr = html.escape(data['addr'])
    unit = html.escape(data['unit'])

    # Find the service location the user would like to delete
    q1 = ("SELECT sid FROM Customers NATURAL JOIN OwnedLocations NATURAL JOIN ServiceLocations WHERE name = %s AND addr = %s and unit = %s")
    cursor.execute(q1, (user, addr, unit))
    r1 = cursor.fetchone()
    sid = r1[0]

    try:
        # Delete the service location
        q2 = ("DELETE FROM ServiceLocations WHERE sid = %s")
        cursor.execute(q2, (sid,))

        ctx.commit()
    except Exception as e:
        ctx.rollback()
        raise e

def viewServiceLocations(cursor, user):
    # Find all service locations for this user
    query = ("SELECT addr, unit, square_ft, bedrooms, occupants, date_owned, zipcode FROM Customers NATURAL JOIN OwnedLocations NATURAL JOIN ServiceLocations WHERE name = %s")
    cursor.execute(query, (user,))
    rows = cursor.fetchall()

    result = []
    for row in rows:
        addr, unit, square_ft, bedrooms, occupants, date_owned, zipcode = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        result.append({'Address': addr, 'Unit Number': unit, 'Size (square ft)': square_ft, 'Num. of Bedrooms': bedrooms, 'Num. of Occupants': occupants, \
              'Date Owned': date_owned, 'Zip Code': zipcode})

    return result

def enrollDevice(ctx, cursor, data, user):
    # Fetch all data submitted
    dv_type = data["types"]
    mtype = data["models"]
    addr = html.escape(data["addr"])
    unit = html.escape(data["unit"])

    # Find the model ID for this type of model
    q0 = ("SELECT mid FROM Models WHERE name = %s")
    cursor.execute(q0, (mtype,))
    r0 = cursor.fetchone()
    mid = r0[0]

    # Find the device ID for this type of device
    q1 = ("SELECT did FROM Devices WHERE type = %s AND mid = %s")
    cursor.execute(q1, (dv_type, mid))
    r1 = cursor.fetchone()
    did = r1[0]

    # Find the service location and user for which this (addr, unit) belongs to
    q2 = ("SELECT sid, cid FROM Customers NATURAL JOIN OwnedLocations NATURAL JOIN ServiceLocations WHERE name = %s AND addr = %s AND unit = %s")
    cursor.execute(q2, (user, addr, unit))
    r2 = cursor.fetchone()
    sid, cid = r2[0], r2[1]

    try:
        # Insert the newly enrolled device into the DB
        q3 = ("INSERT INTO EnrolledDevices (did, sid, cid) VALUES (%s, %s, %s)")
        cursor.execute(q3, (did, sid, cid))
        
        ctx.commit()
    except Exception as e:
        ctx.rollback()
        raise e

def removeEnrolledDevice(ctx, cursor, data, user):
    dv_type = data["types"]
    model = data["models"]
    addr = html.escape(data["addr"])
    unit = html.escape(data["unit"])

    # Find cid for this customer
    query = ("SELECT cid FROM Customers WHERE name = %s")
    cursor.execute(query, (user,))
    row = cursor.fetchone()
    cid = row[0]

    # Find sid for the enrolled device
    query = ("SELECT sid FROM ServiceLocations NATURAL JOIN OwnedLocations WHERE addr = %s AND zipcode = %s")
    cursor.execute(query, (addr, unit))
    row = cursor.fetchone()
    sid = row[0]

    # Find did for the enrolled device
    query = ("SELECT did FROM Devices NATURAL JOIN Models WHERE type = %s AND name = %s")
    cursor.execute(query, (dv_type, model))
    row = cursor.fetchone()
    did = row[0]

    # Find enrolled device to remove
    query = ("SELECT rid FROM EnrolledDevices WHERE did = %s AND sid = %s AND cid = %s")
    cursor.execute(query, (did, sid, cid))
    row = cursor.fetchone()
    rid = row[0]

    try:
        # Delete the enrolled device
        query = ("DELETE FROM EnrolledDevices WHERE rid = %s")
        cursor.execute(query, (rid,))

        ctx.commit()
    except Exception as e:
        ctx.rollback()
        raise e
    
def viewEnrolledDevices(cursor, user):
    # Find all enrolled devices for this user
    query = ("SELECT addr, unit, type FROM Customers NATURAL JOIN EnrolledDevices NATURAL JOIN OwnedLocations NATURAL JOIN ServiceLocations NATURAL JOIN Devices\
             WHERE name = %s")
    cursor.execute(query, (user,))
    rows = cursor.fetchall()

    result = []
    for row in rows:
        addr, unit, dv_type = row[0], row[1], row[2]
        result.append({'Address': addr, 'Unit Number': unit, 'Device Type': dv_type})
    
    return result


def fetchEnergyConsumptionByTime(cursor, data, user):
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

    # Set up X and Y data for axes
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

def fetchEnergyConsumptionByDevice(cursor, user):
    # Get energy consumption data by device
    query = ("SELECT did, type, SUM(value) AS energy_consumption \
             FROM Customers NATURAL JOIN EnrolledDevices NATURAL JOIN Devices NATURAL JOIN Events \
             WHERE label = 'energy use' AND name = %s\
             GROUP BY did, type")
    cursor.execute(query, (user,))
    result = cursor.fetchall()

    # Go through our result set and compute the energy consumption for each device as a percentage of the total energy consumption.
    # We will view this statistic as a pie chart on the frontend.
    device_to_ec = {}
    total_energy_consumption = 0
    for row in result:
        dv_type, ec = row[1], row[2]
        device_to_ec[dv_type] = ec
        total_energy_consumption += ec
    
    data = []
    for dv_type, ec in device_to_ec.items():
        data.append((dv_type, ec/total_energy_consumption))

    return data

def fetchEnergyConsumptionByServiceLocation(cursor, user):
    # Get energy consumption data by service location
    query = ("SELECT addr, SUM(value) AS energy_consumption\
             FROM Customers NATURAL JOIN EnrolledDevices NATURAL JOIN ServiceLocations NATURAL JOIN OwnedLocations NATURAL JOIN Events\
             WHERE label = 'energy use' AND name = %s\
             GROUP BY addr")
    cursor.execute(query, (user,))
    result = cursor.fetchall()

    # Set up X and Y data for axes
    x = []
    y = []
    for row in result:
        addr, ec = row[0], row[1]
        x.append(addr)
        y.append(ec)
    
    return x, y

def fetchEnergyPricingByZipcode(cursor, data, user):
    # Fetch start/finish dates for user selected time period
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    finish_date = datetime.strptime(data['finish_date'], '%Y-%m-%d').date()

    query = ("SELECT DISTINCT zipcode, price, timestamp\
             FROM Customers NATURAL JOIN OwnedLocations NATURAL JOIN ServiceLocations NATURAL JOIN EnergyPrices\
             WHERE name = %s AND DATE(timestamp) BETWEEN %s AND %s")
    cursor.execute(query, (user, start_date, finish_date))
    result = cursor.fetchall()

    # Set up data for plotting
    data = collections.defaultdict(list)
    for row in result:
        zipcode, price, date = row
        data[zipcode].append((date, price))

    return data