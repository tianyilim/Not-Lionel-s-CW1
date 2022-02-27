import sqlite3 as sl
import json
import datetime
from random import randint, randrange
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
            avg_usage BLOB,
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
sql = '''INSERT INTO overall_usage 
    (lock_postcode, lock_cluster_id, lock_id, username, bike_sn, in_time, stay_duration, remark)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    '''
    
postcodes = ['SW72AZ', 'W68EL']
usernames = ['tianyi', 'smith', 'joe']
d1 = datetime.datetime.strptime('3/1/2022 1:30 PM', '%d/%m/%Y %I:%M %p')
d2 = datetime.datetime.strptime('27/2/2022 4:50 AM', '%d/%m/%Y %I:%M %p')


def random_date(start, end):
    """
    This function will return a random datetime between two datetime 
    objects.
    """
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    date = start + datetime.timedelta(seconds=random_second)
    return datetime.datetime.strftime(date, "%Y-%m-%d %H:%M:%S")

for i in range(1000):
    
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
    # print("inserting", data)

    with con:
        con.execute(sql, data)

# Perform averaging
all_locks = "SELECT lock_postcode, lock_cluster_id, num_lock FROM cluster_coordinates;"
with con:
    data = con.execute(all_locks, [])
    lock_info = data.fetchall()

# get start and end times
all_times = "SELECT in_time FROM overall_usage ORDER BY in_time;"
with con:
    data = con.execute(all_times, [])
    data = data.fetchall()
    first_time = data[0][0]
    last_time = data[-1][0]

# iterate over locks
for postcode, cluster, num_lock in lock_info:
    lock_usage = [[None for j in range(8)] for i in range(7)]

    # iterate over weeks
    dt_idx = datetime.datetime.strptime(first_time, "%Y-%m-%d %H:%M:%S")
    dt_lim = datetime.datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
    while(dt_idx < dt_lim):
        # print("Resetting week_usage")
        week_usage = [[[0 for k in range(num_lock)] for j in range(8)] for i in range(7)]
        # accumulator for lock usage per week

        # print(postcode, cluster)
        # print(dt_idx.strftime("%Y-%m-%d %H:%M:%S"))
        dt_end = dt_idx + datetime.timedelta(days=7)

        # Query database between these two times
        # Wrapping around days and weeks is too hard. Skipping for now.
        usage_query = '''
            SELECT lock_id, in_time, stay_duration FROM overall_usage WHERE
            in_time > ? AND in_time < ?
            AND lock_postcode=?
            AND lock_cluster_id=?
            AND remark=0
            ;
        '''
        with con:
            data = con.execute(usage_query, [
                dt_idx.strftime("%Y-%m-%d %H:%M:%S"),
                dt_end.strftime("%Y-%m-%d %H:%M:%S"),
                postcode, cluster
            ])
            usage_data = data.fetchall()

        # Iterate over usage entries in each week
        for lock_id, in_time, stay_duration in usage_data:
            # print(postcode, cluster, lock_id, in_time, stay_duration)
            in_time = datetime.datetime.strptime(in_time, "%Y-%m-%d %H:%M:%S")
            out_time = in_time + datetime.timedelta(seconds=stay_duration)
            # print("In time:", in_time.strftime("%A %Y-%m-%d %H:%M:%S"))
            # print("Out time:", out_time.strftime("%Y-%m-%d %H:%M:%S"))
            while (in_time < out_time):
                hr_idx = int(in_time.strftime('%H'))//3
                week_idx = int(in_time.strftime('%w'))    # we index in 3-hour increments
                # print(week_idx, hr_idx, lock_id)          # Sunday is 0
                week_usage[week_idx][hr_idx][lock_id-1] = 1

                in_time += datetime.timedelta(hours=3)

        # Week percentage
        for dayofweek in range(7):
            for hours in range(8):
                timeslot_usage = 0
                for lock in range(num_lock):
                    # this will be 1 if the lock is in use at that time
                    timeslot_usage += week_usage[dayofweek][hours][lock]
                
                timeslot_usage_percentage = (100*timeslot_usage)/num_lock
                
                if lock_usage[dayofweek][hours] == None:
                    # If not initialised
                    lock_usage[dayofweek][hours] = int( timeslot_usage_percentage )
                else:
                    # take the average
                    lock_usage[dayofweek][hours] = \
                        int( (timeslot_usage_percentage + lock_usage[dayofweek][hours]) / 2 )

        dt_idx = dt_end

    # usage dict
    daysOfWeek = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]
    usage_dict = {}

    print(postcode, cluster)
    for i in range(7):
        # print(daysOfWeek[i], lock_usage[i])
        usage_dict[daysOfWeek[i]] = lock_usage[i]

    json_data = json.dumps(usage_dict)
    print(json_data)

    # serialise json into bytes
    json_data = bytes(json_data, 'utf-8')
    update_blob = '''
        UPDATE cluster_coordinates SET avg_usage=?
        WHERE lock_postcode=? AND lock_cluster_id=?;
    '''
    with con:
        con.execute(update_blob, [json_data, postcode, cluster])