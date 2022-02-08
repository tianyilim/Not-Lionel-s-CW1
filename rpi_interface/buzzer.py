from gpiozero import TonalBuzzer
from gpiozero.tones import Tone
from time import sleep

import threading

class Buzzer:
    pin_num = 17 #GPIO pin at which buzzer is connected

    def __init__(self): #init buzzer
        #Instantiate a TonalBuzzer element
        self.buzzer = TonalBuzzer(17, mid_tone=Tone('G6'), octaves=3)

        #Set initial values of parameters
        self.stopping = False #If this is set True, buzzer will stop playing sound

    def stop(self): #Stops all sound being played
        self.stopping = True

    def play(self,sound): #Plays a sound on the buzzer

        if sound == 'alarm':
            #Create a thread for the buzzer functions to execute on
            self.thread =  threading.Thread(target=self.__alarm)
            self.thread.start() #Start the thread
        elif sound == 'inserted':
            #Create a thread for the buzzer functions to execute on
            self.thread =  threading.Thread(target=self.__inserted)
            self.thread.start() #Start the thread
        elif sound == 'removed': #Removed
            #Create a thread for the buzzer functions to execute on
            self.thread =  threading.Thread(target=self.__removed)
            self.thread.start() #Start the thread
        else:
            raise ValueError("The requested sound does not exist")

    def __inserted(self): #Plays an "inserted" sound
        self.buzzer.play(Tone('A6'))
        sleep(0.1)
        self.buzzer.play(Tone('B6'))
        sleep(0.1)
        self.buzzer.play(Tone('D7'))
        sleep(0.1)
        self.buzzer.stop()

    def __removed(self):  #Plays a "removed" sound
        self.buzzer.play(Tone('A6'))
        sleep(0.1)
        self.buzzer.play(Tone('F5'))
        sleep(0.1)
        self.buzzer.play(Tone('E5'))
        sleep(0.1)
        self.buzzer.stop()

    def __alarm(self):

        i = 0
        notes = ['A6','A6','A6','A6','A6','C7','C7','C7','C7','C7'] #Sequence of notes which will be played

        while True:
            
            #Check if sound should stop playing
            if self.stopping == True:
                self.stopping = False
                self.buzzer.stop()
                return

            self.buzzer.play(Tone(notes[i]))

            if i >= len(notes) - 1: #Make sound loop
                i = 0
            else:
                i += 1

            sleep(0.1) #Each note lasts 100 ms
    