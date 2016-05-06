

from trinamic_motor import *
from motors_specs import *
from xy_steward import *
from ps3_joypad import *

a = motors_specs['TMCM-1161']
a['serial_addr'] = 1
a['direction'] = -1

m1 = TrinamicMotor.from_new_interface("/dev/ttyO4",a)

a = motors_specs['TMCM-1161']
a['serial_addr'] = 2
a['direction'] = 1
m2 = TrinamicMotor(m1.interface,a)


print("M1 M2 inintialized")
#Components
a = motors_specs['TMCM-1161']
a['serial_addr'] = 3
m3 = TrinamicMotor(m1.interface,a)
a['serial_addr'] = 4
m4 = TrinamicMotor(m1.interface,a)

print("M3 M4 inintialized")
print("Motors correctly initialized")

xy = XYSteward(m1,m2,12)

print("Steward instanced")

js = PS3XYController("/dev/input/js0")

print("Joypad inintialized")
js.start(xy)

print("Controller connected, device ready.")
