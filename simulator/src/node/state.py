from enum import Enum

class State(Enum):
    Idle = 0
    Receive = 1
    Transmit = 2

class Package(Enum):
    DISC = 0
    DISC_ACK = 1
    SYNC = 2
    ACK = 3