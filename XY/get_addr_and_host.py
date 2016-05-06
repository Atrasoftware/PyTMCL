from __future__ import division
import sys
sys.path.insert(0,'../')

from TMCL import *


HOSTADDR = 2
MOTORADDR = 0

MOTOR_DEV = "/dev/ttyACM0"


interface = communication.TMCLCommunicator(MOTOR_DEV, 115200, False)


#HOST ADDRESS
def get_host_address(interface): return interface.query((MOTORADDR,10,76,0,0))[1]

#SERIAL ADDRESS
def get_serial_address(interface): return interface.query((MOTORADDR,10,66,0,0))[1]

print("Motor serial address ", get_serial_address(interface))
print("Motor host serial address ", get_host_address(interface))
