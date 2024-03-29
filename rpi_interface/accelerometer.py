import smbus2
from time import sleep

class AccelerometerSensor:
    i2c_bus_num = 1 # bus 1 is connected to the breakout adapter
    address = 0x18 # Assumes SDO pad left unconnected

    def __init__(self): #init sensor

      #Create a bus instance
      self.bus = smbus2.SMBus(self.i2c_bus_num) 
      
      #Select data rate, normal mode at 100 Hz, enable z y x axes
      ctr_reg_1 = 0b01010111
      self.bus.write_byte_data(self.address, 0x20, ctr_reg_1)

      #Turn of filters
      ctr_reg_2 = 0b10100001
      self.bus.write_byte_data(self.address, 0x21, ctr_reg_2)

      #Send interrupt to INT1
      ctr_reg_3 = 0b01000000
      self.bus.write_byte_data(self.address, 0x22, ctr_reg_3)

      #Set measurements to non-continuous update (necessary to use thermometer), big endian notation, ±4g measurement range
      ctr_reg_4 = 0b00010000
      self.bus.write_byte_data(self.address, 0x23, ctr_reg_4)

      #Latch Interrupt 1 until it is read
      ctr_reg_5 = 0b00001000
      self.bus.write_byte_data(self.address, 0x24, ctr_reg_5)

      #INT1 threshold
      int1_ths = 0b00001000
      self.bus.write_byte_data(self.address, 0x32, int1_ths)

      #INT1 duration
      int1_duration = 0b00000000 #0.1s
      self.bus.write_byte_data(self.address, 0x33, int1_duration)

      #Enable temperature sensor and ADC
      temp_cfg_reg = 0b11000000
      self.bus.write_byte_data(self.address, 0x1f, temp_cfg_reg)

      sleep(0.1)

      #Configure interupt 1
      int1_cfg_reg = 0b00001010
      self.bus.write_byte_data(self.address, 0x30, int1_cfg_reg)



    def readTemperature(self):
      #Returns a temperature value with step size of celsius
      #Note temperature sensor is only good for measuring temperature changes

      #Get data from the two temperature registers
      raw_data = [self.bus.read_byte_data(self.address, 0x0c + i) for i in range(2)]

      #Convert raw bytes to signed ints
      temp = int.from_bytes(raw_data[0:2],byteorder='little', signed=True)

      #Convert to change in celsius
      temp /= 2**8

      return temp


    def readAccelerometer(self):
      #Returns a list of accelerations in the order [x,y,z] (unit = g-force)
      
      #Get data from all acceleration registers
      raw_data = [self.bus.read_byte_data(self.address, 0x28 + i) for i in range(6)]

      #Convert raw bytes to signed ints
      x = int.from_bytes(raw_data[0:2],byteorder='little', signed=True)
      y = int.from_bytes(raw_data[2:4],byteorder='little', signed=True)
      z = int.from_bytes(raw_data[4:6],byteorder='little', signed=True)
  
      #Convert signed ints to g-force
      acceleration = [x,y,z]
      acceleration = [i/(2**15)*4 for i in acceleration] #Factor of 4 as we measure ±4g

      return acceleration



                
