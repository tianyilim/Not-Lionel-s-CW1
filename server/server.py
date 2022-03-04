# Server-side implementation
from operator import sub
from tabnanny import check
from xmlrpc.client import Boolean
import paho.mqtt.client as mqtt
import ssl
from socket import gethostname
from time import sleep
import datetime
import json
import sqlite3 as sl
import os
from threading import Timer
import logging

# MQTT Parameteters
CLIENT_NAME = "server_py"
BASE_TOPIC = "ic_embedded_group_4"
# BROKER_IP = "35.178.122.34"
BROKER_IP = "localhost"
BROKER_PORT = 8883
SUBSCRIBED_TOPICS = ['in', 'out', 'checkin', 'checkout', 'stolen', 'report', 'telemetry']

# SQL parameters
DB_PATH = "../db/es_cw1.db"

# used for grace period checking in between
USER_CHECKIN_GRACE = 1
# USER_CHECKIN_GRACE = 0.1 # Testing
LOCK_MUTEX = {}

# callbacks
def on_connect(client, userdata, flags, rc):
    global conn_flag
    conn_flag = True
    logging.info(f"Client Connected with flag {mqtt.connack_string(rc)}")
    
    for topic in SUBSCRIBED_TOPICS:
        sub_topic = BASE_TOPIC+'/+/+/+/'+topic
        logging.info(f"Client suscribing to {sub_topic}")
        client.subscribe(sub_topic)
    
    conn_flag = True

def on_disconnect(client, userdata, rc):
    logging.info(f"Client Disconnected with flag {mqtt.error_string(rc)}")

def on_log(client, userdata, level, buf):
    pass    # we don't need to print this out for now
    # logging.debug(f"MQTT client log: [{level}]: {buf}")

def on_message(client, userdata, message):
    # handle incoming message

    payload = json.loads( message.payload.decode("utf-8") )
    
    # Decompose message
    subtopics = message.topic.split('/')
    lock_name = '/'.join(subtopics[1:4])

    # decode message string from JSON
    logging.info(f"Message topic: '{message.topic}'")
    logging.debug(f"Message content: {payload}")

    # connect to db
    con = sl.connect(DB_PATH)

    # Flag to update database
    to_update_curr_usage = False
    to_insert_overall_usage = False
    to_update_overall_usage = False

    # we first query the current usage database to find out what state we are in
    state = check_curr_usage(con, subtopics[1], subtopics[2], subtopics[3])
    if not state:
        logging.warn("Got invalid values on subtopics, not responding to message")
        return
    logging.debug(f"Fetched {state} from DB")

    # current time is a useful thing
    dt_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # stay duration is also a useful thing
    if state['lock_time'] is not None:
        stay_start = datetime.datetime.strptime(state['lock_time'], "%Y-%m-%d %H:%M:%S")
        stay_end = datetime.datetime.strptime(payload['timestamp'], "%Y-%m-%d %H:%M:%S")
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
            logging.debug(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} State A->C at time {payload['timestamp']}")
            # Insert lock_time in OU
            to_insert_overall_usage = True

            # Update lock_time, occupied, ouid in CU
            sql_update_usage_param['lock_time'] = dt_string
        
        elif not state['username']and state['lock_time'] and state['occupied']:
            # State C, something enters the lock even after the lock is already occupied
            # update the current usage table with the most recent time
            logging.debug(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} State C->C at time {payload['timestamp']}")
            logging.info( f"{subtopics[1]} {subtopics[2]} {subtopics[3]} In message received while lock still occupied. Updated lock_time.")
            
            # Update lock_time in OU
            # to_update_overall_usage = True
            sql = '''
                UPDATE overall_usage SET in_time = ?
                WHERE transaction_sn=?;
                '''
            with con:
                con.execute(sql, [dt_string, state['ouid']])
            logging.info("Updated overall_usage table with new lock_time.")

            # Update lock_time in CU
            sql_update_usage_param['lock_time'] = dt_string
        
        elif state['username'] and state['lock_time'] and not state['occupied']:
            # State B, after user has manually checked in
            logging.debug(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} State B->D at time {payload['timestamp']}")
            # ! This assumes that we are currently in state B. There is a mutex that lets it take priority over an expiring timer.
            LOCK_MUTEX[lock_name] = True

            # Insert lock_time, username in OU
            to_insert_overall_usage = True
            # Update occupied, ouid in CU
            
            # Arm RPi Alarm
            send_alarm_msg(subtopics, True)

            # Send checkin confirmation
            send_checkin_response(subtopics, True, 'B->D')
        
        else:
            # Throw an error
            logging.warning(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} Unexpected state detected {payload['timestamp']}")
            logging.warning('RPi \'In\' response error state')
        
    elif subtopics[4] == 'out':
        # Event 3 - RPi reports that something has left lock

        # Check the state
        if not state['username'] and state['lock_time'] and state['occupied']:
            # State C, anonymous user has inserted a bike
            logging.debug(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} State C->A at time {payload['timestamp']}")
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
            logging.warning(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} Unexpected state detected {payload['timestamp']}")
            logging.warning('RPi \'Out\' response error state')

    elif subtopics[4] == 'checkin':
        # Event 2 - User checks in from JS
        if not state['username'] and not state['lock_time'] and not state['occupied']:
            # State A, the start state
            logging.debug(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} State A->B at time {payload['timestamp']}")
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
            time_start = datetime.datetime.strptime(state['lock_time'], "%Y-%m-%d %H:%M:%S")
            time_end = datetime.datetime.strptime(payload['timestamp'], "%Y-%m-%d %H:%M:%S")
            time_duration = time_end - time_start

            # define check in grace period as 5 minutes
            timestamp_match = time_duration.total_seconds() < 60*USER_CHECKIN_GRACE

            ouid_match = check_ouid(con, state['ouid'], payload['username'] )

            if timestamp_match or ouid_match:
                # Timestamps match, further update the usage table
                logging.debug(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} State C->D at time {payload['timestamp']}")
                send_checkin_response(subtopics, True, 'C->D')
                
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
                sql = '''
                    UPDATE overall_usage SET username=?, bike_sn=?
                    WHERE transaction_sn=?;
                    '''
                with con:
                    con.execute(sql, [
                        sql_update_usage_param['username'],
                        sql_update_usage_param['bike_sn'],
                        state['ouid']
                    ])
                logging.info("Updated overall_usage table with username, bike_sn.")

            else:
                # Timestamps don't match, user association fails, db not updated.
                logging.info(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} State C->C at time {payload['timestamp']}. Timestamp_match: {timestamp_match}, OUID_Match: {ouid_match}")
                send_checkin_response(subtopics, False, 'Unable to find lock entry to associate with check-in')
                
        else:
            # Throw an error
            logging.warning(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} Unexpected state detected {payload['timestamp']}")
            logging.warning('Client \'Checkin\' response error state')

    elif subtopics[4] == 'checkout':
        # Event 4 - User checks out from JS
        if state['username'] and state['lock_time'] and state['occupied']:
            # State E, the checkout state
            logging.debug(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} State D->C at time {payload['timestamp']}")
            # update (remove) username, bike_sn from CU
            sql_update_usage_param['username'] = None
            sql_update_usage_param['bike_sn'] = None
            to_update_curr_usage = True
            
            # Disarm Rpi Alarm
            send_alarm_msg(subtopics, False)
            
        else:
            # Throw an error
            logging.warning(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} Unexpected state detected {payload['timestamp']}")
            logging.warning('Client \'Checkout\' response error state')

    elif subtopics[4] == 'report':
        # Event 5 - User confirms that their bike has been stolen.
        if payload['state'] == 1:
            alarm_state = 0     # checkout, no irregularity
        elif payload['state'] == 2:
            alarm_state = 1
        else:
            logging.warning(f"Got unexpected value in state payload when processing report message: {payload['state']}")
            return

        if state['username'] and state['lock_time'] and state['occupied']:
            # State D, the signed-in-user state
            logging.debug(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} State D->A at time {payload['timestamp']}")
            # update stay_duration, remark=1 in OU
            to_update_overall_usage = True
            sql_update_usage_param['remark'] = alarm_state

            # update (remove) username, bike_sn, lock_time, occupied, ouid in CU
            sql_update_usage_param['username'] = None
            sql_update_usage_param['bike_sn'] = None
            sql_update_usage_param['occupied'] = False
            sql_update_usage_param['lock_time'] = None
            sql_update_usage_param['ouid'] = None
            to_update_curr_usage = True

            # disable RPi alarm
            send_alarm_msg(subtopics, False)
            
        elif not state['username'] and state['lock_time'] and state['occupied']:
            # State C, the anonymous user state
            logging.debug(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} State C->A at time {payload['timestamp']}")
            # update stay_duration, remark=1 in OU
            to_update_overall_usage = True
            sql_update_usage_param['remark'] = alarm_state
            
            # update (remove) lock_time, occupied, ouid in CU
            sql_update_usage_param['occupied'] = False
            sql_update_usage_param['lock_time'] = None
            sql_update_usage_param['ouid'] = None
            to_update_curr_usage = True

        else:
            # Throw an error
            logging.warning(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} Unexpected state detected {payload['timestamp']}")
            logging.warning('Client \'Report\' response error state')
    
    elif subtopics[4] == 'stolen':
        # Event 6 - RPi reports bike is stolen
        if not state['username'] and state['lock_time'] and state['occupied']:
            # State C, the anonymous user state
            logging.debug(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} State C->A at time {payload['timestamp']}")
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
            logging.warning(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} Unexpected state detected {payload['timestamp']}")
            logging.warning('RPi \'Stolen\' response error state')

    elif subtopics[4] == 'telemetry':
        # RPi reports regular telemetry data
        sql = '''
            INSERT INTO telemetry (timestamp, data, lock_postcode, lock_cluster_id, lock_id)
            VALUES (?, ?, ?, ?, ?);'''
        con.execute(sql, [
            dt_string, payload['accel_data'],   # TODO confirm this works
            subtopics[1], subtopics[2], subtopics[3]
        ])
        # logging.info(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} Handle regular telemetry")
    
    else:
        # Error handling (unexpected topic)
        logging.warning(f"{subtopics[1]} {subtopics[2]} {subtopics[3]} Got unexpected topic", message.topics)
        
    assert not (to_insert_overall_usage and to_update_overall_usage), "Should not update and insert overall usage simultaneously"
    
    if to_insert_overall_usage:
        sql = '''
            INSERT INTO overall_usage
            (lock_postcode, lock_cluster_id, lock_id, 
            username, bike_sn, in_time)
            VALUES (?, ?, ?, ?, ?, ?);
        '''
        with con:
            con.execute(sql, [
                subtopics[1], subtopics[2], subtopics[3],
                sql_update_usage_param['username'],
                sql_update_usage_param['bike_sn'],
                sql_update_usage_param['lock_time']
                ])
        logging.debug("Inserted into overall_usage table username, bike_sn and lock_time.")
    
        # get OUID
        sql = "SELECT last_insert_rowid();"
        cursor = con.cursor()
        cursor.execute(sql)
        records = cursor.fetchall()[0]
        logging.debug(f"Fetched last-inserted OUID as {records}")
        sql_update_usage_param['ouid'] = records[0]     # it should only return one thing

    elif to_update_overall_usage:
        sql = '''
            UPDATE overall_usage SET
            stay_duration=?, remark=?
            WHERE transaction_sn=?;
        '''
        with con:
            con.execute(sql, [
                sql_update_usage_param['stay_duration'],
                sql_update_usage_param['remark'],
                state['ouid']
            ])
        logging.debug("Updated overall_usage table with stay_duration and remark.")

    if to_update_curr_usage:
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
        
        logging.debug("Updated current_usage table.")

    # release lock mutex
    LOCK_MUTEX[lock_name] = False
    logging.debug('\n') # newlines for clearer status
    
    ###########################################
    ###      END on_message callback        ###
    ###########################################

def check_curr_usage(con, lock_postcode, lock_cluster_id, lock_id):
    if (not lock_postcode) or (not lock_cluster_id) or (not lock_id):
        return None

    query = '''
        SELECT occupied, username, bike_sn, lock_time, ouid FROM current_usage
        WHERE lock_postcode=?
        AND lock_cluster_id=?
        AND lock_id=?;
        '''
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
        logging.debug(f"Fetched {data} from overall_usage while checking for ouid {ouid} and username {username}")

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
            with con:
                con.execute(query, [lock_postcode, lock_cluster_id, lock_id])
            logging.debug(f"{lock_postcode} {lock_cluster_id} {lock_id} State B->A")
            
            send_checkin_response(
                [BASE_TOPIC, lock_postcode, lock_cluster_id, lock_id, ' '],
                False, 'Check-in timed out. Check-in again and re-insert bike')
        else:
            logging.debug(f"{lock_postcode} {lock_cluster_id} {lock_id} is locked. Not modifying its state.")
    else:
        logging.debug(f"{lock_postcode} {lock_cluster_id} {lock_id} no longer in state B. Not modifying its state.")


def send_alarm_msg(subtopics, onoff):
    alarm_topic = ('/'.join( subtopics[:-1]+['alarm'] ))
    msg = {'status' : onoff}
    logging.debug(f"Publishing {msg} on {alarm_topic}")

    msg = bytes(json.dumps(msg), 'utf-8')
    client.publish(alarm_topic, msg)

def send_checkin_response(subtopics, status, message: str=''):
    response_topic = ('/'.join( subtopics[:-1]+['checkinresponse'] ))
    msg = {'status': status, 'message': message}
    logging.debug(f"Publishing {msg} on {response_topic}")

    msg = bytes(json.dumps(msg), 'utf-8')
    client.publish(response_topic, msg)

def update_usage_average_values():
    '''Call this function to update averages every week'''
    con = sl.connect(DB_PATH)

    # Get current usage stats
    all_locks = "SELECT lock_postcode, lock_cluster_id, num_lock, avg_usage FROM cluster_coordinates;"
    with con:
        data = con.execute(all_locks, [])
        lock_info = data.fetchall()
    
    # Iterate over locks
    for postcode, cluster, num_lock, avg_usage in lock_info:
        
        # Go through the past week's usage
        week_usage = [[[0 for k in range(num_lock)] for j in range(8)] for i in range(7)]
        time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_oneweekago = time_now - datetime.timedelta(days=7)
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
                time_oneweekago.strftime("%Y-%m-%d %H:%M:%S"),
                time_now,
                postcode, cluster
            ])
            usage_data = data.fetchall()

        # Iterate over usage entries in each week
        for lock_id, in_time, stay_duration in usage_data:
            in_time = datetime.datetime.strptime(in_time, "%Y-%m-%d %H:%M:%S")
            out_time = in_time + datetime.timedelta(seconds=stay_duration)
            while (in_time < out_time):
                hr_idx = int(in_time.strftime('%H'))//3
                week_idx = int(in_time.strftime('%w'))    # we index in 3-hour increments
                week_usage[week_idx][hr_idx][lock_id-1] = 1

                in_time += datetime.timedelta(hours=3)
        
        # Add to avg_usage
        usage_dict = json.loads( avg_usage.decode("utf-8") )
        daysOfWeek = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]
        for dayOfWeek in range(7):
            for hours in range(8):
                timeslot_usage = 0
                for lock in range(num_lock):
                    timeslot_usage += week_usage[dayOfWeek][hours][lock]
                
                timeslot_usage_percentage = int( (100*timeslot_usage)/num_lock )
                # Perform average
                usage_dict[daysOfWeek[dayOfWeek]][hours] = \
                    int( (usage_dict[daysOfWeek[dayOfWeek]][hours] + timeslot_usage_percentage)/2 )

        # update lock info
        json_data = json.dumps(usage_dict)
        logging.info(f"Updated {postcode} {cluster} averages with {json_data}")

        # serialise json into bytes
        json_data = bytes(json_data, 'utf-8')
        update_blob = '''
            UPDATE cluster_coordinates SET avg_usage=?
            WHERE lock_postcode=? AND lock_cluster_id=?;
        '''
        with con:
            con.execute(update_blob, [json_data, postcode, cluster])

# Main code
if __name__ == "__main__":
    # Start logger
    logging.basicConfig(level=logging.DEBUG, 
        # format="%(asctime)s %(process)d [%(levelname)s]: %(message)s",
        format="[%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        # filename='python_server.log', 
        # filemode='a'
        )   # uncomment above to just write to file

    # Connect to database
    if not os.path.exists(DB_PATH):
        logging.info("Database not found. Has it been created?")
        exit(1)
        
    client = mqtt.Client(CLIENT_NAME)                           # Create client object
    if True:
        client.username_pw_set("user", password="user")             # Set username and password
        client.tls_set(ca_certs='../comms/auth/ca.crt', tls_version=ssl.PROTOCOL_TLSv1_2)
    else:
        BROKER_IP = "localhost"
        BROKER_PORT = 1883
    status = client.connect(BROKER_IP, port=BROKER_PORT)        # Connect to MQTT broker
    logging.info(f"{CLIENT_NAME} connect {mqtt.error_string(status)}")    # Error handling

    # add client callbacks
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_log = on_log

    conn_flag = False
    while not conn_flag:
        client.loop_start()
        logging.info("Waiting for connection to broker...")
        sleep(2)

    while conn_flag:
        sleep(60*60*24*7) # sleep 1 week
        update_usage_average_values()

    # ! Insert conditions to disconnect / stop looping here.
    # client.loop_stop()
    # client.disconnect()
