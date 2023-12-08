from datetime import date, datetime

import bcrypt


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


def insertNewServiceLocation(ctx, cursor, data):
    # Fetch all data submitted
    addr = data['addr']
    unit = data['unit']
    square_ft = float(data['square_ft'])
    num_bedrooms = int(data['num_bedrooms'])
    num_occupants = int(data['num_occupants'])
    date_owned = datetime.strptime(data['date_owned'], '%Y-%m-%d').date()
    zipcode = data['zipcode']

    # insert into DB and commit
    query = ("INSERT INTO ServiceLocations (addr, unit, square_ft, bedrooms, occupants, date_owned, zipcode) VALUES (%s, %s, %s, %s, %s, %s, %s)")
    cursor.execute(query, (addr, unit, square_ft, num_bedrooms, num_occupants, date_owned.strftime('%Y-%m-%d'), zipcode))

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
    pass

# TODO - is supporting concurrent access to DB necessary?