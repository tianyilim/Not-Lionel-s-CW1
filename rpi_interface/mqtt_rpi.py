# Implement a simple script for publishing unsecurely
from datetime import datetime
# from msilib.schema import Class
from time import strftime
import paho.mqtt.client as mqtt
import json
import datetime
from socket import gethostname
import queue
import ssl

# @sherwin python indent is 4 pls lolol
LOCK_POSTCODE = "SW7 2AZ"   # These parameters will be baked in at install-time
LOCK_CLUSTER_ID = 1
LOCK_ID = 1
CLIENT_ID = "{}:{}_{}_{}".format(gethostname(), LOCK_POSTCODE, LOCK_CLUSTER_ID, LOCK_ID)
BASE_TOPIC = "ic_embedded_group_4/{}/{}/{}".format(LOCK_POSTCODE, LOCK_CLUSTER_ID, LOCK_ID)
BROKER_IP = "35.178.122.34"         # AWS IP
BROKER_PORT = 8883                  # MQTT Secure Port

# TODO periodically sync time with online, so that timestamps are accurate!

class MessageHandler:
    def __init__(self):
        client = mqtt.Client(CLIENT_ID)                           # Create client object
        client.username_pw_set("user", password="user")             # Set username and password
        client.tls_set(ca_certs='../comms/auth/ca.crt', tls_version=ssl.PROTOCOL_TLSv1_2)
        # Assume that you are running this from this directory.

        status = client.connect(BROKER_IP, port=BROKER_PORT)        # Connect to MQTT broker
        print(CLIENT_ID, "connect", mqtt.error_string(status))    # Error handling

        client.subscribe(BASE_TOPIC+"/alarm")   # you need to listen to Alarm                # sub to incoming messages
        self.client.on_message = self.__alarm_callback            # bind callback to checkin
        self.alarmQueue = queue.Queue(1)
        self.alarmed = 0

        self.start()    # start to react to incoming messages on the defined topic

    def start(self):
        '''MQTT Client to start loop'''
        self.client.loop_start()
    
    def stop(self):
        '''MQTT Client to start receieving on the channel'''
        self.client.loop_stop()

    def sendMessage(self, bikein):
        '''Sends message to server on `BASE_TOPIC/stolen` with a timestamp
        The server assumes any message on `/stolen` indicates that the lock 
        has detected something stolen.

        So there is no need to send anything other than a timestamp in the message body.
        '''
        timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        
        msg = { "timestamp"  : timestamp } # dump json object into string
        msg = bytes(json.dumps(msg), 'utf-8') 

        if bikein:
            MSG_INFO = self.client.publish(BASE_TOPIC+'/in', msg)
            print(mqtt.error_string(MSG_INFO.rc))
        else: 
            MSG_INFO = self.client.publish(BASE_TOPIC+'/out', msg)
            print(mqtt.error_string(MSG_INFO.rc))
    
    def sendTelemetry(self, payload):
        '''Sends regular accelerometer data to the server for anomaly detection purposes.
        payload is a 2D list of float accel data. (not numpy array!)
        '''
        timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        
        # if payload is a np array, first run .to_list() on it.
        msg = {"timestamp" : timestamp,
                "payload" : payload }
        msg = bytes(json.dumps(msg), 'utf-8')

        MSG_INFO = self.client.publish(BASE_TOPIC+'/telemetry', msg)
        print(mqtt.error_string(MSG_INFO.rc))
    
    def getAlarmStatus(self):
        try:
            status = self.alarmQueue.get_nowait()
            self.alarmed = status
        except queue.Empty:
            pass

        return self.alarmed

    def __alarm_callback(self, client, userdata, message):
        """Function to bind to function
        """
        payload = json.loads( message.payload.decode("utf-8") )
        
        timestamp = payload['timestamp']
        # todo check if timestamp is sensible (security)

        alarmStatus = payload['status']
        if alarmStatus == 0 or alarmStatus == 1:
            self.alarmQueue.put(alarmStatus)
            print("Alarm set to ", alarmStatus)
        else:
            print("message received ", payload)
            print("message topic=",message.topic)
        
        
        # print("message qos=",message.qos)
        # print("message retain flag=",message.retain)

#status = client.disconnect()