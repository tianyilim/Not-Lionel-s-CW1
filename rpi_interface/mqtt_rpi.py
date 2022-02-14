# Implement a simple script for publishing unsecurely
from datetime import datetime
# from msilib.schema import Class
from time import strftime
import paho.mqtt.client as mqtt
import json
import datetime
from socket import gethostname

# @sherwin python indent is 4 pls lolol
LOCK_POSTCODE = "SW7 2AZ"   # These parameters will be baked in at install-time
LOCK_CLUSTER_ID = 1
LOCK_ID = 1
CLIENT_ID = "{}:{}_{}_{}".format(gethostname(), LOCK_POSTCODE, LOCK_CLUSTER_ID, LOCK_ID)
BASE_TOPIC = "ic_embedded_group_4/{}/{}/{}".format(LOCK_POSTCODE, LOCK_CLUSTER_ID, LOCK_ID)
BROKER_IP = "localhost"
BROKER_PORT = 1883          # This will change to 8883 when we figure out TLS

# TODO periodically sync time with online, so that timestamps are accurate!

class MessageHandler:
    def __init__(self):
        self.client = mqtt.Client(client_id=CLIENT_ID)              # client object
        status = self.client.connect(BROKER_IP, port=BROKER_PORT)   # connect to server
        print(mqtt.error_string(status))                            # error handling
        self.client.subscribe(BASE_TOPIC+"/status")                 # sub to incoming messages
        self.client.on_message = self.__checkin_callback            # bind callback to checkin

        self.start()    # start to react to incoming messages on the defined topic

    def start(self):
        '''MQTT Client to start loop'''
        self.client.loop_start()
    
    def stop(self):
        '''MQTT Client to start receieving on the channel'''
        self.client.loop_stop()

    def sendMessage(self, stolen=False):
        '''Sends message to server on `BASE_TOPIC/stolen` with a timestamp
        The server assumes any message on `/stolen` indicates that the lock 
        has detected something stolen.

        So there is no need to send anything other than a timestamp in the message body.
        '''
        timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        
        if stolen:
            msg = { "timestamp"  : timestamp }
            msg = bytes(json.dumps(msg), 'utf-8')           # dump json object into string
            
            MSG_INFO = self.client.publish(BASE_TOPIC+'/stolen', msg)
            print(mqtt.error_string(MSG_INFO.rc))
        else: 
            # we actually don't need to publish for this
            msg = { "stolen" : "no", "time"  : timestamp }
    
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
    
  # Returns either bikein [1], bikeout [2], or NULL (no message) [0]
    def getBikeStatus(self):
        # For now just read from terminal
        return input("Enter status: 0 - NULL, 1 - bikein, 2 - bikeout")
        pass
        # TODO

    def __checkin_callback(self, client, userdata, message):
        """Function to bind to checkin function
        """
        payload = json.loads( message.payload.decode("utf-8") )
        
        timestamp = payload['timestamp']
        # todo check if timestamp is sensible (security)

        inout = payload['in_out']
        if (inout == "in"):
            # TODO hardware things for checking in
            print("Lock checked in!")
        elif (inout == "out"):
            # TODO hardware things for checking out
            print("Lock checked out!")
        else:
            assert False, "Lock received an invalid value on /status[in_out]: {}".format(inout)

        # print("message received ", payload)
        # print("message topic=",message.topic)
        # print("message qos=",message.qos)
        # print("message retain flag=",message.retain)

#status = client.disconnect()