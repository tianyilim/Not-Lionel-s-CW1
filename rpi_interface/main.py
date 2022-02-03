from rpi_interface.accelerometer import accelerometerSensor
from rpi_interface.ultrasound import ultrasoundSensor

class monitor:

  ultrasound_allowance = 3
  num_ultrasound_measurements = 10

  def __init__(self):
    # init accelerometer
    self.accel = accelerometerSensor()
    self.accel.setRegisters()
    # init ultrasound
    self.usound = ultrasoundSensor()
    # modes: 0 - free, 1 - filled (monitor for theft)
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
      self.mode = 1
    else:
      # TODO
      print("Error: device locked with another bike")
  
  def releaseBike(self):
    if self.mode == 1:
      self.bike_distance = 0
    else:
      # TODO
      print("Error: device already unlocked")

  def monitorBike(self):
    if self.mode == 1:
      current_bike_distance = self.collectMeasurements(5)
      if abs(current_bike_distance - self.bike_distance) > self.ultrasound_allowance:
        # TODO
        # ALARM
        pass




if __name__ == "__main__":
    m = monitor()
    while True:
      m.monitorBike
      # TODO: Check for MQTT messages

      # If new user wants to park bike
      m.newBike()

      # If user wants to release bike
      m.releaseBike()
