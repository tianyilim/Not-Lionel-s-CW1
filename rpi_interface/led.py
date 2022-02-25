from gpiozero import RGBLED
from colorzero import Color

class LED:

    def __init__(self): #init LED
        self.led = RGBLED(23, 22, 27, active_high = False)

        self.blocked = False # Used to ensure that alarm is triggered if device is stolen

    def turnOff(self): #Turn led off
        if not self.blocked:
            self.led.off()

    def setColor(self,color): #Set LED to given color
        #Takes in tuple of length 3 with rgb color values between 0 and 1.0
        if not self.blocked:
            self.led.color = Color.from_rgb(color[0],color[1],color[2])

    def startAlarm(self): #Sets LED to blink rapidly
        self.led.blink(on_time=0.1, off_time=0.1, on_color=(1, 0, 0), off_color=(1, 1, 1))

    def noBike(self):
        if not self.blocked:
            self.led.pulse(fade_in_time=1, fade_out_time=1, on_color=(0, 1, 0), off_color=(0.25, 1, 0.25), n=None, background=True)

    def hasBike(self):
        if not self.blocked:
            self.led.pulse(fade_in_time=1, fade_out_time=1, on_color=(1, 0.4, 0), off_color=(1, 0.6, 0), n=None, background=True)

    def blockedAlarm(self): # Alarm which will not be turned off by any other function being called
        self.blocked = True
        self.startAlarm()

    def unblock(self): # Unblocks the LED so that normal operation is restored
        self.blocked = False    
