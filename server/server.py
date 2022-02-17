# Server-side implementation
import paho.mqtt.client as mqtt
import ssl
from socket import gethostname
from time import sleep
from datetime import datetime
import json
import sqlite3 as sl
import os

# MQTT Parameteters
CLIENT_NAME = "server_py"
BASE_TOPIC = "ic_embedded_group_4"
BROKER_IP = "localhost"
BROKER_PORT = 1883

# SQL parameters
DB_PATH = "es_cw1.db"

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
    subtopics = message.topics.split('/')

    # decode message string from JSON
    print("Message received", payload)
    print("Message topics",subtopics)

    # Flag to update database
    to_update_curr_usage = False
    to_update_overall_usage = False

    # current time is a useful thing
    dt_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # we first query the current usage database to find out what state we are in
    state = check_curr_usage(subtopics[1], subtopics[2], subtopics[3])
    print("Fetched", state, "from DB")

    sql_update_curr_usage_param = {
        'occupied': False,
        'lock_time': 'NULL',
        'expected_departure_time': 'NULL',
        'username': state['username'],
        'bike_sn': state['bike_sn']
    }

    # null re

    if subtopics[4] == 'in':
        # Event 1 - RPi reports that something has entered lock
        sql_update_curr_usage_param['occupied'] = True
        sql_update_curr_usage_param['lock_time'] = dt_string
        to_update_curr_usage = True

        if not state['username'] and not state['lock_time'] and not state['occupied']:
            # State A, the start state
            print(subtopics[1], subtopics[2], subtopics[3], "State A->C at time", payload.timestamp)
        
        elif not state['username']and state['lock_time'] and state['occupied']:
            # State C, something enters the lock even after the lock is already occupied
            # update the current usage table with the most recent time
            print(subtopics[1], subtopics[2], subtopics[3], "State C->C at time", payload.timestamp)
            print(subtopics[1], subtopics[2], subtopics[3], 
                "In message received while lock still occupied. Updated lock_time.")
        
        elif state['username'] and state['lock_time'] and not state['occupied']:
            # State B, after user has manually checked in
            print(subtopics[1], subtopics[2], subtopics[3], "State B->D at time", payload.timestamp)
        
        else:
            # Throw an error
            print(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload.timestamp)
            to_update_curr_usage = False
            assert False, 'RPi \'In\' response error state'
        
    elif subtopics[4] == 'out':
        # Event 3 - RPi reports that something has left lock
        sql_update_curr_usage_param['occupied'] = False
        sql_update_curr_usage_param['lock_time'] = 'null'
        to_update_curr_usage = True
        to_update_overall_usage = True

        # Check the state
        if not state['username'] and state['lock_time'] and state['occupied']:
            # State C, anonymous user has inserted a bike
            print(subtopics[1], subtopics[2], subtopics[3], "State C->A at time", payload.timestamp)

        elif state['username'] and state['lock_time'] and state['occupied']:
            # State D, bike removed with named user
            print(subtopics[1], subtopics[2], subtopics[3], "State D->E at time", payload.timestamp)
            # TODO trigger User Authentication event
        else:
            # Throw an error
            print(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload.timestamp)
            to_update_curr_usage = False
            assert False, 'RPi \'Out\' response error state'

    elif subtopics[4] == 'checkin':
        # Event 2 - User checks in from JS
        ''''''
        if not state['username'] and not state['lock_time'] and not state['occupied']:
            # State A, the start state
            print(subtopics[1], subtopics[2], subtopics[3], "State A->B at time", payload.timestamp)
            # TODO trigger timeout event
        elif not state['username'] and state['lock_time'] and state['occupied']:
            # State C, anonymous user has inserted a bike

            # check timestamps if they match
            timestamp_match = True
            if timestamp_match:
                # Timestamps match, further update the usage table
                print(subtopics[1], subtopics[2], subtopics[3], "State C->D at time", payload.timestamp)
            else:
                # Timestamps don't match, user association fails
                print(subtopics[1], subtopics[2], subtopics[3], "State C->C at time", payload.timestamp)
        else:
            # Throw an error
            print(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload.timestamp)
            to_update_curr_usage = False
            assert False, 'Client \'Checkin\' response error state'

    elif subtopics[4] == 'checkout':
        # Event 4 - User checks out from JS
        ''''''
    elif subtopics[4] == 'stolen':
        # RPi reports bike is stolen
        ''''''
    elif subtopics[4] == 'telemetry':
        # RPi reports regular telemetry data
        ''''''
    else:
        # Error handling (unexpected topic)
        print("Got unexpected topic", message.topics)
        
    
    if to_update_curr_usage:
        sql = '''
          UPDATE current_usage SET
          occupied = ${},
          lock_time = \'${}\',
          expected_departure_time = ${},
          username = \'${}\',
          bike_sn = \'${}\',
          WHERE lock_postcode=\'${}\'
          AND lock_cluster_id=${}
          AND lock_id=${};
        '''.format(
            sql_update_curr_usage_param['occupied'],
            sql_update_curr_usage_param['lock_time'],
            sql_update_curr_usage_param['expected_departure_time'],
            sql_update_curr_usage_param['username'],
            sql_update_curr_usage_param['bike_sn'],
            subtopics[1],
            subtopics[2],
            subtopics[3]
        )
        print("Updating current_usage table with query:\n", sql)
        with con:
            con.execute(sql)
        
        print("Updated current_usage table.")

    if to_update_overall_usage:
        print("TODO Update Overall Usage here")

def check_curr_usage(lock_postcode, lock_cluster_id, lock_id):
    query = '''
            SELECT occupied, username, bike_sn, lock_time FROM current_usage
            WHERE lock_postcode=\'${}\'
            AND lock_cluster_id=${}
            AND lock_id=${};
            '''.format(lock_postcode, lock_cluster_id, lock_id)
    with con:
        data = con.execute(query)
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
    
    con = sl.connect(DB_PATH)
    
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
        sleep(2)
        print("Waiting for connection to broker...")

    # ! Insert conditions to disconnect / stop looping here.
    # client.loop_stop()
    # client.disconnect()