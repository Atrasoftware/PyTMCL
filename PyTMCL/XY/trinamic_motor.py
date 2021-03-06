from __future__ import division

import threading
import time
import math as mt

from .. TMCL import *
from . utils import *

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
        # Expect a dictionary (not nested, no references), do a shallow copy.
        self.params = params.copy()

        self.debug = debug
        self.interface = interface
        self.query = self.interface.query

        if(lock is not None):
            self.lock = lock

        self.serial_addr = params['serial_addr']
        self.spr = params['steps_per_rotation']
        self.direction = params['direction']  # Not imlemented yet

        self.reset_motor_params()

        self.home_microstep_resolution = 4

    @classmethod
    def from_new_interface(cls, dev, params, lock=None,
                           baudrate=115200, debug=False):
        """
        Set the interface from an already opened instance
        """
        interface = communication.TMCLCommunicator(dev, baudrate, debug)

        return cls(interface, params, lock, debug)

    def reset_motor_params(self):
        self.next_speed = 0
        self.stepdir_mode = self.params['step_direction_mode']
        self.step_interpolation_enable = \
            self.params['step_interpolation_enable']
        self.microstep_resolution = self.params['microstep_resolution']
        self.freewheeling_delay = self.params['freewheeling_delay']
        self.max_current = self.params['max_current']
        self.standby_current = self.params['standby_current']
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
        self.query((self.serial_addr, 3, 0, 0, 0))

    @threaded
    def limit_checker(self, direction, stall_value=-30,
                      encoder_dev=0, poll_time=0.01, speed=600):

        self.next_speed = 0
        self.next_position = 0
        self.encoder_position = self.actual_position = 0

        self.stepdir_mode = 0
        self.step_interpolation_enable = 0
        self.ramp_mode = 2
        self.max_current = 120
        self.microstep_resolution = self.home_microstep_resolution

        self.encoder_prescaler = 1600

        self.stop_on_stall = int(speed * 0.95)
        self.stall_guard = stall_value
        # steps per second
        usteps_per_second = self.speed2ustepps(speed)
        steps_per_poll = int(usteps_per_second * poll_time)
        self.max_acceleration = 2047

        self.max_encoder_deviation = encoder_dev
        time.sleep(0.1)
        if direction:
            self.next_speed = speed
        else:
            self.next_speed = -speed

        a = 0
        while(not a):
            a = self.error_flag
            time.sleep(poll_time)
            if a:
                break

        time.sleep(0.1)
        self.limit = int(self.encoder_position *
                         2**(self.microstep_resolution -
                             self.home_microstep_resolution))

        self.stop_on_stall = 2047
        self.max_encoder_deviation = 0
        self.reset_motor_params()

    @threaded
    def move_to(self, usteps, speed, relative=True):
        self.stepdir_mode = 0
        self.ramp_mode = 0
        self.max_positioning_speed = speed
        self.move_to_position(usteps, relative=relative)
        while(not self.position_reached):
            time.sleep(0.1)
        print("ok")
        self.ramp_mode = 2
        self.reset_motor_params()

    def home(self):
        """
        Automatically searches for the home position (pos min and pos max)
        """
        l1 = self.limit_checker(0)
        l1.join()
        l2 = self.limit_checker(1)
        l2.join()

        self.stepdir_mode = 0
        self.ramp_mode = 2

        self.next_position = self.actual_position - int(self.limit / 2)
        while(not self.position_reached):
            time.sleep(0.1)

        self.limit = int(self.limit / 2)

    def get_lock(self): return self._lock

    def set_lock(self, value):
        if(value is not None):
            self._lock = value
            self.query = self.locked_query
        else:
            self._lock = None
            self.query = self.interface.query

    lock = property(get_lock, set_lock)

    ############################################################################
    # Global parameters
    ############################################################################
    # HOST ADDRESS
    # def get_host_address(self): return self.query((self.serial_addr,10,76,0,0))[1]
    #
    # def set_host_address(self, value): self.query((self.serial_addr,9,76,0,value))
    #
    # host_address = property(get_host_address,set_host_address)

    # SERIAL ADDRESS
    # def get_serial_address(self): return self.query((self.serial_addr,10,66,0,0))[1]
    #
    # def set_serial_address(self, value): self.query((self.serial_addr,9,66,0,value))
    #
    # serial_address = property(get_serial_address,set_serial_address)

    ############################################################################
    # Motor Axis Parameters
    ############################################################################

    def move_to_position(self, usteps, relative=True):
        absolute = 0 if not relative else 1
        return self.query((self.serial_addr, 4, absolute, 0, usteps))[1]

    # ERROR FLAGS
    def get_error_flag(self):
        return self.query((self.serial_addr, 6, 207, 0, 0))[1]

    def set_error_flag(self, value): pass

    error_flag = property(get_error_flag, set_error_flag)

    # STOP ON STALL
    def get_stop_on_stall(self):
        return self.query((self.serial_addr, 6, 181, 0, 0))[1]

    def set_stop_on_stall(self, value):
        self.query((self.serial_addr, 5, 181, 0, value))

    stop_on_stall = property(get_stop_on_stall, set_stop_on_stall)

    # STALL GUARD
    def get_stall_guard(self):
        return self.query((self.serial_addr, 6, 174, 0, 0))[1]

    def set_stall_guard(self, value):
        self.query((self.serial_addr, 5, 174, 0, value))

    stall_guard = property(get_stall_guard, set_stall_guard)

    # MAX ENCODER DEVIATION
    def get_max_encoder_deviation(self):
        return self.query((self.serial_addr, 6, 212, 0, 0))[1]

    def set_max_encoder_deviation(self, value):
        self.query((self.serial_addr, 5, 212, 0, value))

    max_encoder_deviation = property(get_max_encoder_deviation,
                                     set_max_encoder_deviation)

    #ENCODER POSITION
    def get_encoder_position(self): return self.query((self.serial_addr,6,209,0,0))[1]

    def set_encoder_position(self, value): self.query((self.serial_addr,5,209,0,value))

    encoder_position = property(get_encoder_position,set_encoder_position)

    #ENCODER PRESCALER
    def get_encoder_prescaler(self): return self.query((self.serial_addr,6,210,0,0))[1]

    def set_encoder_prescaler(self, value): self.query((self.serial_addr,5,210,0,value))

    encoder_prescaler = property(get_encoder_prescaler,set_encoder_prescaler)

    #ENCODER POSITION
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

    #STADNBY CURRENT
    def get_standby_current(self): return self.query((self.serial_addr,6,7,0,0))[1]

    def set_standby_current(self, value): self.query((self.serial_addr,5,7,0,value))

    standby_current = property(get_standby_current, set_standby_current)

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
