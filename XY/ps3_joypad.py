
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
        self.enabled = False

    def read_status(self):

        self.payload = unpack('IhBB', os.read(self.fd, 8))

    def start(self, callback_object, debug=False):
        """
        This is the most important function, we pretend to have a callback_object with the following API:

        -   stop()
        -   move(axis,value)
        # 1  up = -  down = +
        # 0 left = - right = +

        #square 15 1 = up
        #square 15 0 = down
        """

        #In case if you want to run with the test class
        if(debug):
            while(True):
                self.read_status()
                if(self.payload[2] == 0x01 or (self.payload[2] == 0x02 and self.payload[3] < 5)):
                    callback_object.print_values(self.payload[3], self.payload[1])
        else:
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
        #Outer if to check the start button
        if((self.payload[3] == 3) and (self.payload[1] == 1)):
            print("START PRESSED")
            if(self.enabled):
                callback_object.reset_motors()
            else:
                callback_object.mx.stepdir_mode = 0
                callback_object.my.stepdir_mode = 0
                #disable interp
                callback_object.mx.step_interpolation_enable = 0
                callback_object.my.step_interpolation_enable = 0
                #Set speed mode
                callback_object.mx.ramp_mode = 2
                callback_object.my.ramp_mode = 2

            self.enabled = not self.enabled

        #If the joypad is enabled, read manage every button binding
        if(self.enabled):
            if((self.payload[3] == 15) and (self.payload[1] == 1)):
                callback_object.stop()
            elif((self.payload[3] == 12) and (self.payload[1] == 1)):
                callback_object.homing()

    def joystick_moved(self, callback_object):
        #same as button pressed but for axis
        if(self.enabled):
            if(self.payload[3] < 4):
                callback_object.set_speed(self.payload[3], self.payload[1]/MAX_AXES_VALUE)

    events_type = {
        0x01:button_pressed,
        0x02:joystick_moved
    }



if __name__ == "__main__":
    js = PS3XYController("/dev/input/js0")
    test = Test()
    js.start(test,debug=True)
