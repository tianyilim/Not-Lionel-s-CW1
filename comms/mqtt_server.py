import paho.mqtt.client as mqtt
import ssl
from socket import gethostname
from time import sleep
import json

CLIENT_NAME = "Server_" + gethostname()
TOPIC = "ic_embedded_group_4/test"

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

    reply = json.dumps( { "msg": "received: " + payload["msg"] } )
    client.publish(TOPIC, bytes(reply, 'utf-8'))

server = mqtt.Client(CLIENT_NAME)                           # Create client object
status = server.connect('localhost', port=8883)              # Connect to MQTT broker
server.tls_set(ca_certs='./auth/ca/ca.crt', certfile='./auth/client/client.crt', keyfile='./auth/client/client.key', tls_version=ssl.PROTOCOL_TLSv1_2)
print(CLIENT_NAME, "connect", mqtt.error_string(status))    # Error handling

# add client callback
server.on_message = on_message

# loop for certain time
server.loop_start()
# Subscribe to a topic
server.subscribe(TOPIC)
print(CLIENT_NAME, "subscribed to", TOPIC)

sleep(10)
server.loop_stop()
server.disconnect()