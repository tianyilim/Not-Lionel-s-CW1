# Server-side implementation
from operator import sub
from tabnanny import check
from xmlrpc.client import Boolean
import paho.mqtt.client as mqtt
import ssl
from socket import gethostname
from time import sleep
from datetime import datetime, timedelta
import json
import sqlite3 as sl
import os
from threading import Timer

# MQTT Parameteters
CLIENT_NAME = "server_py"
BASE_TOPIC = "ic_embedded_group_4"
BROKER_IP = "localhost"
BROKER_PORT = 1883

# SQL parameters
DB_PATH = "../db/es_cw1.db"

# used for grace period checking in between
# USER_CHECKIN_GRACE = 5
USER_CHECKIN_GRACE = 0.1 # Testing
LOCK_MUTEX = {}

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
    lock_name = '/'.join(subtopics[1:4])

    # decode message string from JSON
    print("Message received", payload)
    print("Message topics", subtopics)

    # connect to db
    con = sl.connect(DB_PATH)

    # Flag to update database
    to_update_curr_usage = False
    to_insert_overall_usage = False
    to_update_overall_usage = False

    # we first query the current usage database to find out what state we are in
    state = check_curr_usage(con, subtopics[1], subtopics[2], subtopics[3])
    print("Fetched", state, "from DB")

    # current time is a useful thing
    dt_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # stay duration is also a useful thing
    if state['lock_time'] is not None:
        stay_start = datetime.strptime(state['lock_time'], "%Y-%m-%d %H:%M:%S")
        stay_end = datetime.strptime(payload['timestamp'], "%Y-%m-%d %H:%M:%S")
        stay_duration = stay_end - stay_start
        stay_duration = int(stay_duration.total_seconds())
    else: 
        stay_duration = 0

    sql_update_usage_param = {
        'occupied': state['occupied'],
        'lock_time': state['lock_time'],
        'expected_departure_time': None,
        'username': state['username'],
        'bike_sn': state['bike_sn'],
        'ouid': state['ouid'],
        'stay_duration': stay_duration,
        'remark': None
    }
    if subtopics[4] == 'in':
        # Event 1 - RPi reports that something has entered lock
        to_update_curr_usage = True
        sql_update_usage_param['occupied'] = True  # True for all cases

        if not state['username'] and not state['lock_time'] and not state['occupied']:
            # State A, the start state
            print(subtopics[1], subtopics[2], subtopics[3], "State A->C at time", payload['timestamp'])
            # Insert lock_time in OU
            to_insert_overall_usage = True

            # Update lock_time, occupied, ouid in CU
            sql_update_usage_param['lock_time'] = dt_string
        
        elif not state['username']and state['lock_time'] and state['occupied']:
            # State C, something enters the lock even after the lock is already occupied
            # update the current usage table with the most recent time
            print(subtopics[1], subtopics[2], subtopics[3], "State C->C at time", payload['timestamp'])
            print(subtopics[1], subtopics[2], subtopics[3], 
                "In message received while lock still occupied. Updated lock_time.")
            
            # Update lock_time in OU
            # to_update_overall_usage = True
            sql = '''
                UPDATE overall_usage SET in_time = ?
                WHERE transaction_sn=?;
                '''
                # '''.format( dt_string, state['ouid'] )
            # print("Updating overall_usage table with query:\n", sql)
            with con:
                con.execute(sql, [dt_string, state['ouid']])
            print("Updated overall_usage table with new lock_time.")

            # Update lock_time in CU
            sql_update_usage_param['lock_time'] = dt_string
        
        elif state['username'] and state['lock_time'] and not state['occupied']:
            # State B, after user has manually checked in
            print(subtopics[1], subtopics[2], subtopics[3], "State B->D at time", payload['timestamp'])
            # ! This assumes that we are currently in state B. There is a mutex that lets it take priority over an expiring timer.
            LOCK_MUTEX[lock_name] = True

            # Insert lock_time, username in OU
            to_insert_overall_usage = True
            # Update occupied, ouid in CU
            
            # Arm RPi Alarm
            send_alarm_msg(subtopics, True)
        
        else:
            # Throw an error
            print(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload['timestamp'])
            print('RPi \'In\' response error state')
        
    elif subtopics[4] == 'out':
        # Event 3 - RPi reports that something has left lock

        # Check the state
        if not state['username'] and state['lock_time'] and state['occupied']:
            # State C, anonymous user has inserted a bike
            print(subtopics[1], subtopics[2], subtopics[3], "State C->A at time", payload['timestamp'])
            # Update stay_duration, remark=0 in OU
            sql_update_usage_param['remark'] = 0
            to_update_overall_usage = True

            # Update (remove) occupied, lock_time, ouid in CU
            sql_update_usage_param['occupied'] = False
            sql_update_usage_param['lock_time'] = None
            sql_update_usage_param['ouid'] = None
            to_update_curr_usage = True

        else:
            # Throw an error
            print(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload['timestamp'])
            print('RPi \'Out\' response error state')

    elif subtopics[4] == 'checkin':
        # Event 2 - User checks in from JS
        if not state['username'] and not state['lock_time'] and not state['occupied']:
            # State A, the start state
            print(subtopics[1], subtopics[2], subtopics[3], "State A->B at time", payload['timestamp'])
            # ! Starts a timer to reset back to State A after a while.
            Timer(USER_CHECKIN_GRACE*60, checkin_timeout_fn, args=(subtopics[1], subtopics[2], subtopics[3])).start()
            
            # update username, bike_sn, lock_time in CU
            sql_update_usage_param['username'] = payload['username'] \
                if payload['username'] != '' else None
            sql_update_usage_param['bike_sn'] = payload['bike_sn'] \
                if payload['bike_sn'] != '' else None
            sql_update_usage_param['lock_time'] = dt_string

            to_update_curr_usage = True

        elif not state['username'] and state['lock_time'] and state['occupied']:
            # State C, anonymous user has inserted a bike

            # check timestamps if they match
            time_start = datetime.strptime(state['lock_time'], "%Y-%m-%d %H:%M:%S")
            time_end = datetime.strptime(payload['timestamp'], "%Y-%m-%d %H:%M:%S")
            time_duration = time_end - time_start

            # define check in grace period as 5 minutes
            timestamp_match = time_duration.total_seconds() < 60*USER_CHECKIN_GRACE

            ouid_match = check_ouid(con, state['ouid'], payload['username'] )

            if timestamp_match or ouid_match:
                # Timestamps match, further update the usage table
                print(subtopics[1], subtopics[2], subtopics[3], "State C->D at time", payload['timestamp'])
                send_checkin_response(subtopics, True)
                
                # Arm RPi alarm
                send_alarm_msg(subtopics, True)

                # update username, bike_sn in CU
                if 'username' in payload:
                    sql_update_usage_param['username'] = payload['username'] \
                        if payload['username'] != '' else None
                if 'bike_sn' in payload:
                    sql_update_usage_param['bike_sn'] = payload['bike_sn'] \
                        if payload['bike_sn'] != '' else None
                to_update_curr_usage = True

                # update username, bike_sn in OU
                # to_update_overall_usage = True
                # sql = '''
                #     UPDATE overall_usage SET username = {}, bike_sn = {}
                #     WHERE transaction_sn={};
                #     '''.format(
                #         'NULL' if sql_update_usage_param['username'] is None 
                #             else "\'"+sql_update_usage_param['username']+"\'",
                #         'NULL' if sql_update_usage_param['bike_sn'] is None 
                #             else sql_update_usage_param['bike_sn'], 
                #         state['ouid'] 
                #         )
                # print("Updating overall_usage table with query:\n", sql)
                sql = '''
                    UPDATE overall_usage SET username=?, bike_sn=?
                    WHERE transaction_sn=?;
                    '''
                with con:
                    # con.execute(sql)
                    con.execute(sql, [
                        sql_update_usage_param['username'],
                        sql_update_usage_param['bike_sn'],
                        state['ouid']
                    ])
                print("Updated overall_usage table with username, bike_sn.")

            else:
                # Timestamps don't match, user association fails, db not updated.
                print(subtopics[1], subtopics[2], subtopics[3], "State C->C at time", payload['timestamp'], "Timestamp_match", timestamp_match, "OUID_Match", ouid_match)
                send_checkin_response(subtopics, False)
                # TODO warn client (on MQTT channel?)
        else:
            # Throw an error
            print(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload['timestamp'])
            print('Client \'Checkin\' response error state')

    elif subtopics[4] == 'checkout':
        # Event 4 - User checks out from JS
        if state['username'] and state['lock_time'] and state['occupied']:
            # State E, the checkout state
            print(subtopics[1], subtopics[2], subtopics[3], "State D->C at time", payload['timestamp'])
            # update (remove) username, bike_sn from CU
            sql_update_usage_param['username'] = None
            sql_update_usage_param['bike_sn'] = None
            to_update_curr_usage = True
            
            # Disarm Rpi Alarm
            send_alarm_msg(subtopics, False)
            
        else:
            # Throw an error
            print(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload['timestamp'])
            print('Client \'Checkout\' response error state')

    elif subtopics[4] == 'report':
        # Event 5 - User confirms that their bike has been stolen.
        if state['username'] and state['lock_time'] and state['occupied']:
            # State E, the checkout state
            print(subtopics[1], subtopics[2], subtopics[3], "State D->A at time", payload['timestamp'])
            # update stay_duration, remark=1 in OU
            to_update_overall_usage = True
            sql_update_usage_param['remark'] = 1

            # update (remove) username, lock_time, occupied, ouid in CU
            sql_update_usage_param['username'] = None
            sql_update_usage_param['occupied'] = False
            sql_update_usage_param['lock_time'] = None
            sql_update_usage_param['ouid'] = None
            to_update_curr_usage = True
            
        else:
            # Throw an error
            print(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload['timestamp'])
            print('Client \'Report\' response error state')
    
    elif subtopics[4] == 'stolen':
        # Event 6 - RPi reports bike is stolen
        if not state['username'] and state['lock_time'] and state['occupied']:
            # State E, the checkout state
            print(subtopics[1], subtopics[2], subtopics[3], "State C->A at time", payload['timestamp'])
            # update stay_duration, remark=1 in OU
            to_update_overall_usage = True
            sql_update_usage_param['remark'] = 1
            
            # update (remove) lock_time, occupied, ouid in CU
            sql_update_usage_param['occupied'] = False
            sql_update_usage_param['lock_time'] = None
            sql_update_usage_param['ouid'] = None
            to_update_curr_usage = True
            
        else:
            # Throw an error
            print(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload['timestamp'])
            print('Client \'Report\' response error state')

    elif subtopics[4] == 'telemetry':
        # RPi reports regular telemetry data
        print(subtopics[1], subtopics[2], subtopics[3], "TODO Handle regular telemetry")
    
    else:
        # Error handling (unexpected topic)
        print(subtopics[1], subtopics[2], subtopics[3], "Got unexpected topic", message.topics)
        
    assert not (to_insert_overall_usage and to_update_overall_usage), "Should not update and insert overall usage simultaneously"
    
    if to_insert_overall_usage:        
        # sql = '''
        #     INSERT INTO overall_usage
        #     (lock_postcode, lock_cluster_id, lock_id, 
        #     username, bike_sn, in_time)
        #     VALUES ({}, {}, {}, {}, {}, {});
        # '''.format(
        #     "\'"+subtopics[1]+"\'", subtopics[2], subtopics[3], 
        #     'NULL' if sql_update_usage_param['username'] is None else "\'"+sql_update_usage_param['username']+"\'",
        #     'NULL' if sql_update_usage_param['bike_sn'] is None else sql_update_usage_param['bike_sn'],
        #     "\'"+sql_update_usage_param['lock_time']+"\'"
        # )
        # print("Inserting into overall_usage table with query:\n", sql)
        sql = '''
            INSERT INTO overall_usage
            (lock_postcode, lock_cluster_id, lock_id, 
            username, bike_sn, in_time)
            VALUES (?, ?, ?, ?, ?, ?);
        '''.format(
            "\'"+subtopics[1]+"\'", subtopics[2], subtopics[3], 
            'NULL' if sql_update_usage_param['username'] is None else "\'"+sql_update_usage_param['username']+"\'",
            'NULL' if sql_update_usage_param['bike_sn'] is None else sql_update_usage_param['bike_sn'],
            "\'"+sql_update_usage_param['lock_time']+"\'"
        )
        with con:
            # con.execute(sql)
            con.execute(sql, [
                subtopics[1], subtopics[2], subtopics[3],
                sql_update_usage_param['username'],
                sql_update_usage_param['bike_sn'],
                sql_update_usage_param['lock_time']
                ])
        print("Inserted into overall_usage table username, bike_sn and lock_time.")
    
        # get OUID
        sql = "SELECT last_insert_rowid();"
        cursor = con.cursor()
        cursor.execute(sql)
        records = cursor.fetchall()[0]
        print("Fetched last-inserted OUID as", records)
        sql_update_usage_param['ouid'] = records[0]     # it should only return one thing

    elif to_update_overall_usage:
        # sql_..param is overwritten, (to update curr_usage) so we read from state instead
        # sql = '''
        #     UPDATE overall_usage SET
        #     stay_duration = {},
        #     remark = {}
        #     WHERE transaction_sn={};
        # '''.format(
        #     sql_update_usage_param['stay_duration'],
        #     sql_update_usage_param['remark'],
        #     state['ouid']
        # )
        # print("Updating overall_usage table with query:\n", sql)
        sql = '''
            UPDATE overall_usage SET
            stay_duration=?, remark=?
            WHERE transaction_sn=?;
        '''
        with con:
            # con.execute(sql)
            con.execute(sql, [
                sql_update_usage_param['stay_duration'],
                sql_update_usage_param['remark'],
                state['ouid']
            ])
        print("Updated overall_usage table with stay_duration and remark.")

    if to_update_curr_usage:
        # sql = '''
        #   UPDATE current_usage SET
        #   occupied = {},
        #   lock_time = {},
        #   expected_departure_time = {},
        #   username = {},
        #   bike_sn = {},
        #   ouid = {}
        #   WHERE lock_postcode=\'{}\'
        #   AND lock_cluster_id={}
        #   AND lock_id={};
        # '''.format(
        #     sql_update_usage_param['occupied'],
        #     'NULL' if not sql_update_usage_param['lock_time'] 
        #         else "\'"+sql_update_usage_param['lock_time']+"\'",    # add quotes only around string
        #     'NULL' if sql_update_usage_param['expected_departure_time'] is None 
        #         else "\'"+sql_update_usage_param['expected_departure_time']+"\'",
        #     'NULL' if sql_update_usage_param['username'] is None 
        #         else "\'"+sql_update_usage_param['username']+"\'",
        #     'NULL' if sql_update_usage_param['bike_sn'] is None 
        #         else sql_update_usage_param['bike_sn'],
        #     'NULL' if sql_update_usage_param['ouid'] is None else sql_update_usage_param['ouid'],
        #     subtopics[1],
        #     subtopics[2],
        #     subtopics[3]
        # ) 
        # print("Updating current_usage table with query:\n", sql)
        sql = '''
          UPDATE current_usage SET
          occupied = ?,
          lock_time = ?,
          expected_departure_time = ?,
          username = ?,
          bike_sn = ?,
          ouid = ?
          WHERE lock_postcode=?
          AND lock_cluster_id=?
          AND lock_id=?;
        '''
        with con:
            # con.execute(sql)
            con.execute(sql, [
                sql_update_usage_param['occupied'],
                sql_update_usage_param['lock_time'],    # add quotes only around string
                sql_update_usage_param['expected_departure_time'],
                sql_update_usage_param['username'],
                sql_update_usage_param['bike_sn'],
                sql_update_usage_param['ouid'],
                subtopics[1],
                subtopics[2],
                subtopics[3]
            ])
        
        print("Updated current_usage table.")

    # release lock mutex
    LOCK_MUTEX[lock_name] = False

    print()
    print() # newlines for clearer status

def check_curr_usage(con, lock_postcode, lock_cluster_id, lock_id):
    # query = '''
    #         SELECT occupied, username, bike_sn, lock_time, ouid FROM current_usage
    #         WHERE lock_postcode=\'{}\'
    #         AND lock_cluster_id={}
    #         AND lock_id={};
    #         '''.format(lock_postcode, lock_cluster_id, lock_id)    
    query = '''
        SELECT occupied, username, bike_sn, lock_time, ouid FROM current_usage
        WHERE lock_postcode=?
        AND lock_cluster_id=?
        AND lock_id=?;
        '''
    # print("Querying curr_usage with query:\n", query)
    with con:
        data = con.execute(query, [lock_postcode, lock_cluster_id, lock_id])
        data = data.fetchall()[0] # This returns a tuple in a list for some reason...

        return { 
            'occupied': data[0],
            'username': data[1],
            'bike_sn' : data[2],
            'lock_time': data[3],
            'ouid' : data[4]
            }

def check_ouid(con, ouid, username):
    # check the OUID in current_usage is NULL or has no username attached
    q = 'SELECT username FROM overall_usage WHERE transaction_sn = ?;'
    with con:
        data = con.execute(q, [ouid])
        data = data.fetchall()[0][0]
        print("Fetched", data, "from overall_usage while checking for ouid", ouid, "username", username)

    return data == username     # only pass if username in the ouid is same as provided

# Removes username and lock_time from CU table, shifting from state B->A due to a timeout
def checkin_timeout_fn(lock_postcode, lock_cluster_id, lock_id):
    lock_name = '/'.join([lock_postcode, lock_cluster_id, lock_id])
    con = sl.connect(DB_PATH)

    # check what state we are in
    state = check_curr_usage(con, lock_postcode, lock_cluster_id, lock_id)
    if state['username'] and state['lock_time'] and not state['occupied']:
        # In state B, revert out of it
        if not (LOCK_MUTEX[lock_name]==True) or not (lock_name in LOCK_MUTEX):
            query = '''
                    UPDATE current_usage SET occupied = 0,
                    username = NULL,
                    bike_sn = NULL,
                    lock_time = NULL
                    WHERE lock_postcode=?
                    AND lock_cluster_id=?
                    AND lock_id=?;
                    '''
                    # '''.format(lock_postcode, lock_cluster_id, lock_id)
            # print("Querying curr_usage with query:\n", query)
            with con:
                con.execute(query, [lock_postcode, lock_cluster_id, lock_id])
            print(lock_postcode, lock_cluster_id, lock_id, "State B->A")
            
            # TODO checkin fail -> Response code?
            send_checkin_response([BASE_TOPIC, lock_postcode, lock_cluster_id, lock_id, ' '], False)
        else:
            print(lock_postcode, lock_cluster_id, lock_id, "is locked. Not modifying its state.")
    else:
        print(lock_postcode, lock_cluster_id, lock_id, "no longer in state B. Not modifying its state.")


def send_alarm_msg(subtopics, onoff: Boolean):
    alarm_topic = ('/'.join( subtopics[:-1]+['alarm'] ))
    msg = {'status' : onoff}
    print("Publishing", msg, "on", alarm_topic)

    msg = bytes(json.dumps(msg), 'utf-8')
    client.publish(alarm_topic, msg)

def send_checkin_response(subtopics, status: Boolean):
    topic = ('/'.join( subtopics[:-1]+['checkinresponse'] ))
    msg = {'status': status}
    print("Publishing", msg, "on", topic)

    msg = bytes(json.dumps(msg), 'utf-8')
    client.publish(topic, msg)

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

    client.subscribe(BASE_TOPIC+"/+/+/+/in")
    client.subscribe(BASE_TOPIC+"/+/+/+/out")
    client.subscribe(BASE_TOPIC+"/+/+/+/checkin")
    client.subscribe(BASE_TOPIC+"/+/+/+/checkout")
    client.subscribe(BASE_TOPIC+"/+/+/+/stolen")
    client.subscribe(BASE_TOPIC+"/+/+/+/report")
    client.subscribe(BASE_TOPIC+"/+/+/+/telemetry")

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