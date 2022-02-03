import serial

class ultrasoundSensor:
    i2c_bus_num = 1

    def __init__(self):
      # init sensor
      self.bus = smbus2.SMBus(self.i2c_bus_num)