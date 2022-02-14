import paho.mqtt.client as mqtt
from socket import gethostname
from time import sleep
import json

CLIENT_NAME = "Server_" + gethostname()
TOPIC = "IC.embedded/GROUP_4/test"

# callback
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
status = client.connect("localhost",port=1883)              # Connect to MQTT broker
print(CLIENT_NAME, "connect", mqtt.error_string(status))    # Error handling

# add client callback
client.on_message = on_message

# loop for certain time
client.loop_start()
# Subscribe to a topic
client.subscribe(TOPIC)
print(CLIENT_NAME, "subscribed to", TOPIC)

sleep(10)
client.loop_stop()
client.disconnect()