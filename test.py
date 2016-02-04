


from TMCL import *


motor = communication.TMCLCommunicator("/dev/ttyUSB0",1,4,(2),5000000,21,2**23,debug=True)


motor.ror(0,10000)
