import paho.mqtt.client as mqtt
from socket import gethostname
from time import sleep
import json

CLIENT_NAME = "Client_" + gethostname()
TOPIC = "ic_embedded_group_4/test"

# callbacks
def on_connect(client, userdata, flags, rc):
    global conn_flag
    conn_flag = True
    print("Client Connected", conn_flag)
    conn_flag = True

def on_disconnect(client, userdata, flags, rc):
    print("Client Disconnected")

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

    reply = json.dumps( { "msg": "received: " + payload["msg"] } )
    client.publish(TOPIC, bytes(reply, 'utf-8'))

client = mqtt.Client(CLIENT_NAME)                           # Create client object
status = client.connect("localhost",port=8883)              # Connect to MQTT broker
client.tls_set('./auth/ca/m2mqtt_ca.crt')
print(CLIENT_NAME, "connect", mqtt.error_string(status))    # Error handling

# add client callbacks
client.on_message = on_message
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_log = on_log

conn_flag = False
while not conn_flag:
    sleep(2)
    print("Waiting for connection...")
    client.loop()

sleep(2)
print("Client Publishing")
msg = { "payload" : "Hello world!" }
msg = bytes(json.dumps(msg), 'utf-8')
client.publish(TOPIC, "test123")
sleep(2)
client.loop()
client.disconnect()