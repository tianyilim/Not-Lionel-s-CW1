from accelerometer import AccelerometerSensor

import threading, queue
from time import sleep
from math import sqrt
from statistics import mean

class TheftDetector:

    def __init__(self): #init theft detection

        # Queue for sending information to outside script
        self.queue = queue.SimpleQueue()

        # Start a thread on which to run theft detection
        self.thread = threading.Thread(target=self.__detect)

        # Lock to make sure I2C connection is not interupted
        self.lock = threading.Lock()
        self.thread.start() #Start the thread


    def __detect(self): # thread which runs and detects abnormal accleration

        # Instantiate an accelerometer
        accelerometer = AccelerometerSensor()

        # Declare the initial acceleration history values (avoids the program to say it is stolen in first second)
        accel_history = [0.94,0.94,0.94,0.94,0.94]

        # Index used to emulate a stack
        index = 0

        # Check for abnormal acceleration
        while True:

            try:
                with self.lock:
                    new_reading = accelerometer.readAccelerometer()

                accel_history[index] = sqrt(sum([i**2 for i in new_reading]))
            except:
                print("Lock failed in theftdetector!")

            if mean([abs(i - 0.94) for i in accel_history ]) > 0.05:
                self.queue.put_nowait(True)
            else:
                self.queue.put_nowait(False)

            if index == 4:
                index = 0
            else:
                index += 1

            sleep(0.2)
