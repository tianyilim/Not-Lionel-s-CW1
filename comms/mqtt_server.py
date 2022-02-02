from antigravity import geohash
import paho.mqtt.client as mqtt
from socket import gethostname
from time import sleep

CLIENT_NAME = "Server_" + gethostname()
TOPIC = "IC.embedded/GROUP_4/test"

# callback
def on_message(client, userdata, message):
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)

client = mqtt.Client(CLIENT_NAME)
status = client.connect("localhost",port=1883)
print(CLIENT_NAME, "connect", mqtt.error_string(status))

# add client callback
client.on_message = on_message

# spin
client.loop_start()
# Subscribe to a topic
client.subscribe(TOPIC)
print(CLIENT_NAME, "subscribed to", TOPIC)

sleep(10)
client.loop_stop()
client.disconnect()