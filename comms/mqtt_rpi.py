# Implement a simple script for publishing unsecurely

import paho.mqtt.client as mqtt
from socket import gethostname

CLIENT_ID = "Rpi_"+gethostname()
TOPIC = "IC.embedded/GROUP_4/test"

client = mqtt.Client(client_id=CLIENT_ID)
status = client.connect("localhost",port=1883)
print(mqtt.error_string(status))

MSG_INFO = client.publish(TOPIC,"hello")
print(mqtt.error_string(MSG_INFO.rc))

status = client.disconnect()