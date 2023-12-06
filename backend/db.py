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


    

# TODO - is supporting concurrent access to DB necessary?