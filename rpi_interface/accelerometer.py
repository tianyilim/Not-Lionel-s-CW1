import smbus2

class ultrasoundSensor:
    i2c_bus_num = 1
    address = 0

    def __init__(self):
      # init sensor
      self.bus = smbus2.SMBus(self.i2c_bus_num)
      # Select data rate, low-power mode (8-bit data), enable z y x axes

    def setRegisters(self):
      ctr_reg_1 = 0b00101111 # data rate set to 10 Hz
      self.bus.write_byte_data(self.address, 0x20, ctr_reg_1, True)
      
      # enable temperature sensor
      temp_cfg_reg = 0b11000000
      self.bus.write_byte_data(self.address, 0x1f, temp_cfg_reg, True)

    def readTemperature(self):
      return self.bus.read_byte_data(self.address, 0x0c)


                