from __future__ import division
import sys
sys.path.insert(0,'../')

from TMCL import *


HOSTADDR = 0
MOTORADDR = 4
BAUDRATE = 7
MOTOR_DEV = "/dev/ttyACM0"


interface = communication.TMCLCommunicator(MOTOR_DEV, 115200, False)


#HOST ADDRESS
def get_host_address(interface): return interface.query((MOTORADDR,10,76,0,0))[1]

def set_host_address(interface, value): interface.query((MOTORADDR,9,76,0,value))

#SERIAL ADDRESS
def get_serial_address(interface): return interface.query((MOTORADDR,10,66,0,0))[1]

def set_serial_address(interface, value): interface.query((MOTORADDR,9,66,0,value))

#BAUD RATE
def get_baudrate_address(interface): return interface.query((MOTORADDR,10,65,0,0))[1]

def set_baudrate_address(interface, value): interface.query((MOTORADDR,9,65,0,value))

set_serial_address(interface, MOTORADDR)
print("Checking if serial addr correctly set... ", str(get_serial_address(interface) == MOTORADDR), " ", MOTORADDR)

set_host_address(interface, HOSTADDR)
print("Checking if host addr correctly set... ", str(get_host_address(interface) == HOSTADDR), " ", HOSTADDR)

set_baudrate_address(interface, BAUDRATE)
print("Checking if baudrate correctly set... ", str(get_baudrate_address(interface) == BAUDRATE), " ", BAUDRATE)
