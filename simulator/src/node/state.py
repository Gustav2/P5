from enum import Enum

class State(Enum):
    Idle = 0
    Receive = 1
    Transmit = 2
    Decode = 3

class Package(Enum):
    DISC = 0
    SYNC = 1
    ACK = 2