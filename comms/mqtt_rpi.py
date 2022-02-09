# Implement a simple script for publishing unsecurely
from datetime import datetime
from msilib.schema import Class
from time import strftime
import paho.mqtt.client as mqtt
import json
import datetime
from socket import gethostname

CLIENT_ID = "Rpi_"+gethostname()
TOPIC = "IC.embedded/GROUP_4/test"

class MessageHandler:

  def __init__(self):
    self.client = mqtt.Client(client_id=CLIENT_ID)               # client object
    status = self.client.connect("localhost",port=1883)          # connect to server
    print(mqtt.error_string(status))                        # error handling

  def sendMessage(self, stolen=False):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    msg = ""
    if stolen:
      # send a JSON message
      msg = {
              "stolen" : "yes",
              "time"  : timestamp
            }
    else: 
      msg = {
              "stolen" : "no",
              "time"  : timestamp
            }
    

    msg_json = json.dumps(msg)                                  # dump json object into string

    MSG_INFO = self.client.publish(TOPIC, bytes(msg_json, 'utf-8'))  # publish on selected topic
    print(mqtt.error_string(MSG_INFO.rc))

  # Returns either bikein [1], bikeout [2], or NULL (no message) [0]
  def getBikeStatus(self):
    pass
    # TODO


#status = client.disconnect()