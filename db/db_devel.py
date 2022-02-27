import sqlite3 as sl
# Tutorial source: https://towardsdatascience.com/do-you-know-python-has-a-built-in-database-d553989c87bd

#### TEST ONLY ####
# Remove prior database file, if it exists (so we don't wipe our databases)
import os
if os.path.exists("es_cw1.db"):
  os.remove("es_cw1.db")

#### CODE HERE ####

# Create a database
con = sl.connect("es_cw1.db")

# Create user table
with con:
    con.execute(
        """
        CREATE TABLE current_usage (
            lock_postcode TEXT NOT NULL,
            lock_cluster_id INTEGER NOT NULL,
            lock_id INTEGER NOT NULL,
            occupied INTEGER NOT NULL,
            username TEXT REFERENCES users(username),
            bike_sn INTEGER REFERENCES bicycles(bike_sn),
            lock_time TEXT,
            expected_departure_time TEXT,
            ouid INTEGER,
            PRIMARY KEY (lock_postcode, lock_cluster_id, lock_id)
        );
        """
    )
    print("created current_usage table")

    con.execute(
        """
        CREATE TABLE cluster_coordinates (
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            lock_postcode TEXT NOT NULL REFERENCES current_usage(lock_postcode),
            lock_cluster_id INTEGER NOT NULL REFERENCES current_usage(lock_cluster_id),
            num_lock INTEGER NOT NULL,
            PRIMARY KEY(lat, lon)
        );
        """
    )
    print("created cluster_coords table")
    
    con.execute(
        """
        CREATE TABLE overall_usage (
            transaction_sn INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            lock_postcode TEXT NOT NULL REFERENCES current_usage(lock_postcode),
            lock_cluster_id INTEGER NOT NULL REFERENCES current_usage(lock_cluster_id),
            lock_id INTEGER NOT NULL REFERENCES current_usage(lock_id),
            username TEXT REFERENCES users(username),
            bike_sn INTEGER REFERENCES bicycles(bike_sn),
            in_time TEXT NOT NULL,
            stay_duration INTEGER,
            remark INTEGER
        );
        """
    )
    print("created overall_usage table")

    con.execute(
        """
        CREATE TABLE users (
            username TEXT PRIMARY KEY NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            email_flag INTEGER
        );
        """
    )
    print("created users table")
    
    con.execute(
        """
        CREATE TABLE bicycles (
            bike_sn INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            bike_name TEXT NOT NULL,
            username TEXT REFERENCES users(username)
        );
        """
    )
    print("created bicycle table")

    con.execute(
        """
        CREATE TABLE telemetry(
            serial_num INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            timestamp TEXT NOT NULL,
            data BLOB,
            lock_postcode TEXT NOT NULL REFERENCES current_usage(lock_postcode),
            lock_cluster_id INTEGER NOT NULL REFERENCES current_usage(lock_cluster_id),
            lock_id INTEGER NOT NULL REFERENCES current_usage(lock_id)
        );
        """
    )
    print("created telemetry table")

sql = """
        INSERT INTO 'cluster_coordinates' (lat, lon, lock_postcode, lock_cluster_id, num_lock) 
        VALUES (?, ?, ?, ?, ?);
"""
cluster_coordinates_data = [
    (51.498616, -0.175689, "SW72AZ", "1", 10),  # Technically this is SW72BU on Google Maps
    (51.497893, -0.175943, "SW72AZ", "2", 7),   # 
    (51.48327, -0.21455, "W68EL", "1", 5),
]

with con:
    con.executemany(sql, cluster_coordinates_data)

# initialize database with some locks
sql = """
        INSERT INTO 'current_usage' (lock_postcode, lock_cluster_id, lock_id, occupied) 
        VALUES (?, ?, ?, ?);
"""
data = [ [ (item[2], item[3], 1+i, '0') for i in range(item[4]) ] for item in cluster_coordinates_data ]
data = [item for sublist in data for item in sublist]   # Flatten list of lists

with con:
    con.executemany(sql, data)

# For creating new users
sql = "INSERT INTO users (username, email, password_hash) values(?, ?, ?);"
data = [
    ('tianyi', 'mm.aderation@gmail.com', 123),
    ('frank', 'iamattestvalue@frank.com', 456),
    ('smith', 'iamattestvalue@smith.com', 789)
]

with con:
    con.executemany(sql, data)

sql = 'INSERT INTO bicycles (bike_name, bike_sn, username) values(?, ?, ?);'
data = [
    ('giant tcr', 123, 'tianyi'),
    ('specialized aethos', 345, 'tianyi'),
    ('canyon aeroad', 99, 'smith'),
    ('triban 500', 464, 'joe'),
]

with con: con.executemany(sql, data)

# Fake some data:
from random import randint, randrange
from datetime import datetime, timedelta

# Fake some data:
sql = '''INSERT INTO overall_usage 
    (lock_postcode, lock_cluster_id, lock_id, username, bike_sn, in_time, stay_duration, remark)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    '''
    
postcodes = ['SW72AZ', 'W68EL']
usernames = ['tianyi', 'smith', 'joe']
d1 = datetime.strptime('1/1/2022 1:30 PM', '%d/%m/%Y %I:%M %p')
d2 = datetime.strptime('28/2/2022 4:50 AM', '%d/%m/%Y %I:%M %p')


def random_date(start, end):
    """
    This function will return a random datetime between two datetime 
    objects.
    """
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    date = start + timedelta(seconds=random_second)
    return datetime.strftime(date, "%Y-%m-%d %H:%M:%S")

for i in range(100):
    
    postcode_idx = randint(0,1)
    postcode = postcodes[postcode_idx]
    if postcode_idx == 0:
        cluster_id = randint(1,2)
        if cluster_id == 1:
            lock_id = randint(1, 10)
        else:
            lock_id = randint(1, 7)
    else:
        cluster_id = 1
        lock_id = randint(1,5)
    

    username_idx = randint(0,2)
    username = usernames[username_idx]
    if username_idx==0:
        bike_sn = randint(0,1)
        if bike_sn == 0: bike_sn = 123
        else: bike_sn = 345
    elif username_idx==1:
        bike_sn = 99
    else: 
        bike_sn = 464

    in_time = random_date(d1, d2)
    stay_duration = randint(300, 36000) # 5 mins to 10 hours

    remark = 0

    data = [postcode, cluster_id, lock_id, username, bike_sn, in_time, stay_duration, remark]
    print("inserting", data)

    with con:
        con.execute(sql, data)


# # Query for each bicycle ordered by user 
# with con:
#     data = con.execute("""
#         SELECT USERS.username, BICYCLES.bike_model, BICYCLES.bike_serialnum
#         FROM 'BICYCLES' 
#         INNER JOIN 'USERS' ON BICYCLES.username=USERS.username
#         WHERE USERS.username="joe"
#         ORDER BY USERS.username;
#         """)
#     for row in data:
#         print(row)