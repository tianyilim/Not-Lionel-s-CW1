import paho.mqtt.client as mqtt
import ssl
from socket import gethostname
from time import sleep
from datetime import datetime
import json

LOCK_POSTCODE = "SW72AZ"
LOCK_CLUSTER_ID = 1
LOCK_ID = 1
CLIENT_NAME = "RPI_/{}/{}/{}".format(LOCK_POSTCODE, LOCK_CLUSTER_ID, LOCK_ID)
BASE_TOPIC = "ic_embedded_group_4/{}/{}/{}".format(LOCK_POSTCODE, LOCK_CLUSTER_ID, LOCK_ID)
# BROKER_IP = "35.178.122.34"
BROKER_IP = "localhost"
BROKER_PORT = 8883

# callbacks
def on_connect(client, userdata, flags, rc):
    global conn_flag
    conn_flag = True
    print("Client Connected with flag", rc)
    conn_flag = True

def on_disconnect(client, userdata, rc):
    print("Client Disconnected with flag", rc)

def on_log(client, userdata, level, buf):
    print("["+level+"]", buf)

def on_message(client, userdata, message):
    print("Got a message!", message)

    payload = json.loads( message.payload.decode("utf-8") )
    # decode message string from JSON
    print("message received ", payload)
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)

    # reply = json.dumps( { "msg": "received: " + payload["msg"] } )
    # client.publish(BASE_TOPIC, bytes(reply, 'utf-8'))

client = mqtt.Client(CLIENT_NAME)                           # Create client object
client.username_pw_set("user", password="user")             # Set username and password
client.tls_set(ca_certs='../comms/auth/ca.crt', tls_version=ssl.PROTOCOL_TLSv1_2)
status = client.connect(BROKER_IP, port=BROKER_PORT)             # Connect to MQTT broker
print(CLIENT_NAME, "connect", mqtt.error_string(status))    # Error handling

# add client callbacks
client.on_message = on_message
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_log = on_log

inout = input('>>> y for in, n for out, s for stolen\n')

print("Client Publishing")
msg = { "timestamp" :  datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
msg = bytes(json.dumps(msg), 'utf-8')
if inout == 'y':
    client.publish(BASE_TOPIC+'/in', msg)
elif inout == 's':
    client.publish(BASE_TOPIC+'/stolen', msg)
elif inout == 'n':
    client.publish(BASE_TOPIC+'/out', msg)

# conn_flag = False
# while not conn_flag:
#     client.loop_start()
#     sleep(2)
#     print("Waiting for connection...")

# sleep(2)
# sleep(2)
# client.loop_stop()

client.disconnect()