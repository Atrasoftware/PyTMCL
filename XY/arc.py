from __future__ import division
import numpy as np

class Arc(object):
    def __init__(self, C, P, theta):
        self.C = np.array(C)
        self.P = np.array(P)
        self.theta = theta
        self.ray = self.P-self.C
        self.r = np.linalg.norm(self.P-self.C)
        self.arc_length = self.r * theta
        self.angle = np.arctan2(self.ray[1],self.ray[0]) #first y then x

    def speed(self, t, w=None):
        """
        t goes from 0 to 1
        w is radiant / second
        """
        omega = self.theta
        if(w != None):
            omega = w

        return ( - self.r * np.sin(t * omega + self.angle) * omega , self.r * np.cos(t * omega + self.angle) * omega )

    def position(self, t, w=None):
        omega = self.theta
        if(w != None):
            omega = w

        return ( self.r * np.cos(t * omega + self.angle) + self.C[0] , self.r * np.sin(t * omega + self.angle) + self.C[1] )
