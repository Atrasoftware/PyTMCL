
import os
import time
from struct import *


#define JS_EVENT_BUTTON 0x01 // button pressed/released
#define JS_EVENT_AXIS   0x02 // joystick moved
#define JS_EVENT_INIT   0x80 // initial state of device

JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80
MIN_AXES_VALUE = -32768;
MAX_AXES_VALUE = 32767;

class Test(object):
    def __init__(self):
        pass

    def print_values(self, value1, value2):
        print("AXIS/BUTTON: "+ str(value1) + " VALUE: " + str(value2))

class PS3XYController(object):

    def __init__(self, device_file):
        self.fd = os.open(device_file, os.O_RDONLY)

        if( self.fd == 0 ): exit(1)

    def read_status(self):

        self.payload = unpack('IhBB', os.read(self.fd, 8))

    def start(self, callback_object):
        """
        This is the most important function, we pretend to have a callback_object with the following API:

        -   stop()
        -   move(axis,value)
        # 1  up = -  down = +
        # 0 left = - right = +

        #square 15 1 = up
        #square 15 0 = down
        """
        while(True):
            self.read_status()
            try:
                self.events_type[self.payload[2]](self, callback_object)
            except:
                pass
            #self.events_type
            #if(self.payload[2] != 2): print(self.payload[2])
            #select event type

    def button_pressed(self, callback_object):
        #print("BUTTON PRESSED, VALUE: " + str(self.payload[1]) + " BUTTON NUMBER: " + str(self.payload[3]))
        #callback(self.payload[3], self.payload[1])
        if((self.payload[3] == 15) and (self.payload[1] == 1)):
            callback_object.stop()

    def joystick_moved(self, callback_object):
        if(self.payload[3] < 4):
            callback_object.set_speed(self.payload[3], self.payload[1]/MAX_AXES_VALUE)
        #if(self.payload[3] < 4):
            #print("JOYSTICK MOVING, VALUE: " + str(self.payload[1]) + "AXIS: "+ str(self.payload[3]))
            #callback(self.payload[3], self.payload[1])

    events_type = {
        0x01:button_pressed,
        0x02:joystick_moved
    }



if __name__ == "__main__":
    js = PS3XYController("/dev/input/js0")
    test = Test()
    js.start(test.print_values)
