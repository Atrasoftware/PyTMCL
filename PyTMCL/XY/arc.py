from __future__ import division
import math as np

class Arc(object):
    """
    Define a 2D arc object and offer some tools in order to parametrize it.
    """
    def __init__(self, C, P, theta):
        """
        Parameters
        ----------
        C : 2D tuple
            Center coordinate.
        P : 2D tuple
            Starting point coordinate
        theta: float
            Angle in radians of the arc
        """
        self.C = np.array(C)
        self.P = np.array(P)
        self.theta = theta
        self.ray = self.P-self.C
        self.r = np.linalg.norm(self.P-self.C)
        self.arc_length = self.r * theta
        self.angle = np.arctan2(self.ray[1],self.ray[0]) #first y then x

    def speed(self, t, w=None):
        """
        Parameters
        ----------
        t : float
            Time parameter [0,1]
        w : float
            Pulse

        Returns
        -------
        tuple
            Returns a tuple with (vx,vy)
        """
        omega = self.theta
        if(w != None):
            omega = w

        return ( - self.r * np.sin(t * omega + self.angle) * omega , self.r * np.cos(t * omega + self.angle) * omega )

    def position(self, t, w=None):
        """
        Parameters
        ----------
        t : float
            Time parameter [0,1]
        w : float
            Pulse

        Returns
        -------
        tuple
            Returns a tuple with (x,y) the "rendered position"
        """
        omega = self.theta
        if(w != None):
            omega = w

        return ( self.r * np.cos(t * omega + self.angle) + self.C[0] , self.r * np.sin(t * omega + self.angle) + self.C[1] )
