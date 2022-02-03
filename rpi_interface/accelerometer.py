import smbus2

class accelerometerSensor:
    i2c_bus_num = 1
    address = 0b0011000 # Assumes SDO pad connected to ground

    def __init__(self):
      # init sensor
      self.bus = smbus2.SMBus(self.i2c_bus_num)
      

    def setRegisters(self):
      # Select data rate, low-power mode (8-bit data), enable z y x axes
      ctr_reg_1 = 0b00101111 # data rate set to 10 Hz
      self.bus.write_byte_data(self.address, 0x20, ctr_reg_1, True)
      
      # enable temperature sensor
      temp_cfg_reg = 0b11000000
      self.bus.write_byte_data(self.address, 0x1f, temp_cfg_reg, True)

    def readTemperature(self):
      return self.bus.read_byte_data(self.address, 0x0c)

    def readAccelerometer(self):
      x = self.bus.read_byte_data(self.address, 0x28)
      y = self.bus.read_byte_data(self.address, 0x2a)
      z = self.bus.read_byte_data(self.address, 0x2c)
      return x, y, z

                