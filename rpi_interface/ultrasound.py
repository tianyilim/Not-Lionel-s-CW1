import smbus2

class UltrasoundSensor:
    i2c_bus_num = 1 # bus 1 is connected to the breakout adapter
    address = 0x48 # Assumes ADDR connected to ground

    def __init__(self): #init sensor
      #Create a bus instance, bus 1 is connected to the breakout adapter
      self.bus = smbus2.SMBus(1)

      #Configure ADC to convert from A0
      write = smbus2.i2c_msg.write(self.address, [0x01,0x44,0x83])
      self.bus.i2c_rdwr(write)

      #Configure ADC to read subsequent data from the conversion register
      write = smbus2.i2c_msg.write(self.address, [0x00])
      self.bus.i2c_rdwr(write)


    def read(self):
      #Returns the distance measured by the ultrasonic sensor in cm

      #Read in the two bytes which give the distance
      read = smbus2.i2c_msg.read(self.address,2)
      self.bus.i2c_rdwr(read)

      #Convert the bytes to a signed int
      result = int.from_bytes(read.buf[0]+read.buf[1],byteorder='big', signed=True)

      #Convert the result to a voltage (mv)
      voltage = result/2**15*2048

      #Convert voltage to a distance (cm)
      distance = voltage/6.4*2.54

      return distance
      