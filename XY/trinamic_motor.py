from __future__ import division
import sys
sys.path.insert(0,'../')

import threading
import time
import math as mt

from utils import *
from TMCL import *

class TrinamicMotor(object):
    """
    Model a trinamic motor enabled to read TMCL language.
    Member variables are properties and are made in such a way is easy to update
    a motor parameter

    Missing:
    A strong debug system and error checking.
    """
    def __init__(self, interface, params, lock=None, debug=False):
        """
        Parameters
        ----------
        interface : Serial instance from PySerial (opened interface)
        params : dict
            A dictionary containing all the parameters of the motor
        lock : Lock instance
            A lock instance in order to avoid race conditions to Serial calls.
        debug : bool
            Enable disable debug
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
        self.next_speed = 0
        self.next_position = self.actual_position
        self.stepdir_mode = self.params['step_direction_mode']
        self.step_interpolation_enable = self.params['step_interpolation_enable']
        self.microstep_resolution = self.params['microstep_resolution']
        self.freewheeling_delay = self.params['freewheeling_delay']
        self.max_current = self.params['max_current']
        self.ramp_mode = self.params['ramp_mode']
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
    def stop(self):
        self.stepdir_mode = 0
        self.step_interpolation_enable = 0
        self.query((self.serial_addr,3,0,0,0))
        #self.reset_motor_params()

    @threaded
    def home(self):
        """
        Searches for the home position (pos min and pos max)
        """
        temp = 0
        wait_time = 0.01

        #Disable step dir
        self.stepdir_mode = 0
        #disable interp
        self.step_interpolation_enable = 0

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

        self.reset_motor_params()




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
    # Global parameters
    ############################################################################
    #HOST ADDRESS
    # def get_host_address(self): return self.query((self.serial_addr,10,76,0,0))[1]
    #
    # def set_host_address(self, value): self.query((self.serial_addr,9,76,0,value))
    #
    # host_address = property(get_host_address,set_host_address)

    #SERIAL ADDRESS
    # def get_serial_address(self): return self.query((self.serial_addr,10,66,0,0))[1]
    #
    # def set_serial_address(self, value): self.query((self.serial_addr,9,66,0,value))
    #
    # serial_address = property(get_serial_address,set_serial_address)

    ############################################################################
    # Motor Axis Parameters
    ############################################################################
    #STEP/DIRECTION MODE
    def get_stepdir_mode(self): return self.query((self.serial_addr,6,254,0,0))[1]

    def set_stepdir_mode(self, value): self.query((self.serial_addr,5,254,0,value))

    stepdir_mode = property(get_stepdir_mode,set_stepdir_mode)

    #STEP INTERPOLATION ENABLE
    def get_step_interpolation_enable(self): return self.query((self.serial_addr,6,160,0,0))[1]

    def set_step_interpolation_enable(self, value): self.query((self.serial_addr,5,160,0,value))

    step_interpolation_enable = property(get_step_interpolation_enable,set_step_interpolation_enable)

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
