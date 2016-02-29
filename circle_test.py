import threading
import time
from TMCL import *
import math as np

lock = threading.Lock()


#Init motor
motor = communication.TMCLCommunicator("/dev/ttyO4",1,4,(2),5000000,21,2**23,debug=False)

addrx=2
addry=1

#MOTORS CONFIGURATION
max_current = 255
step_resolution= 4
max_acc = 2047

##Setup axis parameters
#Set current
motor._query((addrx,5,6,0,max_current))
motor._query((addry,5,6,0,max_current))

#Set step resolution
motor._query((addrx,5,140,0,step_resolution))
motor._query((addry,5,140,0,step_resolution))

#Max acceleration (2047 max)
motor._query((addrx,5,5,0,max_acc)) #Set max acc
motor._query((addry,5,5,0,max_acc)) #Set max acc

#Stallguard stop (value = max speed in order to stop)
#motor._query((addrx,5,181,0,100))
#motor._query((addry,5,181,0,100))

border_speed = 700

#Init variables
counter=[0,0]
vx = [0]
vy = [0]
t = 0
stop=False


# Send to the motor the vx or vy
def worker(i):
    perf=0
    print("WORKER " + str(i) + " started")
    addr = None
    vaxis = [0]
    if( i == 0 ):
        addr = addry
        vaxis = vy
    if( i == 1 ):
        addr = addrx
        vaxis = vx

    #actual_speed = motor._query((addr,6,3,0,0))[1]
    while True:
        with lock:
            #perf = time.time()
            motor._query((addr, 5, 2, 0, vaxis[0]))
            #counter[0] = time.time() - perf
            #print(str(addr) + " " + str(vaxis[0]))
        # while(actual_speed != vaxis):
        #     actual_speed = motor._query((addr,6,3,0,0))[1]

mt = time.time()
for i in range(2):
    thr = threading.Thread(target=worker, args=(i,))
    thr.daemon = True
    thr.start()

print("STARTED THREADS")
time.sleep(1)
vx[0] = border_speed
time.sleep(0.5)

while( True ):
    time.sleep(0.001)
    t = time.time() - mt
    vx[0] = int(border_speed * np.cos(t*10))
    vy[0] = int(border_speed * np.sin(t*10))


print(counter)
stop = True
