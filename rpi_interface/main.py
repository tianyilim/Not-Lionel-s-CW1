from accelerometer import AccelerometerSensor
from ultrasound import UltrasoundSensor
from buzzer import Buzzer
from mqtt_rpi import MessageHandler
from led import LED

from time import sleep

class monitor:

    ultrasound_allowance = 3
    num_ultrasound_measurements = 10
    nobike_threshold = 50

    def __init__(self):
        # init ultrasound
        self.usound = UltrasoundSensor()
        self.buzzer = Buzzer()
        self.mh = MessageHandler()
        self.led = LED()

        """
        States:
        0 - Start
        1 - No bike inserted
        2 - Bike inserted (monitoring)
        3 - Alarm
        """
        self.mode = 0
        self.currDistance = 0

    '''
    mode 0:
    Take measurements to get to next state
    '''
    def noBikeInit(self):
        dist = self.collectMeasurements(self.num_ultrasound_measurements)
        if dist < self.nobike_threshold :
            print("Initial d: ", dist)
            self.currDistance = dist
            self.led.noBike()
            self.mode = 1

    '''
    mode 1
    Check if distance has decreased meaning bike is inserted
    '''
    def waitForBike(self):
        dist = self.collectMeasurements(self.num_ultrasound_measurements)
        if dist < self.currDistance :
            print("Bike inserted. d: ", dist)
            self.currDistance = dist
            self.mh.sendMessage(True) # Bike in
            self.buzzer.play('inserted')
            self.led.hasBike() # orange
            self.mode = 2

    '''
    mode 2
    Monitor bike for removal.
    Alarm if alarmed (mode 3), else goto mode 0
    '''
    def monitorBike(self):
        current_bike_distance = self.collectMeasurements(5)
        if abs(current_bike_distance - self.currDistance) > self.ultrasound_allowance:
          print("Bike removed! Distance: ", current_bike_distance, "cm")
          # Bike removed
          self.mh.sendMessage(False) # Bike removed
          if self.mh.getAlarmStatus():
              # Sound alarm
              self.mode = 3
              self.buzzer.play('alarm')
              self.led.startAlarm()
          else:
              self.mode = 0
              self.led.turnOff()

    '''
    mode 3
    Sounding alarm till stopped
    '''
    def soundAlarm(self):
          if not self.mh.getAlarmStatus():
              self.buzzer.stop()
              self.mode = 0
              self.led.turnOff()

    def collectMeasurements(self, num_measurements):
        measurements = []
        for i in range(num_measurements):
          measurements.append(self.usound.read())
        measurements.sort()
        acc = 0
        for m in measurements[2:num_measurements-3]:
            acc += m
        return acc / (num_measurements - 4)





if __name__ == "__main__":
    m = monitor()
    
    while True:
        sleep(0.1)

        if m.mode == 0:
            m.noBikeInit()

        elif m.mode == 1:
            m.waitForBike()

        elif m.mode == 2:
            m.monitorBike()

        elif m.mode == 3:
            m.soundAlarm()
        
