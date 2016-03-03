from __future__ import division
import sys
sys.path.insert(0,'/root/PyTMCL')

import threading
import time
import math as mt

from utils import *
from TMCL import *

class TrinamicMotor(object):
    def __init__(self, interface, params, lock=None, debug=False):
        """
        Initialize the motor
        -   params: contains the operating ranges of the motor
        """
        self.params = params
        self.debug = debug
        self.interface = interface
        self.query = self.interface.query

        if(lock != None):
            self.lock = lock

        self.serial_addr = params['serial_addr']
        self.spr = params['steps_per_rotation']
        self.direction = params['direction'] #Not implemented yet

        self.reset_motor_params()

        self.pos_ranges = [None,None]

    @classmethod
    def from_new_interface(cls, dev, params, lock=None, baudrate=115200, debug=False):
        """
        Set the interface from an already opened instance
        """
        interface = communication.TMCLCommunicator(dev, baudrate, debug)

        return cls(interface, params, lock, debug)

    def reset_motor_params(self):
        self.microstep_resolution = self.params['microstep_resolution']
        self.freewheeling_delay = self.params['freewheeling_delay']
        self.max_current = self.params['max_current']
        self.ramp_mode = self.params['ramp_mode']
        self.max_acceleration = self.params['max_acceleration']
        self.max_positioning_speed = self.params['max_positioning_speed']

    def reset_posmode_params(self):
        self.max_current = self.params['max_current']
        self.ramp_mode = 0
        self.max_acceleration = self.params['max_acceleration']
        self.max_positioning_speed = self.params['max_positioning_speed']

    def locked_query(self, request):
        """
        Wrapper in order to avoid race conditions (even if GIL is enabled
        this is the safest option)
        """
        with self.lock:
            return self.interface.query(request)

    def speed2ustepps(self, speed):
        """
        Convert the speed into steps per second
        """
        return speed * (16e6 / 65536) / (0x01 << self.pulse_divisor)

    def ustepps2speed(self, ustepps):
        """
        Convert the steps per seconds into the motor unit of speed
        """
        return int(ustepps/((16e6 / 65536) / (0x01 << self.pulse_divisor)))

    @threaded
    def home(self):
        """
        Searches for the home position (pos min and pos max)
        """
        temp = 0
        wait_time = 0.01
        ##Velocity mode
        self.ramp_mode = 2
        ##Low max current
        self.max_current = 97
        ##Set microstep resolution
        home_microstep_resolution = 4
        self.microstep_resolution = home_microstep_resolution
        ##Set max acceleration
        self.max_acceleration = 2047

        #Search the min value (negative speed)
        self.next_speed = -150

        time.sleep(0.2)
        while(self.load_value > 350):
            time.sleep(wait_time)
        self.next_speed = 0
        self.actual_position = 0 #Set position to 0
        temp = self.actual_position
        self.pos_ranges[0] = temp

        #Search max value
        self.next_speed = 150

        time.sleep(0.2)
        while(self.load_value > 350):
            time.sleep(wait_time)
        self.next_speed = 0
        temp = self.actual_position
        self.pos_ranges[1] = temp

        #Reset old params
        self.microstep_resolution = self.params['microstep_resolution']
        self.max_current = self.params['max_current']
        self.ramp_mode = self.params['ramp_mode']
        self.max_acceleration = self.params['max_acceleration']
        self.max_positioning_speed = self.params['max_positioning_speed']

        self.pos_ranges[1] = int(self.pos_ranges[1] * 2**(self.microstep_resolution - home_microstep_resolution))
        self.next_position = self.actual_position - int(self.pos_ranges[1] / 2)
        while(not self.position_reached):
            time.sleep(wait_time)

        self.max_positioning_speed = 0
        self.actual_position = 0
        self.next_position = 0
        self.max_positioning_speed = self.params['max_positioning_speed']

        self.pos_ranges[1] = int(self.pos_ranges[1] / 2)
        self.pos_ranges[0] = -self.pos_ranges[1]




    ############################################################################
    # Class Handling
    ############################################################################
    def get_lock(self): return self._lock

    def set_lock(self, value):
        if(value != None ):
            self._lock = value
            self.query = self.locked_query
        else:
            self._lock = None
            self.query = self.interface.query

    lock = property(get_lock,set_lock)
    ############################################################################
    # Motor Axis Parameters
    ############################################################################
    #RAMP MODE
    def get_ramp_mode(self): return self.query((self.serial_addr,6,138,0,0))[1]

    def set_ramp_mode(self, value): self.query((self.serial_addr,5,138,0,value))

    ramp_mode = property(get_ramp_mode,set_ramp_mode)

    #MAX CURRENT
    def get_max_current(self): return self.query((self.serial_addr,6,6,0,0))[1]

    def set_max_current(self, value): self.query((self.serial_addr,5,6,0,value))

    max_current = property(get_max_current, set_max_current)

    #NEXT SPEED
    def get_next_speed(self): return self.query((self.serial_addr,6,2,0,0))[1]

    def set_next_speed(self, value): self.query((self.serial_addr,5,2,0,value))

    next_speed = property(get_next_speed, set_next_speed)

    #MICROSTEP RESOLUTION
    def get_microstep_resolution(self): return self.query((self.serial_addr,6,140,0,0))[1]

    def set_microstep_resolution(self, value): self.query((self.serial_addr,5,140,0,value))

    microstep_resolution = property(get_microstep_resolution, set_microstep_resolution)

    #LOAD VALUE
    def get_load_value(self): return self.query((self.serial_addr,6,206,0,0))[1]

    def set_load_value(self, value): pass

    load_value = property(get_load_value, set_load_value)

    #ACTUAL POSITION
    def get_actual_position(self): return self.query((self.serial_addr,6,1,0,0))[1]

    def set_actual_position(self, value): self.query((self.serial_addr,5,1,0,value))

    actual_position = property(get_actual_position, set_actual_position)

    #ACTUAL SPEED
    def get_actual_speed(self): return self.query((self.serial_addr,6,3,0,0))[1]

    def set_actual_speed(self, value): pass

    actual_speed = property(get_actual_speed, set_actual_speed)

    #FREEWHEELING DELAY
    def get_freewheeling_delay(self): return self.query((self.serial_addr,6,204,0,0))[1]

    def set_freewheeling_delay(self, value): self.query((self.serial_addr,5,204,0,value))

    freewheeling_delay = property(get_freewheeling_delay, set_freewheeling_delay)

    #NEXT POSITION
    def get_next_position(self): return self.query((self.serial_addr,6,0,0,0))[1]

    def set_next_position(self, value): self.query((self.serial_addr,5,0,0,value))

    next_position = property(get_next_position, set_next_position)

    #PULSE DIVISOR
    def get_pulse_divisor(self): return self.query((self.serial_addr,6,154,0,0))[1]

    def set_pulse_divisor(self, value): self.query((self.serial_addr,5,154,0,value))

    pulse_divisor = property(get_pulse_divisor, set_pulse_divisor)

    #PULSE DIVISOR
    def get_max_positioning_speed(self): return self.query((self.serial_addr,6,4,0,0))[1]

    def set_max_positioning_speed(self, value): self.query((self.serial_addr,5,4,0,value))

    max_positioning_speed = property(get_max_positioning_speed, set_max_positioning_speed)

    #MAX ACCELERATION
    def get_max_acceleration(self): return self.query((self.serial_addr,6,5,0,0))[1]

    def set_max_acceleration(self, value): self.query((self.serial_addr,5,5,0,value))

    max_acceleration = property(get_max_acceleration, set_max_acceleration)

    #POSITION REACHED
    def get_position_reached(self): return self.query((self.serial_addr,6,8,0,0))[1] == 1

    def set_position_reached(self, value): pass

    position_reached = property(get_position_reached, set_position_reached)

if(__name__ == "__main__"):
    pass