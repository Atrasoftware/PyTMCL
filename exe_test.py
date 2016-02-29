import threading
import time
from TMCL import *
import math as np

lock = threading.Lock()


#Init motor
motor = communication.TMCLCommunicator("/dev/ttyO4",1,4,(2),5000000,21,2**23,debug=False)

#addrx=2
addry=1

#MOTORS CONFIGURATION
max_current = 255
step_resolution= 4
max_acc = 2047

##Setup axis parameters
#Set current
#motor._query((addrx,5,6,0,max_current))
motor._query((addry,5,6,0,max_current))

#Set step resolution
#motor._query((addrx,5,140,0,step_resolution))
motor._query((addry,5,140,0,step_resolution))

#Max acceleration (2047 max)
#motor._query((addrx,5,5,0,max_acc)) #Set max acc
motor._query((addry,5,5,0,max_acc)) #Set max acc

#Stallguard stop (value = max speed in order to stop)
#motor._query((addrx,5,181,0,100))
motor._query((addry,5,181,0,2047))


def set_ap(acc, vel, step_res):
    motor._query((addry,5,4,0,vel))
    motor._query((addry,5,5,0,acc))
    motor._query((addry,5,140,0,step_res))

def home():
    motor._query((addry,5,138,0,2))
    motor._query((addry,5,6,0,90))
    set_ap(4,500,4)
    motor._query((addry,5,2,0,-300))
    time.sleep(0.1)
    while(True):
        homer=motor._query((addry,6,206,0,0))[1]
        if(homer > 500):
            print(homer)
        else:
            break

    motor._query((addry,5,6,0,253))
    set_ap(50,500,4)
    motor.mst(0)
    init_pos = motor._query((addry,6,1,0,0))[1]
    motor._query((addry,5,6,0,max_current))
    motor._query((addry,5,140,0,step_resolution))

def go(speed):
    max_speed_reached=0
    max_accel_reached=0
    motor._query((addry,5,138,0,2))
    motor._query((addry,5,2,0,speed))
    speed = motor._query((addry,6,3,0,0))[1]
    #motor._query((addry,5,2,0,end_pos))
    #time.sleep(0.1)
    while(motor._query((addry,6,206,0,0))[1] > 0):
        speed = motor._query((addry,6,3,0,0))[1]
        if( speed > max_speed_reached):
            max_speed_reached = speed
        _ = motor._query((addry,6,135,0,0))[1]
        if( _ > max_accel_reached):
            max_accel_reached = _

    motor.mst(0)
    print("MAX SPEED: " + str(max_speed_reached) + " MAX ACCEL: " + str(max_accel_reached))


#Set speed mode




#motor._query((addry,5,0,0,init_pos))
