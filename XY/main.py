

from trinamic_motor import *
from motors_specs import *
from xy_steward import *
from ps3_joypad import *

m1 = TrinamicMotor.from_new_interface("/dev/ttyO4",motors_specs['TMCM-1161'])

a = motors_specs['TMCM-1161']
a['serial_addr'] = 2
m2 = TrinamicMotor(m1.interface,a)

print("Motors correctly initialized")

xy = XYSteward(m2,m1,12)

print("Steward instanced")

js = PS3XYController("/dev/input/js0")

js.start(xy)

print("Controller connected, device ready.")
