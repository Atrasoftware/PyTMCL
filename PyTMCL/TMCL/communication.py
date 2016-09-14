
import serial

from  . import codec
from .consts import *
from .error import *


class TMCLCommunicator(object):
    """Abstraction of a Communication handler that speak TMCL via serial port to a TMCM"""

    def __init__(self, port, baudrate=115200, debug=False):
        self._port = port
        self._debug = debug
        self._ser = serial.Serial(port)
        self._ser.baudrate = baudrate

    def query(self, request):
        """Encode and send a query. Receive, decode, and return reply"""
        #Insert inside encode request command function a way to check the value ranges
        req = codec.encodeRequestCommand(*request)
        req = list(map(ord,req))
        if self._debug:
            print(("send to TMCL: ", codec.hexString(req), codec.decodeRequestCommand(req)))
        self._ser.write(req)
        resp = codec.decodeReplyCommand(self._ser.read(9))
        if self._debug:
            tmp = list(resp.values())[:-1]
            tmp = codec.encodeReplyCommand(*tmp)
            print(("got from TMCL:", codec.hexString(tmp), resp))
        return resp['status'], resp['value']
