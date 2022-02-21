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
            password_hashed TEXT NOT NULL
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

sql = """
        INSERT INTO 'cluster_coordinates' (lat, lon, lock_postcode, lock_cluster_id, num_lock) 
        VALUES (?, ?, ?, ?, ?);
"""
cluster_coordinates_data = [
    (51.498508, -0.176752, "SW72AZ", "1", 10),
    (51.498500, -0.176800, "SW72AZ", "2", 7),
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

# # For creating new users
# sql = "INSERT INTO 'USERS' (username, password_hash) values(?, ?);"
# data = [
#     ('joe', 123),
#     ('frank', 123),
#     ('smith', 123)
# ]

# with con:
#     con.executemany(sql, data)

# sql = 'INSERT INTO BICYCLES (bike_model, bike_serialnum, username) values(?, ?, ?);'
# data = [
#     ('carrera subway', '123', 'joe'),
#     ('specialized aethos', '345', 'frank'),
#     ('canyon aeroad', '345', 'smith'),
#     ('triban 500', '345', 'joe'),
# ]

# with con: con.executemany(sql, data)

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