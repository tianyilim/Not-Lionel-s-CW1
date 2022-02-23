# Changing MQTT on the RPi to be secure
Put this into wherever you make a connection to your client:
```python
# defines
LOCK_POSTCODE = 'SW72AZ'    # Choose between SW72AZ and W68EL. All caps, no space.
LOCK_CLUSTER_ID = 1         #
LOCK_ID = 1                 # Just set these for now. We can add more RPis to the network to load test.
BASE_TOPIC = "ic_embedded_group_4/{}/{}/{}".format(LOCK_POSTCODE, LOCK_CLUSTER_ID, LOCK_ID)
CLIENT_NAME = "RPI_/{}/{}/{}".format(LOCK_POSTCODE, LOCK_CLUSTER_ID, LOCK_ID)
BROKER_IP = "35.178.122.34"         # AWS IP
BROKER_PORT = 8883                  # MQTT Secure Port

client = mqtt.Client(CLIENT_NAME)                           # Create client object
client.username_pw_set("user", password="user")             # Set username and password
client.tls_set(ca_certs='../comms/auth/ca.crt', tls_version=ssl.PROTOCOL_TLSv1_2)
# Assume that you are running this from this directory.

status = client.connect(BROKER_IP, port=BROKER_PORT)        # Connect to MQTT broker
print(CLIENT_NAME, "connect", mqtt.error_string(status))    # Error handling

client.subscribe(BASE_TOPIC+"/alarm")   # you need to listen to Alarm
# Messages have format {status: onoff} where onoff is Boolean

# Add whatever else you need to do here (register callbacks, etc)
```