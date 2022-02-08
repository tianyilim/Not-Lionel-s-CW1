import sqlite3 as sl
import os

# Tutorial source: https://towardsdatascience.com/do-you-know-python-has-a-built-in-database-d553989c87bd

#### TEST ONLY ####
# Remove prior database file, if it exists (so test code is determinstic)
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
        CREATE TABLE USERS (
            --id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            username TEXT PRIMARY KEY NOT NULL,
            password_hash INTEGER NOT NULL
        );
        """
    )
    print("created user table")
    con.execute(
        """
        CREATE TABLE BICYCLES (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            bike_model TEXT NOT NULL,
            bike_serialnum TEXT NOT NULL,
            username TEXT REFERENCES USER(username)
        );
        """
    )
    print("created bicycle table")
    
    con.execute(
        """
        CREATE TABLE LOCKS (
            postcode TEXT NOT NULL,
            lock_cluster INTEGER NOT NULL,
            lock_id INTEGER NOT NULL,
            occupied INTEGER NOT NULL
        );
        """
    )
    print("created locks table")
# Callback function when user interacts with webpage

# Callback function when bike lock sends telemetry

# For creating new users
sql = "INSERT INTO 'USERS' (username, password_hash) values(?, ?);"
data = [
    ('joe', 123),
    ('frank', 123),
    ('smith', 123)
]

with con:
    con.executemany(sql, data)

sql = 'INSERT INTO BICYCLES (bike_model, bike_serialnum, username) values(?, ?, ?);'
data = [
    ('carrera subway', '123', 'joe'),
    ('specialized aethos', '345', 'frank'),
    ('canyon aeroad', '345', 'smith'),
    ('triban 500', '345', 'joe'),
]

with con: con.executemany(sql, data)

# Query for each bicycle ordered by user 
with con:
    data = con.execute("""
        SELECT USERS.username, BICYCLES.bike_model, BICYCLES.bike_serialnum
        FROM 'BICYCLES' 
        INNER JOIN 'USERS' ON BICYCLES.username=USERS.username
        ORDER BY USERS.username;
        """)
    for row in data:
        print(row)