from accelerometer import AccelerometerSensor
from ultrasound import UltrasoundSensor
from buzzer import Buzzer
from mqtt_rpi import MessageHandler

from time import sleep

class monitor:

  ultrasound_allowance = 3
  num_ultrasound_measurements = 10

  def __init__(self):
    # init accelerometer
    self.accel = AccelerometerSensor()
    # init ultrasound
    self.usound = UltrasoundSensor()
    self.buzzer = Buzzer()
    self.mh = MessageHandler()
    # modes: 0 - free, 1 - filled (monitor for theft)
    """
    States:
    0 - No bike inserted (free)
    1 - Bike is inserted
    2 - Bike wrongfully removed
    3 - Alarm
    """
    self.mode = 0

  def collectMeasurements(self, num_measurements):
    measurement = 0
    for i in range(num_measurements):
      measurement += self.usound.read()
    return measurement / num_measurements

  def calibrateUltrasound(self):
    self.bike_distance = self.collectMeasurements(self.num_ultrasound_measurements)

  def newBike(self):
    if self.mode == 0:
      self.calibrateUltrasound()
      self.buzzer.play('inserted')
      self.mode = 1
    else:
      # TODO
      print("Error: device locked with another bike")
  
  def releaseBike(self):
    if self.mode == 1:
      self.buzzer.play('removed')
      self.bike_distance = 0
      self.mode = 0
    else:
      # TODO
      print("Error: device already unlocked")

  def monitorBike(self):
    if self.mode == 1:
      current_bike_distance = self.collectMeasurements(5)
      if abs(current_bike_distance - self.bike_distance) > self.ultrasound_allowance:
        # Bike removed
        self.mh.sendMessage(True)
        self.mode = 2

  def soundAlarm(self):
    self.buzzer.play('alarm')
    sleep(5)
    self.buzzer.stop()
    self.mode = 0





if __name__ == "__main__":
    m = monitor()
    
    while True:
      # TODO: Check for MQTT messages
      bikestatus = input("Enter status: 0 - NULL, 1 - bikein, 2 - bikeout") #m.mh.getBikeStatus()

      if m.mode == 0: # No bike
        if bikestatus == 1: # bikein
          m.newBike()

      elif m.mode == 1: # Bike inside
        if bikestatus == 2: # bikeout
          m.releaseBike()
        else:
          m.monitorBike()

      elif m.mode == 2: # Bike wrongly removed
        # TODO: Extension: Get confirmation from server
        m.mode = 3

      elif m.mode == 3: # Alarm
        m.soundAlarm()

      

      # If new user wants to park bike
      

      # If user wants to release bike
      
