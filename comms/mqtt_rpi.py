# Implement a simple script for publishing unsecurely
from datetime import datetime
from time import strftime
import paho.mqtt.client as mqtt
import json
import datetime
from socket import gethostname

CLIENT_ID = "Rpi_"+gethostname()
TOPIC = "IC.embedded/GROUP_4/test"

client = mqtt.Client(client_id=CLIENT_ID)               # client object
status = client.connect("localhost",port=1883)          # connect to server
print(mqtt.error_string(status))                        # error handling

timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")

# send a JSON message
msg = {
        "topic" : "hello",
        "time"  : timestamp
      }

msg_json = json.dumps(msg)                                  # dump json object into string

MSG_INFO = client.publish(TOPIC, bytes(msg_json, 'utf-8'))  # publish on selected topic
print(mqtt.error_string(MSG_INFO.rc))

status = client.disconnect()