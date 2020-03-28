#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

"""
Define a packet format (incoming and outgoing) between a client and a server

The representation for our protocol is text-based (UTF-8 encoded)
MSG_TYPE|ARG1|ARG2|ARG3|...\n

"""

MESSAGE_LEN_MAX = 256
MESSAGE_SEP = b'\n'


class Packet:

    def __init__ (self, msg_type, *args):
        self.msg_type = msg_type
        self.args     = list(args)


    def __str__(self):
        res =  str(self.msg_type) + '|'
        for arg in self.args:
            res += arg + '|'
        return res[:-1] + '\n'


    def __eq__(self, other):
        if not isinstance(other, Packet):
            return NotImplemented
        return self.__str__() == other.__str__()


    def to_bytes(self):
        return self.__str__().encode('utf-8', 'strict')


def from_bytes(buf):
    l = buf[:MESSAGE_LEN_MAX].decode('utf-8', 'strict').split('\n')[0].split('|')

    if len(l) == 0:
        raise ValueError('packet.py: Invalid format')

    try:
        msg_type = str(l[0])
    except:
        raise ValueError('packet.py: Invalid format ==> msg_type ' + l[0])

    args = l[1:]
    return Packet(msg_type, *args)
