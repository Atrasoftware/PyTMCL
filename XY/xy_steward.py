from __future__ import division
import sys
sys.path.insert(0,'../')

import threading
import time
from TMCL import *
import trinamic_motor
import math
from utils import *
from arc import *

class XYSteward(object):
    def __init__(self, motor1, motor2, pitch):
        self.mx = motor1
        self.my = motor2

        #thread stuff
        lock = threading.Lock()
        self.mx.lock = lock
        self.my.lock = lock
        self.barrier = Barrier(2)

        #rotations per mm. One rotation = pitch displacement, rpmm=1/pitch
        self.rpmm = 1/pitch
        self.moving = False

    def homing(self, blocking=True):
        """
        Search for the home position in x and y and store the two variables in member variables
        """
        threads=[self.mx.home(),self.my.home()]
        #In order to block until home has finished
        if(blocking):
            for t in threads:
                t.join()

    def stop(self):
        """
        send stop to all the motors
        """
        self.mx.stop()
        self.my.stop()

    def speed_arc(self, C, theta, w):
        """
        Generate an from the actual position given
        the center coordinate as a tuple (x,y) and a theta
        """
        P = (self.x, self.y)
        arc = Arc(C, P, theta)

        vx = [0]
        vy = [0]
        stop = [False]

        self._follow_speed(self.mx, vx, stop)
        self._follow_speed(self.my, vy, stop)

        t=0
        mt = time.time()
        while(t <= theta/w):
            nv = arc.speed(t,w)
            vx[0] = self.mx.ustepps2speed(self.lin2usteps(self.mx,self.rpmm,nv[0]))
            vy[0] = self.my.ustepps2speed(self.lin2usteps(self.my,self.rpmm,nv[1]))
            time.sleep(0.005)
            t = time.time() - mt


        stop[0] = True

    def pos_arc(self, C, theta, w):
        """
        Generate an from the actual position given
        the center coordinate as a tuple (x,y) and a theta
        """
        P = (self.x, self.y)
        arc = Arc(C, P, theta)

        posx = [P[0]]
        posy = [P[1]]
        stop = [False]

        self._follow_position(self.mx, posx, stop)
        self._follow_position(self.my, posy, stop)
        time.sleep(0.1)

        t=0
        mt = time.time()
        while(t <= theta/w):
            nv = arc.position(t,w)
            posx[0] = self.lin2usteps(self.mx,self.rpmm,nv[0])
            posy[0] = self.lin2usteps(self.my,self.rpmm,nv[1])
            time.sleep(0.001)
            t = time.time() - mt

        stop[0] = True

    def lin2usteps(self, motor, rpmm, mm):
        """
        Return the amount of steps needed to achieve a linear movement in mm
        spr = steps per rotation
        rpmm = rotations per mm
        """
        return int(rpmm * mm * motor.spr * (0x01 << motor.microstep_resolution))

    def usteps2lin(self, motor, rpmm, usteps):
        """
        Return the mm for the number of steps. Inversion of lin2rot
        """
        return  usteps / (rpmm * motor.spr * (0x01 << motor.microstep_resolution))

    def mline(self, n, x , y, speed):

        for i in range(0,n):
            self.line(x+i*x,y+i*y,speed)
            while(not self.moving):
                time.sleep(0.001)

            while(self.mx.actual_position != self.mx.next_position or self.my.actual_position != self.my.next_position):
                time.sleep(0.001)

            self.moving = False

    def reset_motors(self):
        """
        Push on the trinamic motor the default setup from the config file
        """
        self.mx.reset_motor_params()
        self.my.reset_motor_params()

    def line(self, x, y, speed):
        """
        Move the plate to the cordinate x, y with speed=speed.
        [x] = mm
        [y] = mm
        [speed] = mm/s
        """

        #evaluate x speed and y speed
        disp = math.sqrt(x*x - 2*x*self.x + self.x*self.x + y*y - 2*y*self.y + self.y*self.y)
        if(disp == 0):
            return
        xratio = (x - self.x) / disp
        yratio = (y - self.y) / disp
        speedx = speed * xratio
        speedy = speed * yratio

        #Set max speed and max acc for each motor
        self.mx.reset_motor_params()
        self.my.reset_motor_params()
        #Max acc
        if(abs(speedx) > abs(speedy)):
            max_acc = self.mx.max_acceleration
            self.my.max_acceleration = max_acc * yratio / xratio
        elif(abs(speedx) < abs(speedy)):
            max_acc = self.my.max_acceleration
            self.mx.max_acceleration = max_acc * xratio / yratio
        else:
            self.mx.max_acceleration = self.my.max_acceleration

        #Max speed
        self.mx.max_positioning_speed = abs(self.mx.ustepps2speed(self.lin2usteps(self.mx,self.rpmm,speedx)))
        self.my.max_positioning_speed = abs(self.my.ustepps2speed(self.lin2usteps(self.my,self.rpmm,speedy)))

        print("SPEED: " + str(self.lin2usteps(self.mx,self.rpmm,speedx)) + " " + str(self.lin2usteps(self.my,self.rpmm,speedy)))
        print("ACC: " + str(self.mx.max_acceleration) + " " + str(self.my.max_acceleration))
        print("SPEED: " + str(self.mx.max_positioning_speed) + " " + str(self.my.max_positioning_speed) )

        self._mmove(self.mx, x)
        self._mmove(self.my, y)

    @threaded
    def _follow_position(self, motor, pos, stop):
        motor.reset_motor_params()
        #Set speed mode, maximum acceleration,
        motor.ramp_mode = 0
        motor.max_acceleration = self.mx.params['max_acceleration']
        motor.max_positioning_speed = 0
        motor.next_position = motor.actual_position
        motor.max_positioning_speed = motor.params['max_positioning_speed']

        self.barrier.wait()
        while(not stop[0]):
            motor.next_position = pos[0]

    def set_speed(self, axes, v):
        #Disable step dir
        motor = None
        if(axes == 1):
            motor = self.my
        elif(axes == 0):
            motor = self.mx

        v = v * motor.params['max_positioning_speed']
        motor.next_speed = v

    @threaded
    def _follow_speed(self, motor, v, stop=False):
        motor.reset_motor_params()
        #Set speed mode, maximum acceleration,
        motor.ramp_mode = 2
        motor.max_acceleration = self.mx.params['max_acceleration']

        self.barrier.wait()
        while(not stop[0]):
            motor.next_speed = v[0]

        motor.next_speed = 0

        motor.ramp_mode = 0
        motor.max_positioning_speed = 0
        motor.next_position = motor.actual_position
        motor.max_positioning_speed = motor.params['max_positioning_speed']

    @threaded
    def _mmove(self, motor, pos):
        """
        Receive the motor, speed in mm/s and pos in mm
        """
        #Set ramp mode to position mode (trapezoidal speed ramps are provided)
        motor.ramp_mode = 0

        #Convert pos in the number of steps
        usteps = self.lin2usteps(motor,self.rpmm,pos)

        #Set target speed
        self.barrier.wait()
        motor.next_position = usteps

        self.moving = True

    ############################################################################
    # Steward parameters
    ############################################################################
    #X
    def get_x(self):
        return self.usteps2lin(self.mx,self.rpmm,self.mx.actual_position)

    def set_x(self, value):
        pass

    x = property(get_x,set_x)

    #Y
    def get_y(self):
        return self.usteps2lin(self.my,self.rpmm,self.my.actual_position)

    def set_y(self, value):
        pass

    y = property(get_y,set_y)
