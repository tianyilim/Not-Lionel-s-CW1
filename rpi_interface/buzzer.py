from urllib.parse import ParseResultBytes
from gpiozero import TonalBuzzer
from gpiozero.tones import Tone
from time import sleep

import threading

class Buzzer:
    pin_num = 17 #GPIO pin at which buzzer is connected

    def __init__(self): #init buzzer

        #Instantiate a TonalBuzzer element
        self.buzzer = TonalBuzzer(17, mid_tone=Tone('G6'), octaves=3)

        #Variable used to enable an alarm which is not turned off by other sounds being played
        self.blocked = False

        #Declare some variables
        self.i = 0 # Index variable
        self.notes = [] #Sequence of notes which will be played
        self.repeat = False # Determines whether notes should be replayed

        #Create a thread to control the buzzer
        self.thread =  threading.Thread(target=self.__play,daemon=True)
        self.thread.start() #Start the thread

    def play(self,sound): #Plays a sound on the buzzer

        if not self.blocked:
            if sound == 'inserted':
                self.i = 0
                self.notes = ['A6','B6','D7']
                self.repeat = False
            elif sound == 'removed':
                self.i = 0
                self.notes = ['A6','F5','E5']
                self.repeat = False
            elif sound == 'alarm':
                self.i = 0
                self.notes = ['A6','A6','A6','A6','A6','C7','C7','C7','C7','C7']
                self.repeat = True
            elif sound == 'blocking_alarm':
                self.i = 0
                self.notes = ['A6','A6','A6','A6','A6','C7','C7','C7','C7','C7']
                self.repeat = True
                self.blocked = True
            else:
                raise ValueError("The requested sound does not exist")

    def stop(self):
        if not self.blocked:
            self.buzzer.stop()
            self.i = 0
            self.notes = []
            self.repeat = False

    def unblock(self): # Returns buzzer to normal function after a blocked alarm has been played 
        self.blocked = False


    def __play(self):

        while True:

            if len(self.notes) > 0:

                self.buzzer.play(Tone(self.notes[self.i]))

                self.i += 1

                if self.i >= len(self.notes):
                    if self.repeat:
                        self.i = 0
                    else:
                        self.stop()

            sleep(0.1) #Each note lasts 100 ms
    