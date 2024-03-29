from accelerometer import AccelerometerSensor
from ultrasound import UltrasoundSensor
from buzzer import Buzzer
from mqtt_rpi import MessageHandler
from led import LED
from theftdetector import TheftDetector
from statistics import median

from time import sleep
import time

class monitor:

    nobike_threshold = 50

    def __init__(self):
        # init ultrasound
        self.usound = UltrasoundSensor()
        self.buzzer = Buzzer()
        self.mh = MessageHandler()
        self.led = LED()
        self.tdetector = TheftDetector()

        """
        States:
        0 - No bike inserted
        1 - Bike inserted (monitoring)
        2 - Alarm
        """
        self.mode = 0

        # Variable used to keep track of ultrasound measurements
        self.measurements = [200,200,200,200,200]

        # Turn on the LED
        self.led.noBike()

        # Timing variable
        self.time = time.time()

    '''
    mode 0
    Check if measured distance is smaller than the threshold for a bike to be inserted
    '''
    def waitForBike(self):
        if median(self.measurements) < self.nobike_threshold:
            print("Bike inserted. d: ", median(self.measurements))
            self.mh.sendMessage(True) # Bike in
            self.buzzer.play('inserted')
            self.led.hasBike() # orange
            self.mode = 1

    '''
    mode 1
    Monitor bike, if bike removed without permission go to alarm (mode 2), if removed with permission go to (mode 0)
    '''
    def monitorBike(self):
        if median(self.measurements) > self.nobike_threshold:
          print("Bike removed! Distance: ", median(self.measurements), "cm")
          # Bike removed
          if self.mh.getAlarmStatus():
              # Sound alarm
              self.mode = 2
              self.time = time.time()
              self.buzzer.play('alarm')
              self.led.startAlarm()
              self.mh.sendMessage(None, stolen=True)
          else:
              self.mode = 0
              self.buzzer.play('removed')
              self.led.noBike()
              self.mh.sendMessage(False) # Bike removed

    '''
    mode 2
    Sounding alarm till stopped
    '''
    def soundAlarm(self):
          if not self.mh.getAlarmStatus() or time.time() - self.time > 20:
              self.buzzer.stop()
              self.mode = 0
              self.led.noBike()


    def collectMeasurement(self):
        try:
            self.measurements.insert(0,self.usound.read())
            self.measurements.pop()
        except:
            pass
        return


    def checkIfStolen(self):
        if not self.tdetector.queue.empty():
            stolen = False

            while not self.tdetector.queue.empty():
                try:
                    stolen = stolen or self.tdetector.queue.get_nowait()
                except:
                    pass
                
            if (not self.led.blocked) and stolen:
                self.led.blockedAlarm()
                self.buzzer.play('blocking_alarm')
            elif self.led.blocked and not stolen:
                # Turn of LED
                self.led.unblock()
                if self.mode == 0:
                    self.led.noBike()
                elif self.mode == 1:
                    self.led.hasBike()
                elif self.mode == 2:
                    self.led.startAlarm()
                else:
                    self.led.turnOff()

                # Turn of buzzer
                self.buzzer.unblock()
                self.buzzer.stop()


if __name__ == "__main__":
    m = monitor()
    
    while True:
        sleep(0.1)

        # Measure the distance using the ultrasound sensor
        m.collectMeasurement()

        # Check if the lock itself is being stolen
        m.checkIfStolen()


        if m.mode == 0:
            m.waitForBike()

        elif m.mode == 1:
            m.monitorBike()

        elif m.mode == 2:
            m.soundAlarm()
        
