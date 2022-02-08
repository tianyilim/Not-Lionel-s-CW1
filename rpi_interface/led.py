from gpiozero import RGBLED
from colorzero import Color

class LED:

    def __init__(self): #init LED
        self.led = RGBLED(27, 22, 23, active_high = False)

    def turnOff(self): #Turn led off
        self.led.off()

    def setColor(self,color): #Set LED to given color
        #Takes in tuple of length 3 with rgb color values between 0 and 1.0
        self.led.color = Color.from_rgb(color[0],color[1],color[2])

    def startAlarm(self): #Sets LED to blink rapidly
        self.led.blink(on_time=0.1, off_time=0.1, on_color=(1, 0, 0), off_color=(1, 1, 1))
    
