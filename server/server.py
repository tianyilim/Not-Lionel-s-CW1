# Server-side implementation
from operator import sub
import paho.mqtt.client as mqtt
import ssl
from socket import gethostname
from time import sleep
from datetime import datetime, timedelta
import json
import sqlite3 as sl
import os

# MQTT Parameteters
CLIENT_NAME = "server_py"
BASE_TOPIC = "ic_embedded_group_4"
BROKER_IP = "localhost"
BROKER_PORT = 1883

# SQL parameters
DB_PATH = "../db/es_cw1.db"

# used for grace period checking in between
USER_CHECKIN_GRACE = 5

# callbacks
def on_connect(client, userdata, flags, rc):
    global conn_flag
    conn_flag = True
    print("Client Connected with flag", mqtt.connack_string(rc))
    conn_flag = True

def on_disconnect(client, userdata, rc):
    print("Client Disconnected with flag", rc)

def on_log(client, userdata, level, buf):
    print("["+level+"]", buf)

def on_message(client, userdata, message):
    # handle incoming message

    payload = json.loads( message.payload.decode("utf-8") )
    
    # Decompose message
    subtopics = message.topic.split('/')

    # decode message string from JSON
    print("Message received", payload)
    print("Message topics", subtopics)

    # connect to db
    con = sl.connect(DB_PATH)

    # Flag to update database
    to_update_curr_usage = False
    to_insert_overall_usage = False

    # current time is a useful thing
    dt_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # we first query the current usage database to find out what state we are in
    state = check_curr_usage(con, subtopics[1], subtopics[2], subtopics[3])
    print("Fetched", state, "from DB")

    sql_update_curr_usage_param = {
        'occupied': state['occupied'],
        'lock_time': state['lock_time'],
        'expected_departure_time': None,
        'username': state['username'],
        'bike_sn': state['bike_sn']
    }
    if subtopics[4] == 'in':
        # Event 1 - RPi reports that something has entered lock
        sql_update_curr_usage_param['occupied'] = True
        sql_update_curr_usage_param['lock_time'] = dt_string
        to_update_curr_usage = True

        if not state['username'] and not state['lock_time'] and not state['occupied']:
            # State A, the start state
            print(subtopics[1], subtopics[2], subtopics[3], "State A->C at time", payload['timestamp'])
        
        elif not state['username']and state['lock_time'] and state['occupied']:
            # State C, something enters the lock even after the lock is already occupied
            # update the current usage table with the most recent time
            print(subtopics[1], subtopics[2], subtopics[3], "State C->C at time", payload['timestamp'])
            print(subtopics[1], subtopics[2], subtopics[3], 
                "In message received while lock still occupied. Updated lock_time.")
        
        elif state['username'] and state['lock_time'] and not state['occupied']:
            # State B, after user has manually checked in
            print(subtopics[1], subtopics[2], subtopics[3], "State B->D at time", payload['timestamp'])
            # TODO implement this
        
        else:
            # Throw an error
            print(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload['timestamp'])
            assert False, 'RPi \'In\' response error state'
        
    elif subtopics[4] == 'out':
        # Event 3 - RPi reports that something has left lock
        sql_update_curr_usage_param['occupied'] = False
        sql_update_curr_usage_param['lock_time'] = None
        to_update_curr_usage = True
        to_insert_overall_usage = True

        # Check the state
        if not state['username'] and state['lock_time'] and state['occupied']:
            # State C, anonymous user has inserted a bike
            print(subtopics[1], subtopics[2], subtopics[3], "State C->A at time", payload['timestamp'])

        elif state['username'] and state['lock_time'] and state['occupied']:
            # State D, bike removed with named user
            print(subtopics[1], subtopics[2], subtopics[3], "State D->E at time", payload['timestamp'])
            # TODO trigger User Authentication event
        else:
            # Throw an error
            print(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload['timestamp'])
            assert False, 'RPi \'Out\' response error state'

    elif subtopics[4] == 'checkin':
        # Event 2 - User checks in from JS
        if not state['username'] and not state['lock_time'] and not state['occupied']:
            # State A, the start state
            print(subtopics[1], subtopics[2], subtopics[3], "State A->B at time", payload['timestamp'])
            # TODO trigger timeout event
        elif not state['username'] and state['lock_time'] and state['occupied']:
            # State C, anonymous user has inserted a bike

            # check timestamps if they match
            time_start = datetime.strptime(state['lock_time'], "%Y-%m-%d %H:%M:%S")
            time_end = datetime.strptime(payload['timestamp'], "%Y-%m-%d %H:%M:%S")
            time_duration = time_end - time_start

            # define check in grace period as 5 minutes
            timestamp_match = time_duration.total_seconds() < 60*USER_CHECKIN_GRACE
            if timestamp_match:
                # Timestamps match, further update the usage table
                print(subtopics[1], subtopics[2], subtopics[3], "State C->D at time", payload['timestamp'])
                if 'username' in payload:
                    sql_update_curr_usage_param['username'] = payload['username'] \
                        if payload['username'] != '' else None
                if 'bike_sn' in payload:
                    sql_update_curr_usage_param['bike_sn'] = payload['bike_sn'] \
                        if payload['bike_sn'] != '' else None
                to_update_curr_usage = True
            else:
                # Timestamps don't match, user association fails, db not updated.
                print(subtopics[1], subtopics[2], subtopics[3], "State C->C at time", payload['timestamp'])
        else:
            # Throw an error
            print(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload['timestamp'])
            assert False, 'Client \'Checkin\' response error state'

    elif subtopics[4] == 'checkout':
        # Event 4 - User checks out from JS
        if state['username'] and not state['lock_time'] and not state['occupied']:
            # State E, the checkout state
            # TODO trigger checkout event
            print(subtopics[1], subtopics[2], subtopics[3], "State E->A at time", payload['timestamp'])
            # clear the username
            sql_update_curr_usage_param['username'] = None
            to_update_curr_usage = True
            
        else:
            # Throw an error
            print(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload['timestamp'])
            assert False, 'Client \'Checkout\' response error state'

    elif subtopics[4] == 'stolen':
        # RPi reports bike is stolen
        print(subtopics[1], subtopics[2], subtopics[3], "TODO beep boop, bike stolen!")
    elif subtopics[4] == 'telemetry':
        # RPi reports regular telemetry data
        print(subtopics[1], subtopics[2], subtopics[3], "TODO Handle regular telemetry")
    else:
        # Error handling (unexpected topic)
        print(subtopics[1], subtopics[2], subtopics[3], "Got unexpected topic", message.topics)
        
    
    if to_update_curr_usage:
        sql = '''
          UPDATE current_usage SET
          occupied = {},
          lock_time = {},
          expected_departure_time = {},
          username = {},
          bike_sn = {}
          WHERE lock_postcode=\'{}\'
          AND lock_cluster_id={}
          AND lock_id={};
        '''.format(
            sql_update_curr_usage_param['occupied'],
            'NULL' if not sql_update_curr_usage_param['lock_time'] 
                else "\'"+sql_update_curr_usage_param['lock_time']+"\'",    # add quotes only around string
            'NULL' if sql_update_curr_usage_param['expected_departure_time'] is None 
                else "\'"+sql_update_curr_usage_param['expected_departure_time']+"\'",
            'NULL' if sql_update_curr_usage_param['username'] is None 
                else "\'"+sql_update_curr_usage_param['username']+"\'",
            'NULL' if sql_update_curr_usage_param['bike_sn'] is None 
                else "\'"+sql_update_curr_usage_param['bike_sn']+"\'",
            subtopics[1],
            subtopics[2],
            subtopics[3]
        ) 
        print("Updating current_usage table with query:\n", sql)
        with con:
            con.execute(sql)
        
        print("Updated current_usage table.")

    if to_insert_overall_usage:
        # calculate stay duration by comparing times
        stay_start = datetime.strptime(state['lock_time'], "%Y-%m-%d %H:%M:%S")
        stay_end = datetime.strptime(payload['timestamp'], "%Y-%m-%d %H:%M:%S")
        stay_duration = stay_end - stay_start

        sql = '''
            INSERT INTO overall_usage
            (lock_postcode, lock_cluster_id, lock_id, 
            username, bike_sn, in_time, stay_duration, remark)
            VALUES ({}, {}, {}, {}, {}, {}, {}, {});
        '''.format(
            "\'"+subtopics[1]+"\'", subtopics[2], subtopics[3], 
            'NULL' if sql_update_curr_usage_param['username'] is None else "\'"+sql_update_curr_usage_param['username']+"\'",
            'NULL' if sql_update_curr_usage_param['bike_sn'] is None else "\'"+sql_update_curr_usage_param['bike_sn']+"\'",
            "\'"+state['lock_time']+"\'",
            (int(stay_duration.total_seconds())),    # For now we store a time with second accuracy
            0   # remark will always be 0 by default
        )
        print("Inserting into overall_usage table with query:\n", sql)
        with con:
            con.execute(sql)
        
        print("Inserted into overall_usage table.")
    
    print()
    print() # newlines for clearer status

# TODO don't use strings here in case of sql injections
def check_curr_usage(con, lock_postcode, lock_cluster_id, lock_id):
    query = '''
            SELECT occupied, username, bike_sn, lock_time FROM current_usage
            WHERE lock_postcode=\'{}\'
            AND lock_cluster_id={}
            AND lock_id={};
            '''.format(lock_postcode, lock_cluster_id, lock_id)
    print("Querying curr_usage with query:\n", query)
    with con:
        data = con.execute(query, [])
        data = data.fetchall()[0] # This returns a tuple in a list for some reason...
        print("Query returned", data)

        return { 
            'occupied': data[0],
            'username': data[1],
            'bike_sn' : data[2],
            'lock_time': data[3] 
            }

# Main code
if __name__ == "__main__":
    # Connect to database
    if not os.path.exists(DB_PATH):
        print("Database not found. Has it been created?")
        exit(1)
        
    client = mqtt.Client(CLIENT_NAME)                           # Create client object
    status = client.connect(BROKER_IP, port=BROKER_PORT)        # Connect to MQTT broker
    # client.tls_set(ca_certs='./auth/ca/ca.crt', certfile='./auth/client/client.crt', keyfile='./auth/client/client.key', tls_version=ssl.PROTOCOL_TLSv1_2)
    print(CLIENT_NAME, "connect", mqtt.error_string(status))    # Error handling

    client.subscribe(BASE_TOPIC+"/+/+/+/+")

    # add client callbacks
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_log = on_log

    conn_flag = False
    while not conn_flag:
        client.loop_start()
        print("Waiting for connection to broker...")
        sleep(2)

    while conn_flag:
        pass

    # ! Insert conditions to disconnect / stop looping here.
    # client.loop_stop()
    # client.disconnect()