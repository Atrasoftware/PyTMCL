

from trinamic_motor import *
from motors_specs import *
from xy_steward import *
from arc import *
import numpy as np

m1 = TrinamicMotor.from_new_interface("/dev/ttyO4",motors_specs['TMCM-1161'])
a = motors_specs['TMCM-1161']
a['serial_addr'] = 2
m2 = TrinamicMotor(m1.interface,a)


xy = XYSteward(m2,m1,12)

C = (0,0)
theta = np.pi / 4
