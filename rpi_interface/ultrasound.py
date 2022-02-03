import serial

class ultrasoundSensor:
    seial_loc = '/dev/ttyUSB'

    def __init__(self):
      # init sensor
      self.ser = serial.Serial(self.seial_loc, 9600, 8)

    def read(self):
      self.ser.flushInput()
      line = self.ser.readline() # eg "R123"
      return int(line[0:-1])